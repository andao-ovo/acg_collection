from pathlib import Path

from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func, select
from pydantic import BaseModel

from database import engine, Base, get_db
from models import Work, Tag, WorkTag, User, UserFavorite
from schemas import WorkCreate, WorkOut
from auth import hash_password, verify_password, create_token, get_current_user, get_optional_user

import time

import redis, json
from redis.backoff import NoBackoff
from redis.retry import Retry

# ---------- Redis 缓存（可选依赖：连不上就自动降级为直连数据库）----------
# 这里的三个参数缺一不可，否则 Redis 未运行时接口会卡到不可用：
#   1. socket_connect_timeout / socket_timeout —— 不设的话会一直阻塞到 TCP 超时
#   2. retry=Retry(NoBackoff(), 0) —— 关键。redis-py 8.x 默认 retries=10 且带指数退避，
#      不关掉的话每次调用要先重试 10 遍，实测单个请求要等 19 秒
#   3. host 用 127.0.0.1 而不是 localhost —— 避免 IPv6(::1) 和 IPv4 各连一次
r = redis.Redis(
    host="127.0.0.1", port=6379, db=0, protocol=2,
    socket_connect_timeout=0.5, socket_timeout=0.5,
    retry=Retry(NoBackoff(), 0),
)


# 熔断：确认 Redis 不可用后，一段时间内直接跳过缓存，
# 免得每个请求都要重新付一次连接超时的代价。
_CACHE_DOWN = False
_CACHE_RETRY_AFTER = 30.0
_CACHE_PROBE_AT = 0.0


def _cache_enabled() -> bool:
    """Redis 被判定为不可用时返回 False；过了冷却期则放行一次探测。"""
    global _CACHE_DOWN
    if not _CACHE_DOWN:
        return True
    if time.monotonic() >= _CACHE_PROBE_AT:
        _CACHE_DOWN = False
        return True
    return False


def _mark_cache_down(exc) -> None:
    global _CACHE_DOWN, _CACHE_PROBE_AT
    if not _CACHE_DOWN:
        print("[缓存] Redis 连接失败，后续 %d 秒内跳过缓存：%s"
              % (_CACHE_RETRY_AFTER, exc), flush=True)
    _CACHE_DOWN = True
    _CACHE_PROBE_AT = time.monotonic() + _CACHE_RETRY_AFTER


def cache_get(key):
    """读缓存。Redis 不可用时返回 None，等同于缓存未命中，调用方会回落到查数据库。"""
    if not _cache_enabled():
        return None
    try:
        value = r.get(key)
        return json.loads(value) if value is not None else None
    except redis.RedisError as exc:
        _mark_cache_down(exc)
        return None


def cache_set(key, value, ttl=300):
    """回填缓存。失败静默忽略 —— 缓存写失败不该影响已经查出来的结果。"""
    if not _cache_enabled():
        return
    try:
        r.setex(key, ttl, json.dumps(value, ensure_ascii=False))
    except redis.RedisError as exc:
        _mark_cache_down(exc)


def cache_delete(*keys):
    """主动失效缓存。失败静默忽略 —— 数据已经落库，缓存过期后自然一致。"""
    if not keys or not _cache_enabled():
        return
    try:
        r.delete(*keys)
    except redis.RedisError as exc:
        _mark_cache_down(exc)


def _probe_redis() -> bool:
    """启动时探测一次 Redis。失败就直接置为降级状态（启动日志会统一告知）。"""
    global _CACHE_DOWN, _CACHE_PROBE_AT
    try:
        r.ping()
        return True
    except redis.RedisError:
        _CACHE_DOWN = True
        _CACHE_PROBE_AT = time.monotonic() + _CACHE_RETRY_AFTER
        return False

#app 定义在最前面（所有接口之前）
app = FastAPI(title="ACG收藏馆", description="动漫/小说/漫画收藏与评价系统")

# 所有业务接口统一挂在 /api 前缀下，与前端 axios 的 baseURL('/api') 保持一致
api = APIRouter()

Base.metadata.create_all(bind=engine)

if _probe_redis():
    print("[缓存] Redis 已连接，统计与标签接口启用缓存", flush=True)
else:
    print("[缓存] 未检测到 Redis，已自动降级为直连数据库（功能不受影响，仅少了缓存）", flush=True)


# ---------- 作品可见范围（scope）----------
# 作品本身是公开的：谁上传的都能被所有人看到，暂时不做用户之间的权限隔离。
# scope 控制的是"这一屏想看哪一批"：
#   all       —— 全馆公开作品（默认，不需要登录）
#   favorites —— 我收藏的（需要登录）
#   mine      —— 我上传的（需要登录）
SCOPES = ("all", "favorites", "mine")


def _check_scope(scope: str) -> None:
    if scope not in SCOPES:
        raise HTTPException(status_code=400, detail="scope 只能是 all / favorites / mine")


def _scope_conditions(scope: str, user, db: Session):
    """把 scope 翻译成一组过滤条件。

    返回"条件列表"而不是拼好的 Query，是为了让列表接口和统计接口共用同一套口径 ——
    两边的 total 必须一致，否则前端的页码会错位。
    """
    if scope == "favorites":
        # 用 IN 子查询而不是 join：统计接口要对同一条件做 count / avg / group by，
        # 子查询在这些聚合里都能直接复用，不会和 group by 相互干扰
        return [Work.id.in_(
            select(UserFavorite.work_id).where(UserFavorite.user_id == user.id)
        )]
    if scope == "mine":
        return [Work.user_id == user.id]
    return []


def _attach_favorite_state(works, user, db: Session):
    """给作品对象挂上 is_favorited，供 WorkOut 序列化输出。

    is_favorited 不是 works 表里的字段，而是"当前用户 × 这部作品"临时算出来的，
    所以只能在这里按当前登录用户挂上去；未登录时一律 False，连库都不用查。
    """
    ids = [w.id for w in works]
    if user is None or not ids:
        for work in works:
            work.is_favorited = False
        return works

    favorite_ids = {
        row[0]
        for row in db.query(UserFavorite.work_id)
        .filter(UserFavorite.user_id == user.id, UserFavorite.work_id.in_(ids))
        .all()
    }
    for work in works:
        work.is_favorited = work.id in favorite_ids
    return works


# 注册请求模型
class UserCreate(BaseModel):
    username: str
    password: str

# ---------- 注册接口（不需要认证）----------
@api.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    new_user = User(
        username=user.username,
        password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "注册成功", "id": new_user.id}

# ---------- 登录接口（不需要认证，返回 token）----------
@api.post("/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    
    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    
    token = create_token(db_user.id)
    return {"access_token": token, "token_type": "bearer"}

# 创建标签（需要认证）
@api.post("/tags")
def create_tag(
    name: str,
    category: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    existing = db.query(Tag).filter(Tag.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="标签已存在")
    
    new_tag = Tag(name=name, category=category)
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag

# ---------- 新增作品（需要认证）----------
@api.post("/works", response_model=WorkOut)
def create_work(
    work: WorkCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)   
):
    try:
        # user_id 由服务端从 token 里取，不接受客户端传入 —— 否则可以伪造成别人上传的
        db_work = Work(**work.model_dump(exclude={"tag_ids"}), user_id=user.id)
        db.add(db_work)
        db.flush()
        for tag_id in work.tag_ids:
            db.add(WorkTag(tag_id=tag_id, work_id=db_work.id))
        db.commit()
        db.refresh(db_work)
    except Exception:
        db.rollback()
        raise

    # 缓存失效放在事务边界之外：Redis 出问题不该影响已经提交的数据
    cache_delete("works_stats")
    # 刚上传的作品不会自己出现在收藏里：上传和收藏是两个独立的动作
    db_work.is_favorited = False
    return db_work

# ---------- 查询作品列表（公开；scope=favorites/mine 时需要认证）----------
# 用 get_optional_user 而不是 get_current_user：默认的全馆浏览必须保持匿名可用，
# 只有切到"我的收藏/我上传的"时才要求登录，由 _check_scope 之后手动判 401
@api.get("/works", response_model=List[WorkOut])
def get_work(
    type: Optional[str] = None,
    status: Optional[str] = None,
    title: Optional[str] = None,
    scope: str = "all",
    skip: int = 0,
    limit: int = 10,
    sort_by: str = "id",
    order: str = "desc",
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user)
):
    _check_scope(scope)
    if scope in ("favorites", "mine") and user is None:
        raise HTTPException(status_code=401, detail="该筛选需要登录")

    work_query = db.query(Work)

    conditions = _scope_conditions(scope, user, db)
    if conditions:
        work_query = work_query.filter(*conditions)

    if type:
        work_query = work_query.filter(Work.type == type)
    if status:
        work_query = work_query.filter(Work.status == status)
    if title:
        work_query = work_query.filter(Work.title.contains(title))

    allowed_sort_fields = {"id", "rating", "created_at"}
    if sort_by not in allowed_sort_fields:
        sort_by = "id"
    sort_column = getattr(Work, sort_by)
    if order == "desc":
        sort_column = sort_column.desc()
    work_query = work_query.order_by(sort_column)
    work_query = work_query.offset(skip).limit(limit)

    works = work_query.all()
    return _attach_favorite_state(works, user, db)

# ---------- 随机推荐（不需要认证）----------
# 注意:固定路径接口必须定义在 /works/{work_id} 之前,否则会被当成 work_id 拦截
@api.get("/works/random", response_model=WorkOut)
def random_work(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user)
):
    work = db.query(Work).order_by(func.random()).first()
    if not work:
        raise HTTPException(status_code=404, detail="No works found")
    return _attach_favorite_state([work], user, db)[0]

# ---------- 统计（公开；scope=favorites/mine 时需要认证）----------
# 统计口径必须和 /works 保持一致（同样的 scope），否则前端用 total 算出来的
# 页码和实际返回的条数会对不上
@api.get("/works/stats")
def get_stats(
    scope: str = "all",
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user)
):
    _check_scope(scope)
    if scope in ("favorites", "mine") and user is None:
        raise HTTPException(status_code=401, detail="该筛选需要登录")

    # 全馆统计人人一样，缓存一份即可；favorites/mine 是"每人一份"，
    # 缓存键必须带上 user_id 才有意义 —— 沿用全局键 "works_stats" 会让 A 读到 B 的数字。
    # 这点收益不值得引入"按用户失效"的复杂度，所以个人统计直接查库。
    if scope == "all":
        cached = cache_get("works_stats")
        if cached is not None:
            return cached

    conditions = _scope_conditions(scope, user, db)
    total_query = db.query(func.count(Work.id))
    avg_query = db.query(func.avg(Work.rating))
    type_query = db.query(Work.type, func.count(Work.id))
    if conditions:
        total_query = total_query.filter(*conditions)
        avg_query = avg_query.filter(*conditions)
        type_query = type_query.filter(*conditions)

    result = {
        "total": total_query.scalar(),
        "avg_rating": avg_query.scalar(),
        "type_breakdown": dict(type_query.group_by(Work.type).all())
    }

    if scope == "all":
        cache_set("works_stats", result)
    return result

# ---------- 查询单个作品（不需要认证）----------
@api.get("/works/{work_id}", response_model=WorkOut)
def get_work_by_id(
    work_id: int,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user)
):
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    return _attach_favorite_state([work], user, db)[0]

# ---------- 收藏作品（需要认证）----------
# 做成幂等的：重复收藏直接返回成功，不报 400。
# 前端是个"收藏/取消"切换按钮，网络慢时用户容易连点两次，
# 幂等能保证连点不会弹错误提示（对比 add_tag 那种"重复即报错"的场景，
# 这里的语义是"让状态变成已收藏"，而不是"新建一条记录"）
@api.post("/works/{work_id}/favorite")
def add_favorite(
    work_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    existing = (
        db.query(UserFavorite)
        .filter(UserFavorite.user_id == user.id, UserFavorite.work_id == work_id)
        .first()
    )
    if existing:
        return {"message": "已在收藏中", "is_favorited": True}

    db.add(UserFavorite(user_id=user.id, work_id=work_id))
    db.commit()
    # 收藏不影响全馆统计（total / avg_rating / 类型分布都不含收藏数），
    # 所以这里不需要动 "works_stats" 缓存
    return {"message": "收藏成功", "is_favorited": True}

# ---------- 取消收藏（需要认证）----------
# 同样幂等：没收藏过也返回成功，前端不必先查状态再删
@api.delete("/works/{work_id}/favorite")
def remove_favorite(
    work_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    favorite = (
        db.query(UserFavorite)
        .filter(UserFavorite.user_id == user.id, UserFavorite.work_id == work_id)
        .first()
    )
    if not favorite:
        return {"message": "尚未收藏该作品", "is_favorited": False}

    db.delete(favorite)
    db.commit()
    return {"message": "已取消收藏", "is_favorited": False}

# ---------- 显示单个作品的标签（不需要认证）----------
@api.get("/works/{work_id}/tags")
def get_work_tags_by_id(work_id: int, db: Session = Depends(get_db)):
    cached = cache_get(f"work:{work_id}:tags")
    # 必须用 is not None：没有标签的作品缓存值是 []，而 [] 是 falsy，
    # 写成 `if cached` 会导致这类作品永远缓存不命中
    if cached is not None:
        return cached
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    tags = db.query(Tag.name).join(WorkTag, WorkTag.tag_id == Tag.id).filter(WorkTag.work_id == work_id).all()
    tag_names = [t[0] for t in tags]
    cache_set(f"work:{work_id}:tags", tag_names)
    return tag_names

# ---------- 添加标签（需要认证）----------
@api.post("/works/{work_id}/tags")
def add_tag(
    work_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)   
):
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # 防止重复添加同一标签（WorkTag 上已有 (work_id, tag_id) 唯一约束兜底）
    existing = (
        db.query(WorkTag)
        .filter(WorkTag.work_id == work_id, WorkTag.tag_id == tag_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="该标签已在此作品上，无需重复添加")

    db.add(WorkTag(work_id=work_id, tag_id=tag_id))
    db.commit()
    cache_delete(f"work:{work_id}:tags")
    return {"message": "标签添加成功"}

# ---------- 删除标签（需要认证）----------
@api.delete("/works/{work_id}/tags/{tag_id}")
def delete_tag(
    work_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)   
):
    db_work_tag = (
        db.query(WorkTag)
        .filter(WorkTag.work_id == work_id, WorkTag.tag_id == tag_id)
        .first()
    )
    if not db_work_tag:
        raise HTTPException(status_code=404, detail="该标签不在此作品上")

    db.delete(db_work_tag)
    db.commit()
    cache_delete(f"work:{work_id}:tags")
    return {"message": "标签删除成功"}

# ---------- 根据标签查找作品（不需要认证）----------
@api.get("/works/tags/by-tags")
def get_works_by_tags(
    tag_ids: str = Query(..., description="逗号分隔的标签ID，如 1,3,5"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user)
):
    tag_id_list = [int(x.strip()) for x in tag_ids.split(",")]
    work_ids = (
        db.query(WorkTag.work_id)
        .filter(WorkTag.tag_id.in_(tag_id_list))
        .group_by(WorkTag.work_id)
        .having(func.count(WorkTag.tag_id) == len(tag_id_list))
        .all()
    )
    work_id_list = [item[0] for item in work_ids]
    if not work_id_list:
        return []
    works = db.query(Work).filter(Work.id.in_(work_id_list)).all()
    return _attach_favorite_state(works, user, db)

# ---------- 更新作品（需要认证）----------
@api.put("/works/{work_id}", response_model=WorkOut)
def update_work(
    work_id: int,
    work_update: WorkCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)   
):
    db_work = db.query(Work).filter(Work.id == work_id).first()
    if not db_work:
        raise HTTPException(status_code=404, detail="Work not found")
    
    db_work.title = work_update.title
    db_work.type = work_update.type
    db_work.author = work_update.author
    db_work.status = work_update.status
    db_work.rating = work_update.rating
    db_work.comment = work_update.comment

    db.commit()
    db.refresh(db_work)
    cache_delete("works_stats")
    return db_work

# ---------- 删除作品（需要认证）----------
@api.delete("/works/{work_id}")
def delete_work(
    work_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)   # ✅ 拼写修正
):
    db_work = db.query(Work).filter(Work.id == work_id).first()
    if not db_work:
        raise HTTPException(status_code=404, detail="Work not found")

    # 先把收藏关联删掉：SQLite 默认不强制外键约束（不打开 PRAGMA foreign_keys），
    # 光删作品会留下指向"已经不存在的作品"的收藏记录。
    # 放在同一个事务里提交，避免出现"作品删了但收藏没删干净"的中间状态
    db.query(UserFavorite).filter(UserFavorite.work_id == work_id).delete()

    db.delete(db_work)
    db.commit()
    cache_delete("works_stats")
    return {"ok": True}


# ---------- 挂载业务路由与前端静态文件 ----------
# 注意：include_router 必须放在所有 @api 路由定义之后
app.include_router(api, prefix="/api")

# 前端构建产物（frontend/dist）。只有 dist 存在时才挂载，
# 开发态没构建过前端也不影响后端启动。
DIST_DIR = Path(__file__).resolve().parent / "frontend" / "dist"

if DIST_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    # SPA fallback：前端用的是 history 路由模式，
    # 直接访问或刷新 /stats、/work/1 这类前端路由时，需要返回 index.html 交给前端接管，
    # 否则会 404。StaticFiles(html=True) 做不到这一点，它只对目录请求生效。
    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        # /api 下未匹配到的路径不能被吞成 HTML，否则前端会把 HTML 当 JSON 解析。
        # 注意：路由没匹配上会继续尝试下一个路由，所以光靠注册顺序挡不住，
        # 必须在这里显式拦截。
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="接口不存在")
        return FileResponse(DIST_DIR / "index.html")

