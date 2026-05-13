"""
登录模块 - 自动登录目标平台
"""

from .browser import BrowserManager
from .config import get_config, DEFAULT_CONFIG, get_selector
from .learner import PageLearner
from typing import Optional


class LoginPage:
    """登录页面自动化"""

    def __init__(self, browser: BrowserManager):
        self.browser = browser
        self.learner = PageLearner()
        self.cfg = get_config()

    def login(self, username: Optional[str] = None, password: Optional[str] = None,
              headless: Optional[bool] = None) -> bool:
        """
        完整的登录流程。
        1. 导航到目标 URL
        2. 检测登录方式（表单/SSO/OTP）
        3. 自动填充登录
        4. 等待登录完成
        """
        username = username or self.cfg.get("username", "")
        password = password or self.cfg.get("password", "")

        if headless is not None:
            self.browser.headless = headless

        page = self.browser.start()
        self.browser.navigate()

        # 等待页面加载
        self.browser.wait_for_load()

        # 学习页面（首次运行）
        model = self.learner.load_model("login")
        if model:
            # 检测 UI 变化
            changes = self.learner.detect_ui_changes(page, model)
            if changes:
                model = self.learner.adapt_to_changes(page, model)
        else:
            model = self.learner.learn_page(page, "login")

        # 检测页面类型并自动适配
        page_type = self.learner._detect_page_type(page.url, page.title(), page)
        print(f"[登录] 检测到页面类型: {page_type}")
        print(f"[登录] 页面标题: {page.title()}")

        # 尝试检测 SSO 登录
        if self._is_sso_page(page):
            print("[登录] 检测到 SSO 登录页，尝试处理...")
            return self._handle_sso_login(page, username, password)

        # 检测是否已有登录表单
        if page.query_selector("input[type='password']"):
            print("[登录] 检测到登录表单，开始自动填写...")
            return self._fill_login_form(page, username, password)

        # 检测是否需要点击"登录"按钮先
        if self._click_login_button(page):
            self.browser.wait_for_load()
            if page.query_selector("input[type='password']"):
                return self._fill_login_form(page, username, password)

        # 检测是否已登录（跳转到 dashboard）
        current_url = page.url
        if "desktop" in current_url or "dashboard" in current_url or "index" in current_url:
            print("[登录] 检测到已登录状态，跳过登录流程")
            return True

        print(f"[登录] 无法识别登录界面，当前 URL: {current_url}")
        print("[登录] 进入手动等待模式（30秒内请手动完成登录）...")
        self._wait_for_manual_login(page)
        return True

    def _is_sso_page(self, page) -> bool:
        """检测是否为 SSO 登录页面"""
        sso_indicators = [
            "text=SSO", "text=企业登录", "text=统一认证",
            "text=单点登录", "[class*='sso']", "[class*='cas']",
            "text=企业微信", "text=钉钉", "text=飞书",
        ]
        for sel in sso_indicators:
            if page.query_selector(sel):
                return True

        url = page.url.lower()
        sso_keywords = ["sso", "cas", "oauth", "saml", "oidc", "connect"]
        return any(k in url for k in sso_keywords)

    def _handle_sso_login(self, page, username: str, password: str) -> bool:
        """处理 SSO 登录"""
        # 不同 SSO 系统的处理策略
        # 1. 直接 SSO 表单
        if page.query_selector("input[type='password']"):
            return self._fill_login_form(page, username, password)

        # 2. 点击 SSO 按钮跳转
        sso_btn = page.query_selector("button:has-text('SSO'), button:has-text('企业登录'), text=统一认证")
        if sso_btn:
            sso_btn.click()
            self.browser.wait_for_load()
            # 等待新页面加载
            self.browser.random_delay(2000, 4000)
            # 如果跳转到表单则填写
            if page.query_selector("input[type='password']"):
                return self._fill_login_form(page, username, password)
            # 如果跳转到企业微信扫码等
            print("[SSO] 检测到扫码登录，等待手动完成...")
            self._wait_for_manual_login(page)
            return True

        print("[SSO] 无法自动处理 SSO 登录，进入手动模式")
        self._wait_for_manual_login(page)
        return True

    def _fill_login_form(self, page, username: str, password: str) -> bool:
        """填写登录表单"""
        # 先学习页面获取准确选择器
        model = self.learner.load_model("login")
        if not model:
            model = self.learner.learn_page(page, "login")

        # 查找用户名输入框
        username_sel = self._find_input(page, ["用户", "账号", "用户名", "手机", "邮箱", "user", "account", "phone", "email"])
        if username_sel:
            print(f"[登录] 找到用户名输入框: {username_sel}")
            self.browser.human_type(username_sel, username)
            self.browser.random_delay()

        # 查找密码输入框
        password_sel = self._find_input(page, ["密码", "pass"], input_type="password")
        if password_sel:
            print(f"[登录] 找到密码输入框")
            self.browser.human_type(password_sel, password)
            self.browser.random_delay()

        # 处理验证码
        captcha_handled = self._handle_captcha(page)

        # 点击登录按钮
        login_btn = self._find_login_button(page)
        if login_btn:
            print(f"[登录] 点击登录按钮")
            page.click(login_btn)
            self.browser.random_delay(1000, 2000)

        # 等待登录完成（页面跳转）
        self.browser.wait_for_load()
        self.browser.random_delay(2000, 3000)

        # 检查登录结果
        current_url = page.url
        if "login" in current_url.lower() or page.query_selector("input[type='password']"):
            # 可能还需要 OTP
            if page.query_selector("input[placeholder*='验证码'], input[id*='otp'], input[placeholder*='OTP']"):
                print("[登录] 检测到 OTP 验证码输入框")
                return self._handle_otp(page)

            print("[登录] 登录可能失败，请检查用户名密码")
            return False

        print("[登录] 登录成功！")
        # 登录后学习 Dashboard
        self.learner.learn_page(page, "dashboard")
        return True

    def _find_input(self, page, keywords: list[str], input_type: Optional[str] = None) -> Optional[str]:
        """智能查找输入框，返回选择器"""
        # 策略1: 按 type 查找（密码框）
        if input_type == "password":
            handle = page.query_selector("input[type='password']")
            if handle:
                return "input[type='password']"

        # 策略2: 按 placeholder 关键词匹配
        for handle in page.query_selector_all("input, textarea"):
            try:
                placeholder = (handle.get_attribute("placeholder") or "").lower()
                for kw in keywords:
                    if kw.lower() in placeholder:
                        # 返回精准选择器
                        return handle.evaluate("""el => {
                            if (el.id) return '#' + el.id;
                            if (el.name) return el.tagName.toLowerCase() + '[name="' + el.name + '"]';
                            if (el.placeholder) return 'input[placeholder*="' + el.placeholder + '"]';
                            return 'input';
                        }""")
            except Exception:
                continue

        # 策略3: 按 name/ID/class 关键词匹配
        for handle in page.query_selector_all("input"):
            try:
                attrs = handle.evaluate("""el => ({
                    id: el.id,
                    name: el.name,
                    className: el.className,
                    type: el.type,
                })""")
                for kw in keywords:
                    if kw.lower() in attrs["id"].lower() or kw.lower() in attrs["name"].lower() or kw.lower() in attrs["className"].lower():
                        return handle.evaluate("el => el.id ? '#' + el.id : el.name ? 'input[name="' + el.name + '"]' : 'input.' + el.className.split(' ')[0]")
            except Exception:
                continue

        return None

    def _find_login_button(self, page) -> Optional[str]:
        """查找登录按钮"""
        # 策略1: 文本匹配（分开处理 CSS 和 Playwright 选择器）
        for text in ["登录", "登 录", "sign in", "Sign In", "LOGIN", "立即登录"]:
            # 先尝试 CSS 选择器
            btn = page.query_selector(f"button:has-text('{text}'), a:has-text('{text}')")
            if btn:
                return btn.evaluate("el => el.id ? '#' + el.id : el.tagName.toLowerCase() + ':has-text(\"'+ el.textContent.trim() +'\")'")
            
            # 再尝试 Playwright 文本选择器
            btn = page.locator(f"text='{text}'").first
            if btn.count() > 0:
                return f"text='{text}'"

        # 策略2: 表单提交按钮
        btn = page.query_selector("button[type='submit']")
        if btn:
            return "button[type='submit']"

        # 策略3: class 包含 login/btn
        for selector in [".login-btn", ".login-button", ".btn-login", "[class*='login'] button", ".el-button--primary"]:
            btn = page.query_selector(selector)
            if btn:
                return selector

        return None

    def _handle_captcha(self, page) -> bool:
        """处理验证码"""
        captcha_inputs = [
            "input[placeholder*='验证']",
            "input[placeholder*='captcha']",
            "input[id*='captcha']",
            "input[id*='验证']",
            "input[placeholder*='图片']",
        ]
        for sel in captcha_inputs:
            if page.query_selector(sel):
                print("[验证码] 检测到图片验证码，请在 30 秒内手动输入...")
                self._wait_for_manual_login(page, timeout=30000)
                return True

        return False

    def _handle_otp(self, page) -> bool:
        """处理 OTP 二次验证"""
        print("[OTP] 检测到二次验证，请在 60 秒内输入验证码...")
        self._wait_for_manual_login(page, timeout=60000)
        return True

    def _click_login_button(self, page) -> bool:
        """查找并点击页面上的登录入口按钮"""
        for text in ["登录", "去登录", "立即登录"]:
            btn = page.query_selector(f"text={text}, button:has-text('{text}')")
            if btn and btn.is_visible():
                btn.click()
                self.browser.random_delay(1000, 2000)
                return True
        return False

    def _wait_for_manual_login(self, page, timeout: int = 60000):
        """等待用户手动完成登录"""
        import time
        start = time.time()
        target_url = self.cfg.get("base_url", DEFAULT_CONFIG["base_url"])

        while time.time() - start < timeout / 1000:
            self.browser.random_delay(2000, 3000)
            current = page.url
            if "login" not in current.lower():
                print(f"[登录] 检测到页面跳转，已登录: {current}")
                return
            # 检测是否打开新页面
            for p in page.context.pages:
                if "login" not in p.url.lower():
                    print(f"[登录] 检测到新页面已登录: {p.url}")
                    return

        print("[登录] 手动等待超时")
