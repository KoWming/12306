#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查票相关 API 接口
"""

from typing import List, Optional, Tuple
from fastapi import APIRouter, Query, HTTPException

from ..schemas.query import (
    QueryRequest, QueryResponse, TrainInfoResponse,
    StationResponse, StationSearchResponse,
    TrainTypeEnum, SeatTypeEnum, TicketTypeEnum
)
from ..schemas.common import ResponseBase
from ..services.query_service import QueryService

router = APIRouter(prefix="/trains", tags=["查票"])


# 全局查票服务实例
_query_service: Optional[QueryService] = None


def get_query_service() -> QueryService:
    """获取查票服务实例"""
    global _query_service
    if _query_service is None:
        _query_service = QueryService()
    return _query_service


@router.get("/query", response_model=QueryResponse)
async def query_tickets(
    from_station: str = Query(..., description="出发站"),
    to_station: str = Query(..., description="到达站"),
    train_date: str = Query(..., description="出发日期 YYYY-MM-DD"),
    ticket_type: TicketTypeEnum = Query(TicketTypeEnum.ADULT, description="票种"),
    train_types: Optional[str] = Query(None, description="车次类型，逗号分隔，如 G,D"),
    start_time_min: Optional[str] = Query(None, description="最早出发时间，如 08:00"),
    start_time_max: Optional[str] = Query(None, description="最晚出发时间，如 12:00"),
    only_has_ticket: bool = Query(False, description="只显示有票车次")
):
    """
    查询车票
    
    - **from_station**: 出发站名称或代码
    - **to_station**: 到达站名称或代码
    - **train_date**: 出发日期，格式 YYYY-MM-DD
    - **ticket_type**: 票种（成人票/学生票）
    - **train_types**: 车次类型筛选，如 G,D 表示高铁和动车
    - **start_time_min/max**: 出发时间范围
    - **only_has_ticket**: 是否只返回有票车次
    """
    service = get_query_service()
    
    # 处理车次类型
    types_list = None
    if train_types:
        types_list = [t.strip() for t in train_types.split(",")]
    
    # 处理时间范围
    time_range = None
    if start_time_min and start_time_max:
        time_range = (start_time_min, start_time_max)
    
    try:
        trains, error = await service.query(
            from_station=from_station,
            to_station=to_station,
            train_date=train_date,
            ticket_type=ticket_type.value,
            train_types=types_list,
            start_time_range=time_range,
            only_has_ticket=only_has_ticket
        )
        
        if error:
            return QueryResponse(success=False, message=error)
        
        # 转换为响应格式
        train_responses = [
            TrainInfoResponse(**t.to_dict()) for t in trains
        ]
        
        return QueryResponse(
            success=True,
            total=len(train_responses),
            trains=train_responses
        )
        
    except Exception as e:
        return QueryResponse(success=False, message=str(e))


@router.post("/query", response_model=QueryResponse)
async def query_tickets_post(request: QueryRequest):
    """
    查询车票（POST 方式）
    
    支持更复杂的查询参数
    """
    service = get_query_service()
    
    # 处理车次类型
    types_list = None
    if request.train_types:
        types_list = [t.value for t in request.train_types]
    
    try:
        trains, error = await service.query(
            from_station=request.from_station,
            to_station=request.to_station,
            train_date=request.train_date,
            ticket_type=request.ticket_type.value,
            train_types=types_list,
            start_time_range=request.start_time_range,
            only_has_ticket=request.only_has_ticket
        )
        
        if error:
            return QueryResponse(success=False, message=error)
        
        train_responses = [
            TrainInfoResponse(**t.to_dict()) for t in trains
        ]
        
        return QueryResponse(
            success=True,
            total=len(train_responses),
            trains=train_responses
        )
        
    except Exception as e:
        return QueryResponse(success=False, message=str(e))


@router.get("/stations/search", response_model=StationSearchResponse)
async def search_stations(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    """
    搜索车站
    
    支持站名、拼音、首字母搜索
    """
    service = get_query_service()
    stations = service.search_stations(keyword, limit)
    
    return StationSearchResponse(
        total=len(stations),
        stations=[
            StationResponse(
                name=s.name,
                code=s.code,
                pinyin=s.pinyin,
                short_pinyin=s.short_pinyin,
                city=s.city
            )
            for s in stations
        ]
    )


@router.get("/stations", response_model=StationSearchResponse)
async def list_all_stations(
    limit: int = Query(100, ge=1, le=5000, description="返回数量限制")
):
    """获取所有车站列表"""
    service = get_query_service()
    stations = service.station_manager.get_all_stations()[:limit]
    
    return StationSearchResponse(
        total=len(stations),
        stations=[
            StationResponse(
                name=s.name,
                code=s.code,
                pinyin=s.pinyin,
                short_pinyin=s.short_pinyin,
                city=s.city
            )
            for s in stations
        ]
    )
