#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统配置 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..models.config import SystemConfig
from ..tasks.scheduler import get_scheduler

router = APIRouter(tags=["config"])


class ConfigUpdate(BaseModel):
    cron: str = Field(..., description="Cron 表达式")
    enabled: bool = Field(False, description="是否启用")


class ConfigResponse(BaseModel):
    cron: str
    enabled: bool


@router.get("/config/global-schedule", response_model=ConfigResponse)
async def get_global_schedule(db: AsyncSession = Depends(get_db)):
    """获取全局定时配置"""
    # 获取 Cron
    stub_cron = await db.execute(select(SystemConfig).where(SystemConfig.key == "global_schedule_cron"))
    cron_config = stub_cron.scalar_one_or_none()
    
    # 获取 Enabled
    stub_enabled = await db.execute(select(SystemConfig).where(SystemConfig.key == "global_schedule_enabled"))
    enabled_config = stub_enabled.scalar_one_or_none()
    
    return {
        "cron": cron_config.value if cron_config else "",
        "enabled": (enabled_config.value == "true") if enabled_config else False
    }


@router.post("/config/global-schedule", response_model=ConfigResponse)
async def update_global_schedule(
    config: ConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新全局定时配置"""
    # 更新 Cron
    stmt_cron = select(SystemConfig).where(SystemConfig.key == "global_schedule_cron")
    result = await db.execute(stmt_cron)
    cron_obj = result.scalar_one_or_none()
    
    if cron_obj:
        cron_obj.value = config.cron
    else:
        cron_obj = SystemConfig(key="global_schedule_cron", value=config.cron)
        db.add(cron_obj)
        
    # 更新 Enabled
    stmt_enabled = select(SystemConfig).where(SystemConfig.key == "global_schedule_enabled")
    result = await db.execute(stmt_enabled)
    enabled_obj = result.scalar_one_or_none()
    
    val_str = "true" if config.enabled else "false"
    if enabled_obj:
        enabled_obj.value = val_str
    else:
        enabled_obj = SystemConfig(key="global_schedule_enabled", value=val_str)
        db.add(enabled_obj)
    
    await db.commit()
    
    # 通知调度器更新
    scheduler = get_scheduler()
    scheduler.update_global_schedule(config.cron, config.enabled)
    
    
    return {
        "cron": config.cron,
        "enabled": config.enabled
    }


@router.get("/config/notification")
async def get_notification_config(db: AsyncSession = Depends(get_db)):
    """获取通知配置"""
    stmt = select(SystemConfig).where(SystemConfig.key == "notification_settings")
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    
    if config and config.value:
        import json
        try:
            return json.loads(config.value)
        except:
            return {}
    return {}


@router.post("/config/notification")
async def update_notification_config(
    config: dict,
    db: AsyncSession = Depends(get_db)
):
    """更新通知配置"""
    import json
    stmt = select(SystemConfig).where(SystemConfig.key == "notification_settings")
    result = await db.execute(stmt)
    obj = result.scalar_one_or_none()
    
    value_str = json.dumps(config)
    
    if obj:
        obj.value = value_str
    else:
        obj = SystemConfig(key="notification_settings", value=value_str)
        db.add(obj)
    
    await db.commit()

    scheduler = get_scheduler()
    if hasattr(scheduler, "reload_notification_config"):
        await scheduler.reload_notification_config()
        
    return config


@router.post("/config/notification/test")
async def test_notification(
    config: dict,
    db: AsyncSession = Depends(get_db)
):
    """测试发送通知"""
    from ..utils import notify
    
    try:
        notify.send("测试通知", "恭喜！您的通知服务配置成功。\n这是一条由于点击[发送测试]按钮触发的消息。", ignore_default_config=True, **config)
        return {"success": True, "message": "测试请求已发送，请检查接收端"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

