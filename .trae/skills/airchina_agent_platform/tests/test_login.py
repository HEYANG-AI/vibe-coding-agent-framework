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
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.config_loader.load()
        self.browser = None
        self.login_flow = None
        self.results = []

    def setup(self):
        logger.info("Setting up test environment...")
        self.browser = BrowserAdapter()
        self.login_flow = LoginFlow(self.browser)
        logger.info("Test environment ready")

    def teardown(self):
        logger.info("Tearing down test environment...")
        if self.browser:
            self.browser.close()
        logger.info("Test environment closed")

    def test_navigate_to_platform(self):
        result = {"name": "test_navigate_to_platform", "success": False, "message": ""}

        try:
            self.browser.init_driver()
            self.browser.navigate(self.config_loader.get('platform.base_url'))
            time.sleep(3)

            current_url = self.browser.get_current_url()
            base_url = self.config_loader.get('platform.base_url')
            if base_url in current_url or 'aiagent' in current_url:
                result["success"] = True
                result["message"] = f"Successfully navigated to {current_url}"
                logger.info(result["message"])
            else:
                result["message"] = f"Navigation failed, current URL: {current_url}"
                logger.error(result["message"])

        except Exception as e:
            result["message"] = f"Navigation exception: {str(e)}"
            logger.error(result["message"])

        self.results.append(result)
        return result

    def test_login_page_elements(self):
        result = {"name": "test_login_page_elements", "success": False, "message": ""}

        try:
            username_field = self.browser.driver.find_element("xpath", "//input[@type='text']")
            password_field = self.browser.driver.find_element("xpath", "//input[@type='password']")
            login_button = self.browser.driver.find_element("xpath", "//button[@type='submit']")

            if username_field and password_field and login_button:
                result["success"] = True
                result["message"] = "All login page elements found"
                logger.info(result["message"])
            else:
                result["message"] = "Some login elements not found"
                logger.warning(result["message"])

        except Exception as e:
            result["message"] = f"Login elements test exception: {str(e)}"
            logger.error(result["message"])

        self.results.append(result)
        return result

    def test_login_flow(self):
        result = {"name": "test_login_flow", "success": False, "message": ""}

        try:
            login_result = self.login_flow.execute(
                username=self.config_loader.get_credential('username'),
                password=self.config_loader.get_credential('password'),
                use_session=False
            )

            result["success"] = login_result.success
            result["message"] = login_result.message

            if login_result.screenshot_path:
                result["screenshot"] = login_result.screenshot_path

            if login_result.success:
                logger.info(f"Login test PASSED: {login_result.message}")
            else:
                logger.error(f"Login test FAILED: {login_result.message}")

        except Exception as e:
            result["message"] = f"Login flow exception: {str(e)}"
            logger.error(result["message"])

        self.results.append(result)
        return result

    def run_all_tests(self):
        logger.info("=" * 60)
        logger.info("Starting Login Tests")
        logger.info("=" * 60)

        self.setup()

        try:
            self.test_navigate_to_platform()
            self.test_login_page_elements()
            self.test_login_flow()

        finally:
            self.teardown()

        logger.info("=" * 60)
        logger.info("Login Tests Completed")
        logger.info("=" * 60)

        passed = sum(1 for r in self.results if r["success"])
        failed = len(self.results) - passed

        logger.info(f"Results: {passed} passed, {failed} failed")

        return {
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "results": self.results
        }


if __name__ == "__main__":
    test = TestLogin()
    report = test.run_all_tests()
    print("\n" + "=" * 60)
    print("TEST REPORT")
    print("=" * 60)
    print(f"Total: {report['total']}")
    print(f"Passed: {report['passed']}")
    print(f"Failed: {report['failed']}")
    for r in report['results']:
        status = "PASS" if r['success'] else "FAIL"
        print(f"  [{status}] {r['name']}: {r['message']}")
