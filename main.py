from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func
from pydantic import BaseModel

from database import engine, Base, get_db
from models import Work, Tag, WorkTag, User
from schemas import WorkCreate, WorkOut
from auth import hash_password, verify_password, create_token, get_current_user

import redis, json

r = redis.Redis(host="localhost", port=6379, db=0, protocol=2)

#app 定义在最前面（所有接口之前）
app = FastAPI(title="ACG收藏馆", description="动漫/小说/漫画收藏与评价系统")

Base.metadata.create_all(bind=engine)

# 注册请求模型
class UserCreate(BaseModel):
    username: str
    password: str

# ---------- 注册接口（不需要认证）----------
@app.post("/register")
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
@app.post("/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    
    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    
    token = create_token(db_user.id)
    return {"access_token": token, "token_type": "bearer"}

# 创建标签（需要认证）
@app.post("/tags")
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
@app.post("/works", response_model=WorkOut)
def create_work(
    work: WorkCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)   
):
    try:
        db_work = Work(**work.dict(exclude={"tag_ids"}))
        db.add(db_work)
        db.flush()
        for tag_id in work.tag_ids:
            db.add(WorkTag(tag_id=tag_id, work_id=db_work.id))
        db.commit()
        db.refresh(db_work)
        r.delete("works_stats")
        return db_work
    except Exception:
        db.rollback()
        raise

# ---------- 查询作品列表（不需要认证）----------
@app.get("/works", response_model=List[WorkOut])
def get_work(
    type: Optional[str] = None,
    status: Optional[str] = None,
    title: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    sort_by: str = "id",
    order: str = "desc",
    db: Session = Depends(get_db)
):
    work_query = db.query(Work)
    
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

    return work_query.all()

# ---------- 查询单个作品（不需要认证）----------
@app.get("/works/{work_id}", response_model=WorkOut)
def get_work_by_id(work_id: int, db: Session = Depends(get_db)):
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    return work

# ---------- 显示单个作品的标签（不需要认证）----------
@app.get("/works/{work_id}/tags")
def get_work_tags_by_id(work_id: int, db: Session = Depends(get_db)):
    cached = r.get(f"work:{work_id}:tags")
    if cached:
        return json.loads(cached)
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")

    tags = db.query(Tag.name).join(WorkTag, WorkTag.tag_id == Tag.id).filter(WorkTag.work_id == work_id).all()
    tag_names = [t[0] for t in tags]
    r.setex(f"work:{work_id}:tags", 300, json.dumps(tag_names))
    return tag_names

# ---------- 添加标签（需要认证）----------
@app.post("/works/{work_id}/tags")
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

    work_tag = WorkTag(work_id=work_id, tag_id=tag_id)
    db.add(work_tag)
    db.commit()
    r.delete(f"work:{work_id}:tags")
    return {"message": "标签添加成功"}

# ---------- 删除标签（需要认证）----------
@app.delete("/works/{work_id}/tags/{tag_id}")
def delete_tag(
    work_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)   
):
    db_work_tag = db.query(WorkTag).filter(WorkTag.work_id == work_id).filter(WorkTag.tag_id == tag_id).first()
    db.delete(db_work_tag)
    db.commit()
    r.delete(f"work:{work_id}:tags")
    return {"message": "标签删除成功"}

# ---------- 根据标签查找作品（不需要认证）----------
@app.get("/works/tags/by-tags")
def get_works_by_tags(
    tag_ids: str = Query(..., description="逗号分隔的标签ID，如 1,3,5"),
    db: Session = Depends(get_db)
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
    return works

# ---------- 更新作品（需要认证）----------
@app.put("/works/{work_id}", response_model=WorkOut)
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
    r.delete("works_stats")
    return db_work

# ---------- 删除作品（需要认证）----------
@app.delete("/works/{work_id}")
def delete_work(
    work_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)   # ✅ 拼写修正
):
    db_work = db.query(Work).filter(Work.id == work_id).first()
    if not db_work:
        raise HTTPException(status_code=404, detail="Work not found")
    
    db.delete(db_work)
    db.commit()
    r.delete("works_stats")
    return {"ok": True}

# ---------- 随机推荐（不需要认证）----------
@app.get("/works/random", response_model=WorkOut)
def random_work(db: Session = Depends(get_db)):
    work = db.query(Work).order_by(func.random()).first()
    if not work:
        raise HTTPException(status_code=404, detail="No works found")
    return work

# ---------- 统计（不需要认证）----------
@app.get("/works/stats")
def get_stats(db: Session = Depends(get_db)):
    cached = r.get("works_stats")
    if cached:
        return json.loads(cached)
    total = db.query(func.count(Work.id)).scalar()
    avg_rating = db.query(func.avg(Work.rating)).scalar()
    type_counts = db.query(Work.type, func.count(Work.id)).group_by(Work.type).all()
    result = {
        "total": total,
        "avg_rating": avg_rating,
        "type_breakdown": dict(type_counts)
    }
    r.setex("works_stats", 300, json.dumps(result))
    return result