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
from flows.publish_flow import PublishFlow

logger = Logger.setup("TestFullFlow")


class TestFullFlow:
    config_loader = None
    browser = None
    login_flow = None
    create_agent_flow = None
    publish_flow = None
    agent_name = None

    def setup_method(self):
        logger.info("Setting up test environment...")
        self.config_loader = ConfigLoader()
        self.config_loader.load()
        self.browser = BrowserAdapter()
        self.login_flow = LoginFlow(self.browser)
        self.create_agent_flow = CreateAgentFlow(self.browser)
        self.publish_flow = PublishFlow(self.browser)
        logger.info("Test environment ready")

    def teardown_method(self):
        logger.info("Tearing down test environment...")
        if self.browser:
            self.browser.close()
        logger.info("Test environment closed")

    def test_full_flow(self):
        logger.info("=" * 60)
        logger.info("Starting Full Flow Test")
        logger.info("=" * 60)

        login_result = self.login_flow.execute(
            username=self.config_loader.get_credential('username'),
            password=self.config_loader.get_credential('password'),
            use_session=True
        )
        assert login_result.success, f"Login failed: {login_result.message}"
        logger.info(f"Login PASSED: {login_result.message}")

        self.agent_name = f"FullFlowAgent_{int(time.time())}"
        create_result = self.create_agent_flow.execute(
            agent_name=self.agent_name,
            description="完整流程测试创建的Agent",
            create_workflow=True
        )
        assert create_result.success, f"Create agent failed: {create_result.message}"
        logger.info(f"Create Agent PASSED: {self.agent_name}")

        publish_result = self.publish_flow.execute(agent_name=self.agent_name)
        assert publish_result.success, f"Publish failed: {publish_result.message}"
        logger.info(f"Publish PASSED: {publish_result.message}")

        logger.info(f"Full flow completed successfully for agent: {self.agent_name}")


class NaturalLanguageDriver:
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.config_loader.load()
        self.browser = None
        self.login_flow = None
        self.create_agent_flow = None
        self.publish_flow = None

    def initialize(self):
        logger.info("Initializing Natural Language Driver...")
        self.browser = BrowserAdapter()
        self.login_flow = LoginFlow(self.browser)
        self.create_agent_flow = CreateAgentFlow(self.browser)
        self.publish_flow = PublishFlow(self.browser)
        logger.info("Natural Language Driver initialized")

    def execute_natural_language_task(self, task: str):
        logger.info(f"Received task: {task}")

        from core.tools import Tools
        tools = Tools()
        parsed = tools.parse_natural_language(task)

        logger.info(f"Parsed intent: {parsed['intent']}")
        logger.info(f"Entities: {parsed['entities']}")

        if parsed['intent'] == 'login':
            return self.login_flow.execute(
                username=parsed['entities'].get('username'),
                password=parsed['entities'].get('password')
            )

        elif parsed['intent'] == 'create_agent':
            return self.create_agent_flow.execute(
                agent_name=parsed['entities'].get('agent_name', 'TestAgent'),
                description="",
                create_workflow=False
            )

        elif parsed['intent'] == 'publish':
            return self.publish_flow.execute()

        elif parsed['intent'] == 'full_flow':
            login_result = self.login_flow.execute()
            if not login_result.success:
                return login_result

            agent_name = parsed['entities'].get('agent_name', f"NLAgent_{int(time.time())}")
            create_result = self.create_agent_flow.execute(
                agent_name=agent_name,
                create_workflow=True
            )
            if not create_result.success:
                return create_result

            return self.publish_flow.execute(agent_name=agent_name)

        else:
            logger.warning(f"Unknown intent: {parsed['intent']}")
            return {"success": False, "message": f"Unknown task: {parsed['intent']}"}

    def close(self):
        if self.browser:
            self.browser.close()
        logger.info("Natural Language Driver closed")


if __name__ == "__main__":
    import unittest
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFullFlow)
    unittest.TextTestRunner(verbosity=2).run(suite)
