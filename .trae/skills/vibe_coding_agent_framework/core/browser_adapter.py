import os
import sys
import platform
import time
import logging
import re
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import yaml

logger = logging.getLogger(__name__)


@dataclass
class Locator:
    loc_type: str
    value: str
    description: str = ""
    priority: int = 0
    last_verified: Optional[str] = None

    def __str__(self):
        return f"{self.loc_type}={self.value}"


@dataclass
class PageElement:
    name: str
    locators: List[Locator] = field(default_factory=list)
    element_type: str = "unknown"
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    learned_at: Optional[str] = None
    hit_count: int = 0


class BrowserAdapter:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.config = self._load_config(config_path)
        self.driver = None
        self.platform_name = platform.system()
        self._element_cache: Dict[str, PageElement] = {}
        self._session_active = False

        logger.info(f"BrowserAdapter initialized on {self.platform_name}")

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"

        if isinstance(config_path, str):
            config_path = Path(config_path)

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def _get_chrome_options(self) -> List[str]:
        options = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            f'--window-size={self.config.get("browser", {}).get("window_size", [1920, 1080]).__str__().replace(",", "x")}'
        ]

        if self.platform_name == 'Darwin':
            pass
        elif self.platform_name == 'Windows':
            options.append('--disable-gpu')

        browser_config = self.config.get('browser', {})
        if not browser_config.get('headless', False):
            options.remove('--no-sandbox')

        user_data_dir = browser_config.get('user_data_dir')
        if user_data_dir:
            options.append(f'--user-data-dir={user_data_dir}')

        return options

    def _get_firefox_options(self) -> List[str]:
        options = []
        if self.platform_name == 'Darwin':
            pass
        return options

    def init_driver(self, browser_type: Optional[str] = None) -> Any:
        if browser_type is None:
            browser_type = self.config.get('browser', {}).get('type', 'chrome')

        browser_type = browser_type.lower()

        try:
            if browser_type == 'chrome':
                from selenium import webdriver
                from selenium.webdriver.chrome.service import Service
                from selenium.webdriver.chrome.options import Options

                options = Options()
                for opt in self._get_chrome_options():
                    options.add_argument(opt)

                self.driver = webdriver.Chrome(options=options)
                logger.info("Chrome driver initialized successfully")

            elif browser_type == 'firefox':
                from selenium import webdriver
                from selenium.webdriver.firefox.options import Options

                options = Options()
                for opt in self._get_firefox_options():
                    options.add_argument(opt)

                self.driver = webdriver.Firefox(options=options)
                logger.info("Firefox driver initialized successfully")

            elif browser_type == 'edge':
                from selenium import webdriver
                from selenium.webdriver.edge.options import Options

                options = Options()
                self.driver = webdriver.Edge(options=options)
                logger.info("Edge driver initialized successfully")

            else:
                raise ValueError(f"Unsupported browser type: {browser_type}")

            self._set_implicit_wait()
            return self.driver

        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
            raise

    def _set_implicit_wait(self):
        wait_time = self.config.get('wait', {}).get('implicit', 10)
        self.driver.implicitly_wait(wait_time)

    def smart_wait(self, condition: str, timeout: Optional[int] = None) -> bool:
        if timeout is None:
            timeout = self.config.get('wait', {}).get('explicit', 15)

        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        try:
            wait = WebDriverWait(self.driver, timeout)
            condition_map = {
                'element_clickable': EC.element_to_be_clickable,
                'element_visible': EC.visibility_of_element_located,
                'element_present': EC.presence_of_element_located,
                'frame_available': EC.frame_to_be_available_and_switch_to_it,
            }

            if condition in condition_map:
                wait.until(condition_map[condition])
            return True
        except:
            return False

    def find_element(self, locators: List[Locator], take_screenshot: bool = True) -> Optional[Any]:
        last_exception = None

        for locator in sorted(locators, key=lambda x: x.priority, reverse=True):
            try:
                element = self._find_by_locator(locator)
                if element and self._is_element_valid(element):
                    locator.last_verified = time.strftime('%Y-%m-%d %H:%M:%S')
                    self._element_cache[locator.value] = element
                    return element
            except Exception as e:
                last_exception = e
                continue

        if take_screenshot:
            self.take_screenshot(f"find_element_failed_{int(time.time())}")

        logger.warning(f"All locators failed. Last error: {last_exception}")
        return None

    def _find_by_locator(self, locator: Locator) -> Any:
        from selenium.webdriver.common.by import By

        by_map = {
            'xpath': By.XPATH,
            'css': By.CSS_SELECTOR,
            'id': By.ID,
            'name': By.NAME,
            'class': By.CLASS_NAME,
            'tag': By.TAG_NAME,
            'link_text': By.LINK_TEXT,
            'partial_link_text': By.PARTIAL_LINK_TEXT,
        }

        by = by_map.get(locator.loc_type.lower(), By.XPATH)
        return self.driver.find_element(by, locator.value)

    def _is_element_valid(self, element) -> bool:
        try:
            return element.is_displayed() and element.is_enabled()
        except:
            return False

    def click(self, element: Any, retry: int = 3) -> bool:
        for attempt in range(retry):
            try:
                element.click()
                return True
            except Exception as e:
                logger.warning(f"Click attempt {attempt + 1} failed: {e}")
                time.sleep(1)
        return False

    def input_text(self, element: Any, text: str, clear_first: bool = True, retry: int = 3) -> bool:
        for attempt in range(retry):
            try:
                if clear_first:
                    element.clear()
                element.send_keys(text)
                return True
            except Exception as e:
                logger.warning(f"Input text attempt {attempt + 1} failed: {e}")
                time.sleep(1)
        return False

    def take_screenshot(self, name: str, full_page: bool = False) -> Optional[str]:
        screenshot_dir = Path(self.config.get('platform', {}).get('screenshot_dir', './logs/screenshots'))
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{name}_{int(time.time())}.png"
        filepath = screenshot_dir / filename

        try:
            self.driver.save_screenshot(str(filepath))
            logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None

    def _is_domain_allowed(self, url: str) -> bool:
        allowed_domains = self.config.get('security', {}).get('allowed_domains', [])
        if not allowed_domains:
            return True
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            
            for allowed in allowed_domains:
                if allowed in domain:
                    return True
            logger.warning(f"Attempt to navigate to restricted domain: {domain}")
            return False
        except Exception as e:
            logger.warning(f"Domain check failed: {e}")
            return False

    def navigate(self, url: str) -> bool:
        if not self._is_domain_allowed(url):
            logger.error(f"Navigation blocked for security reasons: {url}")
            return False
            
        try:
            self.driver.get(url)
            logger.info(f"Navigated to: {url}")
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False

    def get_current_url(self) -> str:
        return self.driver.current_url if self.driver else ""

    def get_page_source(self) -> str:
        return self.driver.page_source if self.driver else ""

    def execute_script(self, script: str, *args) -> Any:
        return self.driver.execute_script(script, *args) if self.driver else None

    def switch_to_frame(self, frame_reference: Any) -> bool:
        try:
            self.driver.switch_to.frame(frame_reference)
            return True
        except Exception as e:
            logger.error(f"Frame switch failed: {e}")
            return False

    def switch_to_default_content(self) -> bool:
        try:
            self.driver.switch_to.default_content()
            return True
        except:
            return False

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser driver closed")
            except:
                pass
            finally:
                self.driver = None

    def is_session_active(self) -> bool:
        return self._session_active

    def set_session_active(self, active: bool):
        self._session_active = active

    def get_element_locator(self, element: Any) -> Optional[str]:
        try:
            return element.get_attribute('data-testid') or \
                   element.get_attribute('id') or \
                   element.get_attribute('name') or \
                   element.tag_name
        except:
            return None

    def add_to_cache(self, name: str, element: PageElement):
        self._element_cache[name] = element

    def get_from_cache(self, name: str) -> Optional[PageElement]:
        return self._element_cache.get(name)

    def clear_cache(self):
        self._element_cache.clear()


class PlatformEnvironment:
    ENV_TEST = "test"
    ENV_PROD = "production"

    @staticmethod
    def detect(url: str) -> str:
        if "test" in url.lower():
            return PlatformEnvironment.ENV_TEST
        return PlatformEnvironment.ENV_PROD


class SemanticLocator:
    @staticmethod
    def build_xpath(text: str, exact: bool = True) -> str:
        if exact:
            return f"//*[contains(text(), '{text}')]"
        return f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"

    @staticmethod
    def build_aria_label(label: str) -> str:
        return f"//*[@aria-label='{label}']"

    @staticmethod
    def build_role(role: str) -> str:
        return f"//*[@role='{role}']"

    @staticmethod
    def build_text_and_tag(tag: str, text: str) -> str:
        return f"//{tag}[contains(text(), '{text}')]"
