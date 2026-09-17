from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 用绝对路径，避免从别的目录启动时在那边新建一个空的 acg.db
BASE_DIR = Path(__file__).resolve().parent
SQLALCHEMY_DATABASE_URL = "sqlite:///" + (BASE_DIR / "acg.db").as_posix()

#创建数据库引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)


SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

#创建基类
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()