#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志配置模块

配置应用日志，支持同时输出到控制台和文件，并提供日志轮转功能
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from .config import get_settings


def setup_logging(log_file: Optional[str] = None) -> None:
    """
    配置应用日志
    
    Args:
        log_file: 日志文件路径，如果为 None 则使用配置中的默认值
    """
    settings = get_settings()
    
    # 确定日志文件路径
    if log_file is None:
        log_file = f"{settings.LOG_DIR}/app.log"
    
    # 确保日志目录存在
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # 如果已经配置过处理器，先清除（避免重复配置）
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # 日志格式
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 1. 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 2. 文件处理器（带日志轮转）
    # maxBytes: 10MB, backupCount: 保留5个备份文件
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别的日志
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 记录日志配置完成
    root_logger.info(f"日志系统已初始化 - 文件: {log_file}")
    root_logger.info(f"日志级别: {settings.LOG_LEVEL}")


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称，通常使用 __name__
        
    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)
