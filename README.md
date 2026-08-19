# webmark

一个使用 React、FastAPI 和 SQLite 构建的网址收藏应用，可在本地运行，也可使用 Vercel + Turso 部署。

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

## 桌面应用

桌面版把 React 页面和 FastAPI 服务打包为一个应用，双击即可运行。数据库保存在当前用户的数据目录：

- macOS：`~/Library/Application Support/Webmark/webmark.db`
- Windows：`%LOCALAPPDATA%\Webmark\webmark.db`

macOS 构建命令为 `./scripts/build_macos.sh`，输出 `dist/Webmark.app`。Windows 可在 GitHub Actions 中手动运行 `Build Windows app`，或者在 Windows 上执行 `scripts/build_windows.ps1`，输出 `dist/Webmark.exe`。

## 云端部署

前端和后端可分别作为 Vercel 项目部署，云端数据库使用 Turso。部署时需要配置：

- `TURSO_DATABASE_URL`：Turso 数据库地址
- `TURSO_AUTH_TOKEN`：Turso 数据库令牌
- `VITE_API_BASE_URL`：后端公开地址加 `/webmark`
