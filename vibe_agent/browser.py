"""
浏览器管理器 - Playwright 浏览器生命周期管理
"""

import os
import time
import random
from pathlib import Path
from typing import Optional

from playwright.sync_api import (
    Playwright,
    Browser,
    BrowserContext,
    Page,
    sync_playwright,
    TimeoutError as PWTimeoutError,
)

from .config import get_config, DEFAULT_CONFIG


class BrowserManager:
    """浏览器管理器，封装 Playwright 的启动、页面管理、截图"""

    def __init__(self, headless: Optional[bool] = None, slow_mo: Optional[int] = None):
        cfg = get_config()
        self.headless = headless if headless is not None else cfg.get("headless", False)
        self.slow_mo = slow_mo if slow_mo is not None else cfg.get("slow_mo", 500)
        self.timeout = cfg.get("timeout", 30000)
        self.stealth = cfg.get("stealth", True)

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        # 截图目录
        self.screenshot_dir = Path(__file__).resolve().parent.parent / "screenshots"
        self.screenshot_dir.mkdir(exist_ok=True)

    def start(self, user_data_dir: Optional[str] = None) -> Page:
        """启动浏览器并返回页面对象"""
        self._playwright = sync_playwright().start()

        launch_options = {
            "headless": self.headless,
            "slow_mo": self.slow_mo,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        }

        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
            "ignore_https_errors": True,
        }

        if user_data_dir:
            persistent_path = Path(user_data_dir)
            persistent_path.mkdir(parents=True, exist_ok=True)
            merged_opts = {**launch_options, **context_options}
            self._context = self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(persistent_path),
                **merged_opts
            )
            self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
        else:
            self._browser = self._playwright.chromium.launch(**launch_options)
            self._context = self._browser.new_context(**context_options)
            self._page = self._context.new_page()

        # 反检测（stealth 模式）
        if self.stealth:
            self._apply_stealth()

        self._page.set_default_timeout(self.timeout)

        # 控制台日志监听
        self._page.on("console", lambda msg: self._on_console(msg))

        return self._page

    def _apply_stealth(self):
        """注入反检测脚本"""
        self._context.add_init_script("""
            // 覆盖 webdriver 属性
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });

            // 覆盖 chrome 属性
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {},
            };

            // 覆盖权限查询
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );

            // 覆盖 plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            // 覆盖 languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en'],
            });
        """)

    def _on_console(self, msg):
        """控制台消息处理（调试用）"""
        pass  # 可通过设置 DEBUG=1 开启

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("浏览器未启动，请先调用 start()")
        return self._page

    def navigate(self, url: Optional[str] = None) -> Page:
        """导航到指定 URL"""
        if url is None:
            cfg = get_config()
            url = cfg.get("base_url", DEFAULT_CONFIG["base_url"])
        self.page.goto(url, wait_until="networkidle", timeout=self.timeout)
        return self.page

    def screenshot(self, name: str = "screenshot") -> str:
        """截图保存，返回路径"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        path = str(self.screenshot_dir / f"{name}_{timestamp}.png")
        self.page.screenshot(path=path, full_page=True)
        return path

    def wait_for_selector(
        self, selector: str, timeout: Optional[int] = None, state: str = "visible"
    ) -> bool:
        """等待元素出现"""
        try:
            self.page.wait_for_selector(selector, timeout=timeout or self.timeout, state=state)
            return True
        except PWTimeoutError:
            return False

    def wait_for_load(self):
        """等待页面完全加载"""
        try:
            self.page.wait_for_load_state("networkidle", timeout=self.timeout)
        except PWTimeoutError:
            pass  # 网络空闲超时，继续执行

    def random_delay(self, min_ms: int = 300, max_ms: int = 1000):
        """随机延迟，模拟人类操作"""
        time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

    def human_type(self, selector: str, text: str, delay_ms: int = 100):
        """模拟人类打字"""
        self.page.click(selector)
        self.random_delay(100, 300)
        self.page.fill(selector, "")
        for char in text:
            self.page.type(selector, char, delay=delay_ms)
            self.random_delay(20, 80)

    def close(self):
        """关闭浏览器"""
        try:
            if self._page:
                self._page.close()
        except Exception:
            pass
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # --- 调试工具 ---

    def dump_page_state(self) -> dict:
        """转储页面状态用于调试"""
        page = self.page
        return {
            "url": page.url,
            "title": page.title(),
            "html_length": len(page.content()),
            "visible_text": page.inner_text("body")[:500],
        }

    def find_visible_elements(self, css: str = "button, input, textarea, select, a, [role='button'], [class*='btn']") -> list[dict]:
        """查找页面上所有可交互元素"""
        elements = self.page.query_selector_all(css)
        result = []
        for el in elements:
            try:
                tag = el.evaluate("el => el.tagName.toLowerCase()")
                text = el.inner_text().strip()[:50] if el.inner_text() else ""
                visible = el.is_visible()
                attrs = el.evaluate("el => ({id: el.id, class: el.className, type: el.type, name: el.name, placeholder: el.placeholder, href: el.href, 'data-testid': el.getAttribute('data-testid'), 'data-test': el.getAttribute('data-test')})")
                result.append({
                    "tag": tag,
                    "text": text,
                    "visible": visible,
                    "attrs": attrs,
                })
            except Exception:
                continue
        return result

    def record_page_state(self, output_path: Optional[str] = None) -> str:
        """记录页面状态到文件（发现模式）"""
        page = self.page
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        path = output_path or str(self.screenshot_dir / f"pagestate_{timestamp}.json")

        import json
        state = {
            "url": page.url,
            "title": page.title(),
            "interactive_elements": self.find_visible_elements(),
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        return path
