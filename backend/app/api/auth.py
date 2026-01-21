#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
认证相关 API 接口

处理用户登录、二维码获取、状态检查等
"""

import json
import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..models.user import User
from ..schemas.user import (
    UserCreate, UserResponse, LoginStatusResponse,
    QRCodeResponse, QRCodeStatusResponse
)
from ..schemas.common import ResponseBase
from ..services.login_service import LoginService, QRCodeStatus

router = APIRouter(prefix="/auth", tags=["认证"])


# ==================== 用户管理 ====================

@router.post("/users", response_model=ResponseBase[UserResponse])
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建用户"""
    # 检查用户名是否已存在
    stmt = select(User).where(User.username == user_data.username)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        if existing.is_active:
            raise HTTPException(status_code=400, detail="用户名已存在")
        else:
            # 如果用户已存在 but is soft deleted, reactivate them
            existing.is_active = True
            existing.is_logged_in = False
            existing.session_data = None
            existing.railway_username = None
            await db.commit()
            await db.refresh(existing)
            
            return ResponseBase(
                success=True,
                message="用户创建成功",
                data=UserResponse.model_validate(existing)
            )
    
    user = User(username=user_data.username)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return ResponseBase(
        success=True,
        message="用户创建成功",
        data=UserResponse.model_validate(user)
    )


@router.get("/users", response_model=ResponseBase[list])
async def list_users(db: AsyncSession = Depends(get_db)):
    """获取用户列表"""
    stmt = select(User).where(User.is_active == True)
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return ResponseBase(
        success=True,
        data=[UserResponse.model_validate(u) for u in users]
    )


@router.get("/users/{user_id}", response_model=ResponseBase[UserResponse])
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """获取用户信息"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return ResponseBase(
        success=True,
        data=UserResponse.model_validate(user)
    )


# ==================== 登录状态 ====================

@router.get("/status/{user_id}", response_model=ResponseBase[LoginStatusResponse])
async def check_login_status(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """检查用户登录状态"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    login_service = LoginService(str(user_id))
    
    # 检查会话是否有效
    is_valid = False
    if login_service.is_logged_in():
        try:
            is_valid = await login_service.check_login_status()
        except Exception:
            pass
        finally:
            await login_service.close()
    
    # 更新数据库状态
    if user.is_logged_in != is_valid:
        user.is_logged_in = is_valid
        await db.commit()
    
    return ResponseBase(
        success=True,
        data=LoginStatusResponse(
            is_logged_in=is_valid,
            username=user.username,
            railway_username=login_service.get_username(),
            login_time=user.login_time,
            expire_time=user.session_expire_time
        )
    )


# ==================== 二维码登录 ====================

@router.post("/qrcode/{user_id}", response_model=ResponseBase[QRCodeResponse])
async def get_qr_code(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取登录二维码"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    login_service = LoginService(str(user_id))
    
    try:
        # 直接获取二维码（内部会处理设备指纹）
        uuid, image_b64, error = await login_service.get_qr_code()
        
        if error:
            raise HTTPException(status_code=500, detail=f"获取二维码失败: {error}")
        
        return ResponseBase(
            success=True,
            data=QRCodeResponse(uuid=uuid, image_base64=image_b64)
        )
    finally:
        await login_service.close()


@router.get("/qrcode/{user_id}/status", response_model=ResponseBase[QRCodeStatusResponse])
async def check_qr_status(
    user_id: int,
    uuid: str,
    db: AsyncSession = Depends(get_db)
):
    """检查二维码状态"""
    login_service = LoginService(str(user_id))
    
    try:
        status, uamtk = await login_service.check_qr_status(uuid)
        
        status_messages = {
            QRCodeStatus.WAITING: "等待扫码",
            QRCodeStatus.SCANNED: "已扫码，请确认",
            QRCodeStatus.CONFIRMED: "登录成功",
            QRCodeStatus.EXPIRED: "二维码已过期",
            QRCodeStatus.ERROR: "系统异常",
        }
        
        is_success = status == QRCodeStatus.CONFIRMED
        
        # 如果登录成功，完成认证
        if is_success:
            auth_success = await login_service.authenticate()
            if auth_success:
                # 更新数据库
                stmt = select(User).where(User.id == user_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                if user:
                    user.is_logged_in = True
                    user.railway_username = login_service.get_username()
                    # 保存完整会话信息 (包含 cookies, uamtk, apptk 等)
                    user.session_data = json.dumps(login_service.session.to_dict())
                    user.login_time = login_service.session.login_time
                    await db.commit()
        
        return ResponseBase(
            success=True,
            data=QRCodeStatusResponse(
                status=status,
                message=status_messages.get(status, "未知状态"),
                is_success=is_success
            )
        )
    finally:
        await login_service.close()


# ==================== WebSocket 扫码登录 ====================

@router.websocket("/ws/login/{user_id}")
async def websocket_login(
    websocket: WebSocket,
    user_id: int
):
    """WebSocket 扫码登录（实时推送状态）"""
    await websocket.accept()
    
    login_service = LoginService(str(user_id))
    
    try:
        # 获取二维码
        await websocket.send_json({"type": "status", "message": "正在获取二维码..."})
        uuid, image_b64, error = await login_service.get_qr_code()
        
        if error:
            await websocket.send_json({"type": "error", "message": f"获取二维码失败: {error}"})
            return
        
        # 发送二维码
        await websocket.send_json({
            "type": "qrcode",
            "uuid": uuid,
            "image": image_b64
        })
        
        # 轮询扫码状态
        last_status = None
        timeout = 120  # 2分钟超时
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                await websocket.send_json({"type": "timeout", "message": "扫码超时"})
                break
            
            status, uamtk = await login_service.check_qr_status(uuid)
            
            if status != last_status:
                last_status = status
                
                status_data = {
                    QRCodeStatus.WAITING: {"type": "waiting", "message": "等待扫码..."},
                    QRCodeStatus.SCANNED: {"type": "scanned", "message": "已扫码，请确认..."},
                    QRCodeStatus.CONFIRMED: {"type": "confirmed", "message": "登录确认成功"},
                    QRCodeStatus.EXPIRED: {"type": "expired", "message": "二维码已过期"},
                    QRCodeStatus.ERROR: {"type": "error", "message": "系统异常"},
                }
                
                await websocket.send_json(status_data.get(status, {"type": "unknown"}))
            
            if status == QRCodeStatus.CONFIRMED:
                # 完成认证
                auth_success = await login_service.authenticate()
                if auth_success:
                    await websocket.send_json({
                        "type": "success",
                        "message": f"登录成功，用户: {login_service.get_username()}",
                        "username": login_service.get_username()
                    })
                else:
                    await websocket.send_json({"type": "error", "message": "认证失败"})
                break
            
            if status in (QRCodeStatus.EXPIRED, QRCodeStatus.ERROR):
                break
            
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        pass
    finally:
        await login_service.close()


@router.post("/logout/{user_id}", response_model=ResponseBase)
async def logout(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """登出"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 清除会话
    login_service = LoginService(str(user_id))
    login_service.clear_session()
    
    # 更新数据库
    user.is_logged_in = False
    user.session_data = None
    await db.commit()
    
    return ResponseBase(success=True, message="已登出")


@router.delete("/users/{user_id}", response_model=ResponseBase)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除用户"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 清除用户会话
    login_service = LoginService(str(user_id))
    login_service.clear_session()
    
    # 软删除用户（将 is_active 设为 False）
    user.is_active = False
    user.is_logged_in = False
    user.session_data = None
    await db.commit()
    
    return ResponseBase(success=True, message="用户已删除")
