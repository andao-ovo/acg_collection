from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from database import Base
from datetime import datetime

class Work(Base):
    __tablename__ = "works"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    type = Column(String)
    author = Column(String)
    status = Column(String)
    rating = Column(Float)
    comment = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    # 上传者。作品本身是公开的（所有人可见），这个字段只用于标记归属，
    # 为以后做「只有作者能改/删」的权限控制留好位置。
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False)

class WorkTag(Base):
    __tablename__ = "work_tags"
    __table_args__ = (UniqueConstraint("work_id", "tag_id", name="uq_work_tag"),)
    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(Integer, ForeignKey("works.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key = True, index = True)
    username = Column(String, unique = True, index = True)
    password = Column(String)
    created_at = Column(DateTime, default = datetime.now)

# 用户收藏表：用户与作品的多对多关联。
# 单独建表而不是在 works 上加个"是否收藏"字段，是因为一个作品会被多个用户收藏，
# 收藏关系属于"用户×作品"这一对组合，只能放在关联表里。
class UserFavorite(Base):
    __tablename__ = "user_favorites"
    __table_args__ = (UniqueConstraint("user_id", "work_id", name="uq_user_favorite"),)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    work_id = Column(Integer, ForeignKey("works.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)