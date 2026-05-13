import os
import re
import time
import logging
import hashlib
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import yaml

logger = logging.getLogger(__name__)


@dataclass
class StepResult:
    step_name: str
    success: bool
    message: str = ""
    screenshot_path: Optional[str] = None
    data: Optional[Dict] = None
    error: Optional[str] = None
    duration: float = 0.0


class SensitiveDataFilter(logging.Filter):
    """自动脱敏敏感信息的日志过滤器"""
    def __init__(self, config_loader=None):
        super().__init__()
        self.config_loader = config_loader
        self._load_patterns()
    
    def _load_patterns(self):
        self.patterns = [
            r'password["\s:=]+[^\s"]+',
            r'pwd["\s:=]+[^\s"]+',
            r'secret["\s:=]+[^\s"]+',
            r'token["\s:=]+[^\s"]+',
            r'key["\s:=]+[^\s"]+',
            r'username["\s:=]+[^\s"]+',
            r'user["\s:=]+[^\s"]+',
            r'credential["\s:=]+[^\s"]+',
        ]
        
        # 从环境变量中获取用户名和密码，加入脱敏模式
        if self.config_loader:
            try:
                username_env = self.config_loader.get('security.username_env', 'AIRCHINA_USERNAME')
                password_env = self.config_loader.get('security.password_env', 'AIRCHINA_PASSWORD')
                username = os.environ.get(username_env)
                password = os.environ.get(password_env)
                
                if username:
                    # 对用户名进行部分脱敏
                    self.patterns.append(re.escape(username))
                if password:
                    self.patterns.append(re.escape(password))
            except Exception:
                pass
    
    def filter(self, record):
        record.msg = Logger.mask_sensitive(record.msg, self.patterns)
        return True


class Logger:
    @staticmethod
    def setup(name: str = "AirChinaAgent", level: int = logging.INFO, config_loader=None) -> logging.Logger:
        log_dir = Path("./logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        logger_instance = logging.getLogger(name)
        logger_instance.setLevel(level)

        if not logger_instance.handlers:
            fh = logging.FileHandler(log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
            fh.setLevel(level)

            ch = logging.StreamHandler()
            ch.setLevel(level)

            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)
            
            # 添加脱敏过滤器
            sensitive_filter = SensitiveDataFilter(config_loader)
            fh.addFilter(sensitive_filter)
            ch.addFilter(sensitive_filter)

            logger_instance.addHandler(fh)
            logger_instance.addHandler(ch)

        return logger_instance

    @staticmethod
    def mask_sensitive(text: str, patterns: Optional[List[str]] = None) -> str:
        if patterns is None:
            patterns = [
                r'password["\s:=]+[^\s"]+',
                r'pwd["\s:=]+[^\s"]+',
                r'secret["\s:=]+[^\s"]+',
                r'token["\s:=]+[^\s"]+',
                r'key["\s:=]+[^\s"]+',
            ]

        masked = text
        for pattern in patterns:
            masked = re.sub(pattern, '***REDACTED***', masked, flags=re.IGNORECASE)

        return masked


class ConfigLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._config: Dict = {}
        self._credentials: Dict = {}

    def load(self, config_path: Optional[str] = None) -> Dict:
        if not self._config:
            if config_path is None:
                config_path = Path(__file__).parent.parent / "config.yaml"

            if isinstance(config_path, str):
                config_path = Path(config_path)

            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}

        return self._config

    def load_credentials(self, cred_path: Optional[str] = None) -> Dict:
        if not self._credentials:
            # 优先从环境变量读取
            username_env = self.get('security.username_env', 'AIRCHINA_USERNAME')
            password_env = self.get('security.password_env', 'AIRCHINA_PASSWORD')
            
            username = os.environ.get(username_env)
            password = os.environ.get(password_env)
            
            if username and password:
                self._credentials = {
                    'username': username,
                    'password': password
                }
                logger.info("Credentials loaded from environment variables")
            else:
                # 环境变量不存在时，尝试从文件读取（向后兼容）
                if cred_path is None:
                    cred_path = Path(__file__).parent.parent / "credentials.yaml"

                if isinstance(cred_path, str):
                    cred_path = Path(cred_path)

                if cred_path.exists():
                    with open(cred_path, 'r', encoding='utf-8') as f:
                        self._credentials = yaml.safe_load(f) or {}
                    logger.info("Credentials loaded from credentials.yaml")
                else:
                    logger.warning("No credentials found in environment variables or file")

        return self._credentials

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def get_credential(self, key: str, default: Any = None) -> Any:
        return self._credentials.get(key, default)


class SessionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._session_data: Dict = {}
        self._session_file = Path(__file__).parent.parent / "session.json"

    def save_session(self, key: str, value: Any):
        self._session_data[key] = value
        self._persist_session()

    def get_session(self, key: str) -> Optional[Any]:
        if not self._session_data and self._session_file.exists():
            self._load_session()
        return self._session_data.get(key)

    def clear_session(self):
        self._session_data.clear()
        if self._session_file.exists():
            self._session_file.unlink()

    def _persist_session(self):
        import json
        try:
            with open(self._session_file, 'w', encoding='utf-8') as f:
                json.dump(self._session_data, f)
        except Exception as e:
            logger.warning(f"Failed to persist session: {e}")

    def _load_session(self):
        import json
        try:
            if self._session_file.exists():
                with open(self._session_file, 'r', encoding='utf-8') as f:
                    self._session_data = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load session: {e}")


class ScreenshotManager:
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent / "logs" / "screenshots"
        else:
            base_dir = Path(base_dir)

        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def capture(self, driver, name: str, full_page: bool = False) -> Optional[str]:
        try:
            filename = f"{name}_{int(time.time())}.png"
            filepath = self.base_dir / filename
            driver.save_screenshot(str(filepath))
            logger.info(f"Screenshot captured: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return None

    def capture_element(self, driver, element, name: str) -> Optional[str]:
        try:
            filename = f"{name}_element_{int(time.time())}.png"
            filepath = self.base_dir / filename
            element.screenshot(str(filepath))
            logger.info(f"Element screenshot captured: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.warning(f"Failed to capture element screenshot: {e}")
            return None


class AssertHelper:
    @staticmethod
    def assert_element_visible(element, message: str = "Element not visible"):
        try:
            assert element.is_displayed(), message
        except AssertionError as e:
            logger.error(f"Assertion failed: {message}")
            raise

    @staticmethod
    def assert_element_enabled(element, message: str = "Element not enabled"):
        try:
            assert element.is_enabled(), message
        except AssertionError as e:
            logger.error(f"Assertion failed: {message}")
            raise

    @staticmethod
    def assert_text_contains(element, expected_text: str, message: str = ""):
        try:
            actual_text = element.text
            assert expected_text in actual_text, message or f"Text '{expected_text}' not found in '{actual_text}'"
        except AssertionError as e:
            logger.error(f"Assertion failed: {message or str(e)}")
            raise

    @staticmethod
    def assert_url_contains(driver, expected: str, message: str = ""):
        try:
            current_url = driver.current_url
            assert expected in current_url, message or f"URL '{expected}' not found in '{current_url}'"
        except AssertionError as e:
            logger.error(f"Assertion failed: {message or str(e)}")
            raise

    @staticmethod
    def assert_title_contains(driver, expected: str, message: str = ""):
        try:
            title = driver.title
            assert expected in title, message or f"Title '{expected}' not found in '{title}'"
        except AssertionError as e:
            logger.error(f"Assertion failed: {message or str(e)}")
            raise


class StepExecutor:
    def __init__(self, browser, screenshot_manager: Optional[ScreenshotManager] = None):
        self.browser = browser
        self.screenshot_manager = screenshot_manager or ScreenshotManager()
        self._steps: List[StepResult] = []

    def execute_step(self, step_name: str, action: Callable, *args, **kwargs) -> StepResult:
        start_time = time.time()
        result = StepResult(step_name=step_name, success=False)

        try:
            logger.info(f"Executing step: {step_name}")
            return_value = action(*args, **kwargs)
            result.success = True
            result.message = "Step completed successfully"
            result.data = {'return_value': return_value}
            logger.info(f"Step '{step_name}' completed successfully")

        except Exception as e:
            result.success = False
            result.error = str(e)
            result.message = f"Step failed: {e}"
            logger.error(f"Step '{step_name}' failed: {e}")

            screenshot = self.screenshot_manager.capture(
                self.browser.driver,
                f"step_failure_{step_name.replace(' ', '_')}"
            )
            result.screenshot_path = screenshot

        finally:
            result.duration = time.time() - start_time
            self._steps.append(result)

        return result

    def get_results(self) -> List[StepResult]:
        return self._steps

    def get_summary(self) -> Dict:
        total = len(self._steps)
        passed = sum(1 for s in self._steps if s.success)
        failed = total - passed

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
            'steps': self._steps
        }


class Tools:
    @staticmethod
    def wait_for(condition: Callable, timeout: int = 10, poll_interval: float = 0.5) -> bool:
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if condition():
                    return True
            except:
                pass
            time.sleep(poll_interval)
        return False

    @staticmethod
    def wait_for_element(driver, locator: str, timeout: int = 10) -> bool:
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By

        try:
            wait = WebDriverWait(driver, timeout)
            wait.until(EC.presence_of_element_located((By.XPATH, locator)))
            return True
        except:
            return False

    @staticmethod
    def sleep(seconds: float):
        time.sleep(seconds)

    @staticmethod
    def generate_id(prefix: str = "") -> str:
        timestamp = int(time.time() * 1000)
        return f"{prefix}{timestamp}" if prefix else str(timestamp)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        return re.sub(r'[^\w\s-]', '', filename).strip().lower().replace(' ', '_')

    @staticmethod
    def hash_text(text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    @staticmethod
    def parse_natural_language(task: str) -> Dict[str, Any]:
        task_lower = task.lower()

        intent = "unknown"
        entities = {}

        if any(word in task_lower for word in ['登录', '登陆', '登录系统']):
            intent = "login"
            import re
            username_match = re.search(r'用户名[是为]*(.+)', task)
            password_match = re.search(r'密码[是为]*(.+)', task)
            if username_match:
                entities['username'] = username_match.group(1).strip()
            if password_match:
                entities['password'] = password_match.group(1).strip()

        elif any(word in task_lower for word in ['创建', '新建', '新建agent', '创建agent']):
            intent = "create_agent"
            import re
            name_match = re.search(r'(?:名称|名字|叫)[是为]*(.+)', task)
            if name_match:
                entities['agent_name'] = name_match.group(1).strip()

        elif any(word in task_lower for word in ['发布', '发布agent', '上线']):
            intent = "publish"

        elif any(word in task_lower for word in ['工作流', '流程', '画布']):
            intent = "workflow"

        elif any(word in task_lower for word in ['完整流程', '全部流程', '执行']):
            intent = "full_flow"

        return {
            'intent': intent,
            'entities': entities,
            'original_task': task
        }
