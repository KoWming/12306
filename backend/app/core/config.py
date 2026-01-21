#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
核心配置模块

包含应用的所有配置项
"""

import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用信息
    APP_NAME: str = "12306 自动化抢票系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API 配置
    API_V1_PREFIX: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/12306.db"
    
    # 会话配置
    SESSION_DIR: str = "./data/sessions"
    
    # 任务调度配置
    SCHEDULER_TIMEZONE: str = "Asia/Shanghai"
    DEFAULT_QUERY_INTERVAL: int = 5  # 默认刷票间隔（秒）
    MIN_QUERY_INTERVAL: int = 3      # 最小刷票间隔（秒）
    MAX_QUERY_INTERVAL: int = 60     # 最大刷票间隔（秒）
    
    # 12306 相关配置
    STATION_FILE: str = "./data/assets/station_name.js"
    
    # CORS 配置
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
    
    # JWT 配置（如果需要用户认证）
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./data/logs"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 创建必要的目录
def ensure_directories():
    """确保必要的目录存在"""
    settings = get_settings()
    
    dirs = [
        Path("./data"),
        Path(settings.SESSION_DIR),
        Path(settings.LOG_DIR),
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
