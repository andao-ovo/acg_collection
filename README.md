# ACG收藏馆

动漫/小说/漫画收藏与评价系统的后端 API。

## 技术栈
- Python 3.10+
- FastAPI
- SQLAlchemy (ORM)
- SQLite
- Redis (缓存)
- JWT (用户认证)

## 功能
- ✅ 作品的增删改查
- ✅ 标签系统（多对多）
- ✅ 用户注册/登录（JWT 认证）
- ✅ Redis 缓存（统计、标签）
- ✅ 按类型、状态、标题模糊搜索
- ✅ 动态排序、分页
- ✅ 随机推荐
- ✅ 统计信息
- ✅ AI 推荐
- ✅ Swagger 自动文档

## API 接口
| 方法 | 路径 | 说明 | 需要认证 |
|------|------|------|---------|
| POST | /register | 注册 | 否 |
| POST | /login | 登录 | 否 |
| POST | /works | 添加作品 | 是 |
| GET | /works | 列表 | 否 |
| GET | /works/{id} | 详情 | 否 |
| PUT | /works/{id} | 更新 | 是 |
| DELETE | /works/{id} | 删除 | 是 |
| GET | /works/{id}/tags | 标签 | 否 |
| POST | /works/{id}/tags | 添加标签 | 是 |
| GET | /works/stats | 统计 | 否 |
| GET | /works/random | 随机推荐 | 否 |