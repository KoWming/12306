# 12306 自动化抢票系统

这是一个基于 Python FastAPI 和 Vue 3 开发的 12306 自动化抢票系统。包含后端 API 服务、前端管理界面以及一些独立的自动化脚本。

## 目录结构

- `backend/`: FastAPI 后端服务
    - `app/`: 应用代码
    - `data/`: 数据存储 (日志, Session 等)
- `frontend/`: Vue 3 + Vite 前端项目

## 环境准备

### 后端环境
- Python 3.10+

### 前端环境
- Node.js 16+
- npm 或 yarn

## Docker 部署（推荐）

### 方式一：使用 Docker Compose（最简单）

1. 确保已安装 Docker 和 Docker Compose

2. 项目已包含 `docker-compose.yml` 配置文件，内容如下：

```yaml
services:
  12306-assistant:
    image: kowming/12306-assistant:latest
    container_name: 12306-assistant
    restart: unless-stopped
    network_mode: host
    environment:
      TZ: Asia/Shanghai
      PYTHONUNBUFFERED: 1
      APP_PORT: 8000
    volumes:
      # 持久化数据库
      - ./data:/app/backend/data
```

3. 在项目根目录下创建数据目录：
```bash
mkdir -p data
```

4. 启动服务：
```bash
docker-compose up -d
```

4. 访问应用：http://localhost:8000

5. 停止服务：
```bash
docker-compose down
```

### 方式二：使用 Docker 镜像

```bash
# 拉取镜像
docker pull kowming/12306-assistant:latest

# 运行容器
docker run -d \
  --name 12306-assistant \
  --restart unless-stopped \
  --network host \
  -e TZ=Asia/Shanghai \
  -e PYTHONUNBUFFERED=1 \
  -e APP_PORT=8000 \
  -v $(pwd)/data:/app/backend/data \
  kowming/12306-assistant:latest
```

### 方式三：自行构建镜像

```bash
# 构建镜像
docker build -t 12306-assistant:local .

# 运行容器
docker run -d \
  --name 12306-assistant \
  --restart unless-stopped \
  --network host \
  -e TZ=Asia/Shanghai \
  -e APP_PORT=8000 \
  -v $(pwd)/data:/app/backend/data \
  12306-assistant:local
```

### Docker 部署说明

- **端口配置**: 默认使用 8000 端口，可通过环境变量 `APP_PORT` 修改
- **数据持久化**: 数据库和日志文件存储在 `./data` 目录，映射到容器的 `/app/backend/data`
- **时区设置**: 默认使用 `Asia/Shanghai` 时区
- **网络模式**: 使用 `host` 网络模式，方便访问本地服务
- **访问地址**: 
  - 前端界面: http://localhost:8000
  - API 文档: http://localhost:8000/docs

## 快速开始（本地开发）

### 1. 启动后端服务

进入 `backend` 目录，安装依赖并启动服务：

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务 (默认端口 8000)
# 也可以使用: uvicorn main:app --reload
python main.py
```

Swagger API 文档地址: http://localhost:8000/docs

### 2. 启动前端界面

进入 `frontend` 目录，安装依赖并启动开发服务器：

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问地址: http://localhost:5173 (默认 Vite 端口)
- 本项目仅供学习交流使用，请勿用于非法用途。
