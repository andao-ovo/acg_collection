from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

#请求模型
class WorkCreate(BaseModel):
    title: str
    type: str                      #包括小说，漫画，动漫
    author: Optional[str] = None   #可有可无，不传入就是None
    status: str                   
    rating: Optional[float] = None
    comment: Optional[str] = None
    tag_ids: List[int] = []

#响应模型
class WorkOut(WorkCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True  #允许从SQLAlchemy模型自动转换