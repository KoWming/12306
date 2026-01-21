#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查票相关的 Pydantic 模式
"""

from datetime import date
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field
from enum import Enum


class TrainTypeEnum(str, Enum):
    """车次类型"""
    G = "G"  # 高铁
    C = "C"  # 城际
    D = "D"  # 动车
    Z = "Z"  # 直达
    T = "T"  # 特快
    K = "K"  # 快速
    OTHER = "O"  # 其他


class SeatTypeEnum(str, Enum):
    """席别类型"""
    BUSINESS = "9"      # 商务座
    PREMIER_FIRST = "P" # 优选一等座
    FIRST = "M"         # 一等座
    SECOND = "O"        # 二等座
    SOFT_SLEEPER = "4"  # 软卧
    HARD_SLEEPER = "3"  # 硬卧
    SOFT_SEAT = "2"     # 软座
    HARD_SEAT = "1"     # 硬座
    NO_SEAT = "0"       # 无座


class TicketTypeEnum(str, Enum):
    """票种类型"""
    ADULT = "ADULT"
    STUDENT = "0X00"


class QueryRequest(BaseModel):
    """查票请求"""
    from_station: str = Field(..., description="出发站")
    to_station: str = Field(..., description="到达站")
    train_date: str = Field(..., description="出发日期 YYYY-MM-DD")
    ticket_type: TicketTypeEnum = Field(TicketTypeEnum.ADULT, description="票种")
    train_types: Optional[List[TrainTypeEnum]] = Field(None, description="车次类型筛选")
    seat_types: Optional[List[SeatTypeEnum]] = Field(None, description="席别筛选")
    start_time_range: Optional[Tuple[str, str]] = Field(None, description="出发时间范围，如 ('08:00', '12:00')")
    only_has_ticket: bool = Field(False, description="只显示有票车次")


class TrainInfoResponse(BaseModel):
    """车次信息响应"""
    train_no: str
    train_code: str
    start_station: str
    end_station: str
    from_station: str
    to_station: str
    from_station_code: str
    to_station_code: str
    start_time: str
    arrive_time: str
    duration: str
    can_buy: bool
    train_date: str
    
    # 各席别余票
    business_seat: str = "--"
    premier_first: str = "--"
    first_seat: str = "--"
    second_seat: str = "--"
    advanced_soft_sleeper: str = "--"
    soft_sleeper: str = "--"
    hard_sleeper: str = "--"
    soft_seat: str = "--"
    hard_seat: str = "--"
    no_seat: str = "--"
    first_sleeper: str = "--"
    second_sleeper: str = "--"
    
    is_support_card: bool = False
    remark: str = ""
    secret_str: str = ""


class QueryResponse(BaseModel):
    """查票响应"""
    success: bool
    message: str = ""
    total: int = 0
    trains: List[TrainInfoResponse] = []


class StationResponse(BaseModel):
    """车站信息响应"""
    name: str
    code: str
    pinyin: str
    short_pinyin: str
    city: str = ""


class StationSearchResponse(BaseModel):
    """车站搜索响应"""
    total: int
    stations: List[StationResponse]
