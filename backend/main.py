#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
12306 自动化抢票系统 - FastAPI 后端入口

启动命令:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# 添加父目录到路径（用于导入原始脚本模块）
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings, ensure_directories
from app.core.database import init_db, close_db
from app.api import auth, trains, tasks, users, config
from app.tasks.scheduler import get_scheduler

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("\n" + "=" * 50)
    print(f"🚄 {settings.APP_NAME} v{settings.APP_VERSION}")
    print("=" * 50)
    
    # 确保目录存在
    ensure_directories()
    
    # 初始化数据库
    await init_db()
    
    # 启动调度器
    scheduler = get_scheduler()
    scheduler.start()
    # 恢复运行中的任务
    await scheduler.resume_tasks()
    
    print("[启动] 服务启动成功!")
    print(f"[启动] API 文档: http://localhost:8000/docs")
    print("=" * 50 + "\n")
    
    yield
    
    # 关闭时
    print("\n[关闭] 正在关闭服务...")
    
    # 关闭调度器
    scheduler.shutdown()
    
    # 关闭数据库连接
    await close_db()
    
    print("[关闭] 服务已关闭\n")

# 创建应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    12306 自动化抢票系统 API
    
    ## 功能
    
    * **认证模块**: 扫码登录、会话管理
    * **查票模块**: 车票查询、车站搜索
    * **任务模块**: 抢票任务的创建、管理、执行
    
    ## 使用说明
    
    1. 创建用户
    2. 扫码登录 12306
    3. 创建抢票任务
    4. 启动任务，等待抢票成功
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": str(exc),
            "error_code": "INTERNAL_ERROR"
        }
    )

# 注册路由
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(trains.router, prefix=settings.API_V1_PREFIX)
app.include_router(tasks.router, prefix=settings.API_V1_PREFIX)
app.include_router(config.router, prefix=settings.API_V1_PREFIX)
app.include_router(config.router, prefix=settings.API_V1_PREFIX)

# 挂载静态文件
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if (frontend_dist / "assets").exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.get("/")
async def serve_root():
    """根路径返回前端首页"""
    if (frontend_dist / "index.html").exists():
        return FileResponse(frontend_dist / "index.html")
    return JSONResponse(
        content={
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "message": "Frontend not built or not found"
        }
    )

# SPA Catch-all 路由
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # 如果是 API 请求，返回 404 (由 api_router 处理，这里只处理未匹配的)
    if full_path.startswith("api/"):
        return JSONResponse({"error": "Not Found"}, status_code=404)
        
    # 尝试提供静态文件
    static_file = frontend_dist / full_path
    if static_file.is_file():
        return FileResponse(static_file)

    # 默认返回 index.html
    if (frontend_dist / "index.html").exists():
        return FileResponse(frontend_dist / "index.html")
    
    return "Frontend not built. Please run 'npm run build' in frontend directory.", 500


# 开发时直接运行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
