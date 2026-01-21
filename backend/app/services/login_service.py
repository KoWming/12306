#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
登录服务

封装 12306 扫码登录逻辑，支持多用户 Session 管理
"""

import json
import base64
import time
import asyncio
import random
import string
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, Callable
from dataclasses import dataclass, field
import httpx

from ..core.config import get_settings

settings = get_settings()


class QRCodeStatus:
    """二维码扫描状态"""
    WAITING = 0       # 等待扫码
    SCANNED = 1       # 已扫码，等待确认
    CONFIRMED = 2     # 确认登录（成功）
    EXPIRED = 3       # 二维码过期
    ERROR = 5         # 系统异常


@dataclass
class LoginSession:
    """登录会话信息"""
    cookies: Dict[str, str] = field(default_factory=dict)
    uamtk: str = ""
    apptk: str = ""
    username: str = ""
    is_logged_in: bool = False
    login_time: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """转换为可序列化的字典"""
        return {
            "cookies": self.cookies,
            "uamtk": self.uamtk,
            "apptk": self.apptk,
            "username": self.username,
            "is_logged_in": self.is_logged_in,
            "login_time": self.login_time.isoformat() if self.login_time else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "LoginSession":
        """从字典创建会话"""
        session = cls()
        session.cookies = data.get("cookies", {})
        session.uamtk = data.get("uamtk", "")
        session.apptk = data.get("apptk", "")
        session.username = data.get("username", "")
        session.is_logged_in = data.get("is_logged_in", False)
        login_time = data.get("login_time")
        session.login_time = datetime.fromisoformat(login_time) if login_time else None
        return session


class LoginService:
    """登录服务类（支持多用户）"""
    
    # API 端点
    BASE_URL = "https://kyfw.12306.cn"
    PASSPORT_URL = "https://kyfw.12306.cn/passport"
    
    QR_CREATE_URL = f"{PASSPORT_URL}/web/create-qr64"
    QR_CHECK_URL = f"{PASSPORT_URL}/web/checkqr"
    UAMTK_URL = f"{PASSPORT_URL}/web/auth/uamtk"
    UAMAUTHCLIENT_URL = f"{BASE_URL}/otn/uamauthclient"
    USER_INFO_URL = f"{BASE_URL}/otn/index/initMy12306Api"
    
    APP_ID = "otn"
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://kyfw.12306.cn',
        'Referer': 'https://kyfw.12306.cn/otn/resources/login.html',
        'X-Requested-With': 'XMLHttpRequest',
    }
    
    # 用户会话存储（内存 + 文件持久化）
    _sessions: Dict[str, LoginSession] = {}
    _session_dir: Path = None
    
    def __init__(self, user_id: str = "default"):
        """
        初始化登录服务
        
        Args:
            user_id: 用户标识（用于多用户支持）
        """
        self.user_id = user_id
        self._client: Optional[httpx.AsyncClient] = None
        
        # 确保会话目录存在
        if LoginService._session_dir is None:
            LoginService._session_dir = Path(settings.SESSION_DIR)
            LoginService._session_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载用户会话
        self._load_session()
    
    @property
    def session(self) -> LoginSession:
        """获取当前用户的会话"""
        if self.user_id not in LoginService._sessions:
            LoginService._sessions[self.user_id] = LoginSession()
        return LoginService._sessions[self.user_id]
    
    @session.setter
    def session(self, value: LoginSession):
        """设置当前用户的会话"""
        LoginService._sessions[self.user_id] = value
    
    async def get_client(self) -> httpx.AsyncClient:
        """获取异步 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=self.HEADERS,
                timeout=30.0,
                verify=False,
                follow_redirects=True
            )
            if self.session.cookies:
                self._client.cookies.update(self.session.cookies)
        return self._client
    
    async def close(self):
        """关闭客户端连接"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    # ==================== 会话管理 ====================
    
    def _get_session_file(self) -> Path:
        """获取会话文件路径"""
        return LoginService._session_dir / f"session_{self.user_id}.json"
    
    def _load_session(self) -> bool:
        """加载会话"""
        session_file = self._get_session_file()
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.session = LoginSession.from_dict(data)
                return True
            except Exception:
                pass
        return False
    
    def _save_session(self):
        """保存会话"""
        session_file = self._get_session_file()
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(self.session.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def clear_session(self):
        """清除会话"""
        self.session = LoginSession()
        session_file = self._get_session_file()
        if session_file.exists():
            session_file.unlink()
    
    # ==================== 设备指纹 ====================
    
    def _generate_synthetic_device_fingerprint(self) -> Dict[str, str]:
        """生成合成的设备指纹（不推荐，可能被拦截）"""
        ts = int(time.time() * 1000)
        random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
        rail_deviceid = f"AlgID_X{ts}{random_suffix}"
        exp = int(time.time() * 1000) + 315360000000
        
        return {
            "RAIL_DEVICEID": rail_deviceid,
            "RAIL_EXPIRATION": str(exp)
        }

    def _get_device_fingerprint_sync(self, headless: bool = False) -> Dict[str, str]:
        """
        使用同步 Playwright 获取设备指纹 Cookie（在线程池中运行）
        默认使用非无头模式以提高成功率
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[登录] 未安装 Playwright，使用合成指纹（可能被拦截）")
            return self._generate_synthetic_device_fingerprint()
        
        cookies_dict = {}
        
        try:
            with sync_playwright() as p:
                # 使用非无头模式，更真实的浏览器环境
                browser = p.chromium.launch(
                    headless=headless,
                    args=['--disable-blink-features=AutomationControlled']
                )
                context = browser.new_context(
                    user_agent=self.HEADERS['User-Agent'],
                    viewport={'width': 1920, 'height': 1080},
                    ignore_https_errors=True,
                    locale='zh-CN'
                )
                page = context.new_page()
                
                # 反爬虫脚本
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                """)
                
                try:
                    print("[登录] 正在访问12306获取设备指纹...")
                    # 访问首页，更容易触发设备指纹生成
                    page.goto("https://kyfw.12306.cn/otn/resources/login.html", wait_until="domcontentloaded", timeout=10000)
                    
                    # 等待页面完全加载和JS执行
                    time.sleep(2)
                    
                    # 检查cookie
                    def check_cookie():
                        current_cookies = context.cookies()
                        for c in current_cookies:
                            if c['name'] == 'RAIL_DEVICEID':
                                return True
                        return False

                    # 轮询检查，最多8秒（减少等待时间）
                    for i in range(8):
                        if check_cookie():
                            print("[登录] ✓ 成功获取设备指纹")
                            break
                        if i % 3 == 0:
                            # 尝试触发更多JS执行
                            page.evaluate("() => { document.body.click(); }")
                        time.sleep(1)
                    else:
                        print("[登录] ⚠ 未能获取到设备指纹，将使用合成指纹")
                    
                    cookies = context.cookies()
                    for cookie in cookies:
                        cookies_dict[cookie['name']] = cookie['value']
                    
                except Exception as e:
                    print(f"[登录] 浏览器访问失败: {e}")
                finally:
                    browser.close()
        except Exception as e:
            print(f"[登录] Playwright 执行失败: {e}")

        # 检查是否获取到设备指纹
        if "RAIL_DEVICEID" not in cookies_dict:
            print("[登录] ⚠ 使用合成设备指纹（可能被12306拦截）")
            synthetic = self._generate_synthetic_device_fingerprint()
            cookies_dict.update(synthetic)
        else:
            print(f"[登录] ✓ 设备指纹: {cookies_dict['RAIL_DEVICEID'][:20]}...")
            
        return cookies_dict
    
    async def get_device_fingerprint(self, headless: bool = False) -> Dict[str, str]:
        """
        使用 Playwright 获取设备指纹 Cookie
        默认使用非无头模式（headless=False）以提高成功率
        在 Windows 上，Playwright 异步模式与 uvicorn 事件循环不兼容，
        因此使用线程池执行同步版本。
        """
        # 在线程池中运行同步的 Playwright
        loop = asyncio.get_event_loop()
        cookies_dict = await loop.run_in_executor(
            None,  # 使用默认线程池
            self._get_device_fingerprint_sync,
            headless
        )
        
        self.session.cookies.update(cookies_dict)
        self._save_session()
        
        return cookies_dict

    # ==================== 二维码登录 ====================
    
    async def get_qr_code(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        获取登录二维码
        
        Returns:
            (uuid, image_base64, error_message)
        """
        # 检查是否已有设备指纹 (RAIL_DEVICEID)
        if "RAIL_DEVICEID" not in self.session.cookies:
            # 直接使用合成指纹（避免长时间等待导致前端超时）
            print("[登录] 使用合成设备指纹（快速获取二维码）")
            synthetic = self._generate_synthetic_device_fingerprint()
            self.session.cookies.update(synthetic)
            self._save_session()
        
        # ... (rest of function)
        client = await self.get_client()
        
        try:
            response = await client.post(self.QR_CREATE_URL, data={"appid": self.APP_ID})
            result = response.json()
            
            if result.get("result_code") == "0":
                uuid = result.get("uuid")
                image_b64 = result.get("image")
                return uuid, image_b64, None
            else:
                error = result.get("result_message", "未知错误")
                return None, None, error
                
        except Exception as e:
            return None, None, str(e)
    
    async def check_qr_status(self, uuid: str) -> Tuple[int, Optional[str]]:
        """
        检查二维码扫描状态
        
        Returns:
            (status_code, uamtk)
        """
        client = await self.get_client()
        
        try:
            data = {
                "RAIL_DEVICEID": self.session.cookies.get("RAIL_DEVICEID", ""),
                "RAIL_EXPIRATION": self.session.cookies.get("RAIL_EXPIRATION", ""),
                "uuid": uuid,
                "appid": self.APP_ID
            }
            
            response = await client.post(self.QR_CHECK_URL, data=data)
            result = response.json()
            
            result_code = int(result.get("result_code", -1))
            uamtk = result.get("uamtk")
            
            return result_code, uamtk
            
        except Exception:
            return QRCodeStatus.ERROR, None
    
    async def poll_qr_status(
        self,
        uuid: str,
        interval: float = 2.0,
        timeout: float = 120.0,
        on_status_change: Optional[Callable[[int], None]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        轮询二维码扫描状态
        
        Returns:
            (success, uamtk)
        """
        start_time = time.time()
        last_status = None
        
        while True:
            if time.time() - start_time > timeout:
                return False, None
            
            status, uamtk = await self.check_qr_status(uuid)
            
            if status != last_status:
                last_status = status
                if on_status_change:
                    on_status_change(status)
            
            if status == QRCodeStatus.CONFIRMED:
                return True, uamtk
            elif status in (QRCodeStatus.EXPIRED, QRCodeStatus.ERROR):
                return False, None
            
            await asyncio.sleep(interval)
    
    # ==================== 登录认证 ====================
    
    async def authenticate(self) -> bool:
        """完成登录认证流程"""
        client = await self.get_client()
        
        try:
            # 获取 uamtk
            response = await client.post(self.UAMTK_URL, data={"appid": self.APP_ID})
            result = response.json()
            
            if result.get("result_code") != 0:
                return False
            
            new_apptk = result.get("newapptk")
            if not new_apptk:
                return False
            
            self.session.uamtk = new_apptk
            
            # 获取 apptk
            response = await client.post(self.UAMAUTHCLIENT_URL, data={"tk": new_apptk})
            result = response.json()
            
            if result.get("result_code") != 0:
                return False
            
            self.session.apptk = result.get("apptk", "")
            self.session.username = result.get("username", "")
            self.session.is_logged_in = True
            self.session.login_time = datetime.now()
            
            # 更新 cookies
            for cookie in client.cookies.jar:
                self.session.cookies[cookie.name] = cookie.value
            
            # 关键：检查认证后的 cookies 中是否包含 RAIL_DEVICEID
            # 如果认证过程中丢失了，重新补上
            if "RAIL_DEVICEID" not in self.session.cookies:
                 print("[Warning] RAIL_DEVICEID lost during auth! Injecting synthetic one.")
                 synthetic = self._generate_synthetic_device_fingerprint()
                 self.session.cookies.update(synthetic)

            self._save_session()
            
            return True
            
        except Exception:
            return False
    
    async def check_login_status(self) -> bool:
        """检查登录状态是否有效"""
        if not self.session.is_logged_in:
            return False
        
        client = await self.get_client()
        
        try:
            response = await client.post(
                self.USER_INFO_URL,
                data={"_json_att": ""}
            )
            result = response.json()
            
            if result.get("status") and result.get("data"):
                return True
            return False
            
        except Exception:
            return False
    
    # ==================== 完整登录流程 ====================
    
    async def login_with_qr(
        self,
        on_qr_code: Optional[Callable[[str, str], None]] = None,
        on_status_change: Optional[Callable[[int], None]] = None
    ) -> Tuple[bool, str]:
        """
        完整的扫码登录流程
        
        Args:
            on_qr_code: 二维码回调 (uuid, image_base64)
            on_status_change: 状态变化回调
            
        Returns:
            (success, message)
        """
        # 1. 获取设备指纹
        try:
            await self.get_device_fingerprint()
        except Exception as e:
            return False, f"获取设备指纹失败: {e}"
        
        # 2. 获取二维码
        uuid, image_b64, error = await self.get_qr_code()
        if error:
            return False, f"获取二维码失败: {error}"
        
        if on_qr_code:
            on_qr_code(uuid, image_b64)
        
        # 3. 轮询扫码状态
        success, uamtk = await self.poll_qr_status(
            uuid,
            on_status_change=on_status_change
        )
        
        if not success:
            return False, "扫码失败或超时"
        
        # 4. 完成认证
        if await self.authenticate():
            return True, f"登录成功，用户: {self.session.username}"
        else:
            return False, "认证失败"
    
    def get_cookies(self) -> Dict[str, str]:
        """获取当前会话的 cookies"""
        return self.session.cookies.copy()
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self.session.is_logged_in
    
    def get_username(self) -> Optional[str]:
        """获取用户名"""
        return self.session.username if self.session.is_logged_in else None
