#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通用响应模式
"""

from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')


class ResponseBase(BaseModel, Generic[T]):
    """通用响应基类"""
    success: bool = True
    message: str = ""
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Any] = None
