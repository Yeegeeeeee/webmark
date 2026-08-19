# webmark

一个使用 React、FastAPI 和 SQLite 构建的网址收藏应用，可在本地运行，也可使用 Render + Turso 部署。

## 项目结构

- `frontend/`：React + Vite 前端
- `backend/`：FastAPI 后端
- `backend/data/`：本地 SQLite 数据目录（首次启动后自动创建数据库）

## 启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 启动前端

另开一个终端：

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`，后端 API 默认运行在 `http://localhost:8000`。

## 云端部署

仓库根目录的 `render.yaml` 会创建一个 FastAPI Web Service 和一个 React Static Site。部署时需要配置：

- `TURSO_DATABASE_URL`：Turso 数据库地址
- `TURSO_AUTH_TOKEN`：Turso 数据库令牌
- `VITE_API_BASE_URL`：后端公开地址加 `/webmark`
