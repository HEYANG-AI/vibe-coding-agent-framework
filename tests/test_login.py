import os
import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.browser_adapter import BrowserAdapter
from core.tools import Logger, ConfigLoader
from flows.login_flow import LoginFlow

logger = Logger.setup("TestLogin")


class TestLogin:
    config_loader = None
    browser = None
    login_flow = None

    def setup_method(self):
        logger.info("Setting up test environment...")
        self.config_loader = ConfigLoader()
        self.config_loader.load()
        self.browser = BrowserAdapter()
        self.login_flow = LoginFlow(self.browser)
        logger.info("Test environment ready")

    def teardown_method(self):
        logger.info("Tearing down test environment...")
        if self.browser:
            self.browser.close()
        logger.info("Test environment closed")

    def test_navigate_to_platform(self):
        self.browser.init_driver()
        self.browser.navigate(self.config_loader.get('platform.base_url'))
        time.sleep(3)

        current_url = self.browser.get_current_url()
        base_url = self.config_loader.get('platform.base_url')
        assert base_url in current_url or 'aiagent' in current_url, \
            f"Navigation failed, current URL: {current_url}"
        logger.info(f"Successfully navigated to {current_url}")

    def test_login_page_elements(self):
        username_field = self.browser.driver.find_element("xpath", "//input[@type='text']")
        password_field = self.browser.driver.find_element("xpath", "//input[@type='password']")
        login_button = self.browser.driver.find_element("xpath", "//button[@type='submit']")

        assert username_field and password_field and login_button, \
            "Some login elements not found"
        logger.info("All login page elements found")

    def test_login_flow(self):
        login_result = self.login_flow.execute(
            username=self.config_loader.get_credential('username'),
            password=self.config_loader.get_credential('password'),
            use_session=False
        )

        assert login_result.success, f"Login failed: {login_result.message}"
        logger.info(f"Login test PASSED: {login_result.message}")


if __name__ == "__main__":
    import unittest
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLogin)
    unittest.TextTestRunner(verbosity=2).run(suite)
