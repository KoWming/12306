#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
任务相关的 Pydantic 模式
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatusEnum(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PassengerInfo(BaseModel):
    """乘车人信息"""
    passenger_name: str
    passenger_id_no: str
    passenger_id_type_code: str = "1"  # 身份证
    passenger_type: str = "1"  # 成人
    mobile_no: str = ""


class TaskCreate(BaseModel):
    """创建任务请求"""
    name: str = Field(..., min_length=1, max_length=200, description="任务名称")
    
    # 行程信息
    from_station: str = Field(..., description="出发站")
    to_station: str = Field(..., description="到达站")
    train_date: str = Field(..., description="出发日期 YYYY-MM-DD")
    
    # 筛选条件
    train_codes: Optional[List[str]] = Field(None, description="指定车次号")
    train_types: Optional[List[str]] = Field(None, description="车次类型，如 ['G', 'D']")
    seat_types: List[str] = Field(..., description="席别优先级，如 ['O', 'M', '9']")
    start_time_range: Optional[str] = Field(None, description="出发时间范围，如 08:00-12:00")
    
    # 乘车人
    passengers: List[PassengerInfo] = Field(..., min_length=1, description="乘车人列表")
    
    # 任务配置
    query_interval: int = Field(5, ge=3, le=60, description="刷票间隔（秒）")
    max_retry_count: int = Field(100, description="最大重试次数（-1表示无限）")
    auto_submit: bool = Field(True, description="自动提交订单")


class TaskUpdate(BaseModel):
    """更新任务请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    
    # 行程信息
    from_station: Optional[str] = None
    to_station: Optional[str] = None
    train_date: Optional[str] = None
    
    # 筛选条件
    train_codes: Optional[List[str]] = None
    train_types: Optional[List[str]] = None
    seat_types: Optional[List[str]] = None
    start_time_range: Optional[str] = None
    
    # 乘车人
    passengers: Optional[List[PassengerInfo]] = None
    
    query_interval: Optional[int] = Field(None, ge=3, le=60)
    max_retry_count: Optional[int] = Field(None, description="最大重试次数（-1表示无限）")
    auto_submit: Optional[bool] = None


class TaskResponse(BaseModel):
    """任务响应"""
    id: int
    user_id: int
    name: str
    
    from_station: str
    to_station: str
    train_date: str
    
    train_codes: Optional[str]
    train_types: Optional[str]
    seat_types: str
    start_time_range: Optional[str]
    
    passengers: str  # JSON string
    
    query_interval: int
    max_retry_count: int
    auto_submit: bool
    
    status: TaskStatusEnum
    retry_count: int
    
    order_id: Optional[str]
    result_message: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """任务列表响应"""
    total: int
    tasks: List[TaskResponse]


class TaskLogResponse(BaseModel):
    """任务日志响应"""
    id: int
    task_id: int
    level: str
    message: str
    details: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TaskLogsResponse(BaseModel):
    """任务日志列表响应"""
    total: int
    logs: List[TaskLogResponse]
