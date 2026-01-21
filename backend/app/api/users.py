#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户相关 API 接口
"""

import json
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..models.user import User
from ..schemas.common import ResponseBase
from ..schemas.task import PassengerInfo
from ..services.order_service import OrderService

router = APIRouter(prefix="/users", tags=["用户"])

@router.get("/{user_id}/passengers", response_model=ResponseBase[List[PassengerInfo]])
async def get_user_passengers(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取用户乘车人列表"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if not user.session_data:
        raise HTTPException(status_code=400, detail="用户未登录 12306")
        
    session_data = json.loads(user.session_data)
    # 兼容处理：如果是新格式（包含 cookies 键），取 cookies；否则假设整个对象就是 cookies 字典
    if "cookies" in session_data and isinstance(session_data["cookies"], dict):
        cookies = session_data["cookies"]
    else:
        cookies = session_data

    order_service = OrderService(cookies)
    
    try:
        success, passengers, msg = await order_service.query_passengers()
        await order_service.close()
        
        if success:
            # Convert OrderService.Passenger to Schema.PassengerInfo
            data = []
            for p in passengers:
                data.append(PassengerInfo(
                    passenger_name=p.passenger_name,
                    passenger_id_no=p.passenger_id_no,
                    passenger_id_type_code=p.passenger_id_type_code,
                    passenger_type=p.passenger_type,
                    mobile_no=p.mobile_no
                ))
            return ResponseBase(success=True, data=data)
        else:
             # Even if failed, return successful response with error message
             return ResponseBase(success=False, message=msg, data=[])
             
    except Exception as e:
        await order_service.close()
        return ResponseBase(success=False, message=str(e), data=[])
