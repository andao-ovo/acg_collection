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
    user_id: Optional[int] = None   #上传者ID，老数据可能为空
    #当前登录用户是否收藏了这部作品。未登录时恒为 False。
    #它不属于 works 表，是查询时按"用户×作品"临时算出来的，由接口挂到对象上。
    is_favorited: bool = False

    model_config = {"from_attributes": True}  #允许从SQLAlchemy模型自动转换(Pydantic v2)