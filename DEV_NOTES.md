# ACG 收藏馆 - 开发进度记录

> 记录时间：2026-08-15
> 说明：这份文件用来记录工作进度和待办事项，方便下次接着做。

---

## 一、当前状态（已完成）

### ✅ 前端已完成（全部四个页面）
基于 **Vue 3 + Element Plus**，代码在 `frontend/` 目录下。

| 页面 | 文件 | 功能 |
|------|------|------|
| 作品列表页 | `frontend/src/views/WorkList.vue` | 筛选、排序、分页、随机推荐、新增/编辑作品 |
| 作品详情页 | `frontend/src/views/WorkDetail.vue` | 展示单作品 + 标签 + 评分 + 短评，编辑/删除 |
| 登录/注册页 | `frontend/src/views/Login.vue` | JWT 登录，注册后自动登录 |
| 统计页 | `frontend/src/views/Stats.vue` | KPI 卡片 + 类型/状态/评分图表(ECharts) |

其他关键文件：
- `frontend/vite.config.js` — 配置了 `/api` 代理到后端 `localhost:8000`
- `frontend/src/api/` — axios 封装（自动带 JWT）
- `frontend/start.bat` — 一键启动脚本（后端+前端）

### ✅ Git 冲突已修复
- 中止了之前由旧代码提交导致的冲突合并
- 本地/远程 `main` 分支现在一致，代码是完整新版
- 已推送远程，提交说明："添加 ACG 收藏馆前端...修复 schemas.py 兼容 Pydantic v2"

### ✅ 后端 bug 已修复（重要）
- **问题**：`GET /works/stats` 返回 422
- **原因**：`main.py` 里 `/works/stats` 定义在 `/works/{work_id}` 之后，被误当成作品 ID
- **修复**：把 `/works/stats` 和 `/works/random` 移到 `/works/{work_id}` 之前
- **验证**：三个接口（stats / random / works/1）实测均返回 200
- ⚠️ **注意**：此修复**尚未提交推送**（见下面待办 2）

### ✅ 其他改进
- 修复 `schemas.py` 的 `orm_mode` → `from_attributes`（兼容 Pydantic v2，消除警告）
- 给 venv 安装了后端依赖（FastAPI、SQLAlchemy、redis 等）

---

## 二、待办事项（明天接着做）

- [ ] **1. 重启后端**：因为修了 `main.py`，需要重新启动后端才能生效。
      → 直接双击 `frontend\start.bat` 即可（会自动启动后端+前端）。
      如果不想连带前端，单独启动：
      ```
      cd /d D:\虚拟c盘\study\0.4更新用户系统
      venv\Scripts\activate
      uvicorn main:app --reload
      ```
- [ ] **2. 提交推送 `main.py` 的路由修复**（今天改了但还没 commit/push）：
      ```
      git add main.py
      git commit -m "修复 /works/stats 和 /works/random 被 {work_id} 误拦截的路由顺序问题"
      git push origin main
      ```
- [ ] 3. 前端如有细节想调整（配色、布局等），改完记得也提交。

---

## 三、启动方法（一键）

**双击** `frontend\start.bat`，会自动：
1. 检查/启动 Redis
2. 启动后端 FastAPI（新窗口，端口 8000）
3. 启动前端 Vite（新窗口，端口 5173）

访问地址：
- 前端页面：http://localhost:5173
- 后端接口文档(Swagger)：http://localhost:8000/docs

> 小提示：数据库 `acg.db` 里现在有 3 条测试数据（title 是 1/a 之类的测试内容），如果不需要可以在网页里删掉。

---

## 四、环境要点（排错参考）

- **编码**：`frontend\start.bat` 必须是 **ANSI/GBK 编码**，否则双击会报一堆"不是内部或外部命令"（中文乱码导致）。已修好。
- **Redis**：后端部分接口（统计、标签）依赖 Redis，需要先启动（在 `C:\Program Files\Redis\redis-server.exe`）。没开 Redis 时 `/works/stats` 会报错。
- **代理**：git 推送 GitHub 需要梯子，本机代理为 `127.0.0.1:7892`，已配置到 git。