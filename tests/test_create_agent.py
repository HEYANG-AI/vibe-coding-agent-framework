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
    config_loader = None
    browser = None
    login_flow = None
    create_agent_flow = None

    def setup_method(self):
        logger.info("Setting up test environment...")
        self.config_loader = ConfigLoader()
        self.config_loader.load()
        self.browser = BrowserAdapter()
        self.login_flow = LoginFlow(self.browser)
        self.create_agent_flow = CreateAgentFlow(self.browser)
        logger.info("Test environment ready")

    def teardown_method(self):
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

        assert result["success"], f"Login failed: {result['message']}"

    def test_navigate_to_create_agent(self):
        try:
            navigate_result = self.create_agent_flow._navigate_to_create_agent()
            logger.info("Navigate to create agent executed")
        except Exception as e:
            logger.error(f"Navigate exception: {str(e)}")
            raise

    def test_create_simple_agent(self):
        agent_name = f"TestAgent_{int(time.time())}"

        create_result = self.create_agent_flow.execute(
            agent_name=agent_name,
            description="自动化测试创建的Agent",
            create_workflow=False
        )

        assert create_result.success, f"Create agent failed: {create_result.message}"

    def test_create_agent_with_workflow(self):
        agent_name = f"TestAgentWithWorkflow_{int(time.time())}"

        create_result = self.create_agent_flow.execute(
            agent_name=agent_name,
            description="自动化测试创建的工作流Agent",
            create_workflow=True
        )

        assert create_result.success, f"Create agent with workflow failed: {create_result.message}"


if __name__ == "__main__":
    import unittest
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCreateAgent)
    unittest.TextTestRunner(verbosity=2).run(suite)
