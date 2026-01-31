# 前端构建阶段
FROM node:lts-alpine AS frontend-builder
WORKDIR /app/frontend

# 复制前端源码
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

COPY frontend .
RUN npm run build

# 后端基础阶段
FROM python:3.10-slim
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

# 安装 Python 依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端源码到 /app/backend
COPY backend /app/backend

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# 切换到 backend 目录作为工作目录
WORKDIR /app/backend

# 暴露端口
EXPOSE 8000

# 设置默认端口
ENV APP_PORT=8000

# 启动应用（使用 shell 形式以支持环境变量）
CMD uvicorn main:app --host 0.0.0.0 --port ${APP_PORT}



