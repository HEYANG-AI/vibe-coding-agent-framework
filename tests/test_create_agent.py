import os
import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.browser_adapter import BrowserAdapter
from core.tools import Logger, ConfigLoader
from flows.login_flow import LoginFlow
from flows.create_agent_flow import CreateAgentFlow

logger = Logger.setup("TestCreateAgent")


class TestCreateAgent:
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.config_loader.load()
        self.browser = None
        self.login_flow = None
        self.create_agent_flow = None
        self.results = []

    def setup(self):
        logger.info("Setting up test environment...")
        self.browser = BrowserAdapter()
        self.login_flow = LoginFlow(self.browser)
        self.create_agent_flow = CreateAgentFlow(self.browser)
        logger.info("Test environment ready")

    def teardown(self):
        logger.info("Tearing down test environment...")
        if self.browser:
            self.browser.close()
        logger.info("Test environment closed")

    def test_login_required(self):
        result = {"name": "test_login_required", "success": False, "message": ""}

        try:
            login_result = self.login_flow.execute(
                username=self.config_loader.get_credential('username'),
                password=self.config_loader.get_credential('password'),
                use_session=True
            )

            result["success"] = login_result.success
            result["message"] = login_result.message

            if login_result.success:
                logger.info("Login successful for create agent test")
            else:
                logger.error(f"Login failed: {login_result.message}")

        except Exception as e:
            result["message"] = f"Login exception: {str(e)}"
            logger.error(result["message"])

        self.results.append(result)
        return result

    def test_navigate_to_create_agent(self):
        result = {"name": "test_navigate_to_create_agent", "success": False, "message": ""}

        try:
            navigate_result = self.create_agent_flow._navigate_to_create_agent()
            result["success"] = True
            result["message"] = "Navigate to create agent executed"
            logger.info(result["message"])

        except Exception as e:
            result["message"] = f"Navigate exception: {str(e)}"
            logger.error(result["message"])

        self.results.append(result)
        return result

    def test_create_simple_agent(self):
        result = {"name": "test_create_simple_agent", "success": False, "message": ""}

        try:
            agent_name = f"TestAgent_{int(time.time())}"

            create_result = self.create_agent_flow.execute(
                agent_name=agent_name,
                description="自动化测试创建的Agent",
                create_workflow=False
            )

            result["success"] = create_result.success
            result["message"] = create_result.message
            result["agent_name"] = agent_name

            if create_result.screenshot_path:
                result["screenshot"] = create_result.screenshot_path

            if create_result.success:
                logger.info(f"Create agent test PASSED: {agent_name}")
            else:
                logger.error(f"Create agent test FAILED: {create_result.message}")

        except Exception as e:
            result["message"] = f"Create agent exception: {str(e)}"
            logger.error(result["message"])

        self.results.append(result)
        return result

    def test_create_agent_with_workflow(self):
        result = {"name": "test_create_agent_with_workflow", "success": False, "message": ""}

        try:
            agent_name = f"TestAgentWithWorkflow_{int(time.time())}"

            create_result = self.create_agent_flow.execute(
                agent_name=agent_name,
                description="自动化测试创建的工作流Agent",
                create_workflow=True
            )

            result["success"] = create_result.success
            result["message"] = create_result.message
            result["agent_name"] = agent_name

            if create_result.screenshot_path:
                result["screenshot"] = create_result.screenshot_path

            if create_result.success:
                logger.info(f"Create agent with workflow test PASSED: {agent_name}")
            else:
                logger.error(f"Create agent with workflow test FAILED: {create_result.message}")

        except Exception as e:
            result["message"] = f"Create agent with workflow exception: {str(e)}"
            logger.error(result["message"])

        self.results.append(result)
        return result

    def run_all_tests(self):
        logger.info("=" * 60)
        logger.info("Starting Create Agent Tests")
        logger.info("=" * 60)

        self.setup()

        try:
            self.test_login_required()
            self.test_navigate_to_create_agent()
            self.test_create_simple_agent()
            self.test_create_agent_with_workflow()

        finally:
            self.teardown()

        logger.info("=" * 60)
        logger.info("Create Agent Tests Completed")
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
    test = TestCreateAgent()
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
