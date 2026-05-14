import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from core.browser_adapter import BrowserAdapter, Locator
from core.learning_engine import LearningEngine
from core.self_healing import SelfHealingEngine
from core.tools import Tools, ConfigLoader, StepExecutor, ScreenshotManager

logger = logging.getLogger(__name__)


@dataclass
class LoginResult:
    success: bool
    message: str
    screenshot_path: Optional[str] = None
    session_maintained: bool = False


class LoginFlow:
    def __init__(self, browser: Optional[BrowserAdapter] = None,
                 config_path: Optional[str] = None):
        self.config_loader = ConfigLoader()
        self.config_loader.load(config_path)

        self.browser = browser or BrowserAdapter(config_path)
        self.learning = LearningEngine(self.browser, config_path)
        self.healing = SelfHealingEngine(self.browser, self.config_loader)
        self.screenshot_mgr = ScreenshotManager()
        self.step_executor = StepExecutor(self.browser, self.screenshot_mgr)
        self.tools = Tools()

        self.platform_url = self.config_loader.get('platform.base_url')

        self._username_input_locators = [
            Locator(loc_type='xpath', value="//input[@type='text' and not(@type='hidden')]", description="Username input field", priority=80),
            Locator(loc_type='xpath', value="//input[@name='username']", description="Username by name", priority=90),
            Locator(loc_type='xpath', value="//input[contains(@placeholder, '用户')]", description="Username by placeholder", priority=70),
            Locator(loc_type='xpath', value="//input[contains(@placeholder, '账号')]", description="Username by placeholder", priority=70),
            Locator(loc_type='xpath', value="//input[contains(@id, 'username')]", description="Username by id", priority=85),
        ]

        self._password_input_locators = [
            Locator(loc_type='xpath', value="//input[@type='password']", description="Password input field", priority=80),
            Locator(loc_type='xpath', value="//input[@name='password']", description="Password by name", priority=90),
            Locator(loc_type='xpath', value="//input[contains(@placeholder, '密码')]", description="Password by placeholder", priority=70),
            Locator(loc_type='xpath', value="//input[contains(@id, 'password')]", description="Password by id", priority=85),
        ]

        self._login_button_locators = [
            Locator(loc_type='xpath', value="//button[@type='submit']", description="Submit button", priority=80),
            Locator(loc_type='xpath', value="//button[contains(text(), '登录')]", description="Login button by text", priority=90),
            Locator(loc_type='xpath', value="//button[contains(text(), '登陆')]", description="Login button by text", priority=90),
            Locator(loc_type='xpath', value="//button[contains(@class, 'login')]", description="Login button by class", priority=70),
            Locator(loc_type='xpath', value="//*[contains(@class, 'btn') and contains(text(), '登录')]", description="Login button by class and text", priority=85),
        ]

        logger.info("LoginFlow initialized")

    def execute(self, username: Optional[str] = None, password: Optional[str] = None,
                use_session: bool = True) -> LoginResult:
        logger.info("=" * 60)
        logger.info("Starting login flow")
        logger.info("=" * 60)

        if use_session:
            session_maintained = self._check_existing_session()
            if session_maintained:
                logger.info("Session maintained, login successful")
                return LoginResult(
                    success=True,
                    message="Session maintained, already logged in",
                    session_maintained=True
                )

        if not username:
            username = self._get_username()
        if not password:
            password = self._get_password()

        if not username or not password:
            return LoginResult(
                success=False,
                message="Username or password not provided and not found in config"
            )

        try:
            self.step_executor.execute_step(
                "Navigate to platform",
                self._navigate_to_login_page
            )

            self.step_executor.execute_step(
                "Enter username",
                self._enter_username,
                username
            )

            self.step_executor.execute_step(
                "Enter password",
                self._enter_password,
                password
            )

            self.step_executor.execute_step(
                "Click login button",
                self._click_login_button
            )

            self.step_executor.execute_step(
                "Verify login success",
                self._verify_login_success
            )

            summary = self.step_executor.get_summary()

            if summary['failed'] > 0:
                failed_steps = [s for s in summary['steps'] if not s.success]
                logger.error(f"Login failed. {summary['failed']} step(s) failed:")
                for step in failed_steps:
                    logger.error(f"  - {step.step_name}: {step.error}")

                return LoginResult(
                    success=False,
                    message=f"Login failed: {failed_steps[0].error if failed_steps else 'Unknown error'}",
                    screenshot_path=failed_steps[0].screenshot_path if failed_steps else None
                )

            self.browser.set_session_active(True)
            logger.info("Login completed successfully")

            return LoginResult(
                success=True,
                message="Login successful",
                session_maintained=False
            )

        except Exception as e:
            logger.error(f"Login flow exception: {e}")
            screenshot = self.screenshot_mgr.capture(self.browser.driver, "login_exception")
            return LoginResult(
                success=False,
                message=f"Login exception: {str(e)}",
                screenshot_path=screenshot
            )

    def _check_existing_session(self) -> bool:
        try:
            if not self.browser.driver:
                return False

            current_url = self.browser.get_current_url()

            if self.platform_url and self.platform_url in current_url:
                page_source = self.browser.get_page_source().lower()
                if any(word in page_source for word in ['登录', '登陆', 'login']):
                    return False
                return True

            self.browser.navigate(self.platform_url)
            time.sleep(2)

            page_source = self.browser.get_page_source().lower()
            if any(word in page_source for word in ['登录', '登陆', 'login']):
                return False

            return True

        except Exception as e:
            logger.warning(f"Session check failed: {e}")
            return False

    def _get_username(self) -> Optional[str]:
        username = self.config_loader.get_credential('username')
        if not username:
            username = self.config_loader.get_credential('username')
        return username

    def _get_password(self) -> Optional[str]:
        password = self.config_loader.get_credential('password')
        if not password:
            password = self.config_loader.get_credential('password')
        return password

    def _navigate_to_login_page(self):
        if not self.browser.driver:
            self.browser.init_driver()

        logger.info(f"Navigating to {self.platform_url}")
        self.browser.navigate(self.platform_url)
        time.sleep(3)

        self.browser.take_screenshot("login_page_loaded")

        if self.config_loader.get('learning.enabled', True):
            logger.info("Learning login page structure...")
            self.learning.learn_current_page("login_page")

    def _enter_username(self, username: str):
        logger.info(f"Entering username: {self._mask_text(username)}")

        element = self._find_element_with_healing("username", self._username_input_locators)

        if not element:
            raise Exception("Username input element not found and could not be healed")

        self.browser.input_text(element, username)
        logger.info("Username entered successfully")

    def _enter_password(self, password: str):
        logger.info("Entering password")

        element = self._find_element_with_healing("password", self._password_input_locators)

        if not element:
            raise Exception("Password input element not found and could not be healed")

        self.browser.input_text(element, password)
        logger.info("Password entered successfully")

    def _click_login_button(self):
        logger.info("Clicking login button")

        element = self._find_element_with_healing("login_button", self._login_button_locators)

        if not element:
            raise Exception("Login button not found and could not be healed")

        self.browser.click(element)
        logger.info("Login button clicked")

        time.sleep(3)

    def _verify_login_success(self):
        logger.info("Verifying login success")

        time.sleep(5)

        current_url = self.browser.get_current_url()

        if any(word in current_url for word in ['login', 'signin', '登录', '登陆']):
            page_source = self.browser.get_page_source().lower()
            if any(word in page_source for word in ['登录', '登陆', 'login', 'error', '失败', '错误']):
                screenshot = self.screenshot_mgr.capture(self.browser.driver, "login_verification_failed")
                raise Exception(f"Login appears to have failed. URL: {current_url}")

        self.browser.take_screenshot("login_success")

        logger.info("Login verified successfully")

    def _find_element_with_healing(self, element_name: str,
                                   locators: list) -> Optional[Any]:
        for locator in locators:
            try:
                element = self.browser.driver.find_element(locator.loc_type, locator.value)
                if element and self.browser._is_element_valid(element):
                    logger.info(f"Found {element_name} with locator: {locator}")
                    return element
            except:
                continue

        logger.warning(f"Standard locators failed for {element_name}, attempting self-healing...")

        healing_result = self.healing.heal_element(element_name, locators)

        if healing_result.success and healing_result.element:
            logger.info(f"Self-healing successful for {element_name}")
            return healing_result.element

        logger.error(f"All methods failed to find {element_name}")
        return None

    def _mask_text(self, text: str) -> str:
        if len(text) <= 4:
            return "***"
        return text[:2] + "***" + text[-2:]

    def get_step_results(self):
        return self.step_executor.get_results()

    def get_summary(self):
        return self.step_executor.get_summary()


class NaturalLanguageLogin:
    def __init__(self, login_flow: LoginFlow):
        self.login_flow = login_flow
        self.tools = Tools()

    def execute(self, task: str) -> LoginResult:
        parsed = self.tools.parse_natural_language(task)

        if parsed['intent'] != 'login':
            return LoginResult(
                success=False,
                message=f"Task '{task}' is not a login task"
            )

        entities = parsed['entities']
        username = entities.get('username')
        password = entities.get('password')

        return self.login_flow.execute(username=username, password=password)


def run_skill(task: str, config_path: Optional[str] = None) -> LoginResult:
    browser = BrowserAdapter(config_path)
    login_flow = LoginFlow(browser, config_path)
    nl_login = NaturalLanguageLogin(login_flow)

    return nl_login.execute(task)
