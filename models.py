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