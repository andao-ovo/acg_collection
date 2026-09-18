from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import bcrypt
from sqlalchemy.orm import Session

from database import get_db
from models import User

SECRET_KEY = "my-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# auto_error=False：缺少 Authorization 头时不由 FastAPI 直接抛 403，
# 改由下面的 get_current_user 统一返回 401（前端只在 401 时才清 token 并跳登录）
security = HTTPBearer(auto_error=False)

# bcrypt 只处理前 72 字节，超出部分会被忽略。
# 为保证前后一致，hash 与 verify 都用同样的方式截断到 72 字节。
def _truncate(password: str) -> bytes:
    return password.encode("utf-8")[:72]

def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(_truncate(password), bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(_truncate(plain_password), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False

def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> int:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return int(payload["sub"])

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或缺少 token"
        )

    token = credentials.credentials
    try:
        user_id = verify_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    return user

# 可选登录：给"公开接口，但登录后能多看到一点信息"的场景用（如作品列表附带收藏状态）。
# 与 get_current_user 的唯一区别是：没带 token 或 token 无效时返回 None，而不是抛 401。
# 注意：token 无效时也返回 None 是有意的 —— 对公开接口来说，"没登录"和"登录过期了"
# 都按匿名处理即可，前端在需要登录的操作上自然会拿到 401。
def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if credentials is None:
        return None

    try:
        user_id = verify_token(credentials.credentials)
    except JWTError:
        return None

    return db.query(User).filter(User.id == user_id).first()