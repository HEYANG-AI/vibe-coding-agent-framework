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
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.config_loader.load()
        self.browser = None
        self.login_flow = None
        self.create_agent_flow = None
        self.publish_flow = None
        self.results = []
        self.agent_name = None

    def setup(self):
        logger.info("Setting up test environment...")
        self.browser = BrowserAdapter()
        self.login_flow = LoginFlow(self.browser)
        self.create_agent_flow = CreateAgentFlow(self.browser)
        self.publish_flow = PublishFlow(self.browser)
        logger.info("Test environment ready")

    def teardown(self):
        logger.info("Tearing down test environment...")
        if self.browser:
            self.browser.close()
        logger.info("Test environment closed")

    def test_step_1_login(self):
        result = {"step": 1, "name": "login", "success": False, "message": "", "duration": 0.0}

        start_time = time.time()

        try:
            login_result = self.login_flow.execute(
                username=self.config_loader.get_credential('username'),
                password=self.config_loader.get_credential('password'),
                use_session=True
            )

            result["success"] = login_result.success
            result["message"] = login_result.message

            if login_result.success:
                logger.info(f"Step 1 (Login) PASSED: {login_result.message}")
            else:
                logger.error(f"Step 1 (Login) FAILED: {login_result.message}")

        except Exception as e:
            result["message"] = f"Login exception: {str(e)}"
            logger.error(result["message"])

        result["duration"] = time.time() - start_time
        self.results.append(result)
        return result

    def test_step_2_create_agent(self):
        result = {"step": 2, "name": "create_agent", "success": False, "message": "", "duration": 0.0}

        start_time = time.time()

        try:
            self.agent_name = f"FullFlowAgent_{int(time.time())}"

            create_result = self.create_agent_flow.execute(
                agent_name=self.agent_name,
                description="完整流程测试创建的Agent",
                create_workflow=True
            )

            result["success"] = create_result.success
            result["message"] = create_result.message
            result["agent_name"] = self.agent_name

            if create_result.success:
                logger.info(f"Step 2 (Create Agent) PASSED: {self.agent_name}")
            else:
                logger.error(f"Step 2 (Create Agent) FAILED: {create_result.message}")

        except Exception as e:
            result["message"] = f"Create agent exception: {str(e)}"
            logger.error(result["message"])

        result["duration"] = time.time() - start_time
        self.results.append(result)
        return result

    def test_step_3_publish(self):
        result = {"step": 3, "name": "publish", "success": False, "message": "", "duration": 0.0}

        start_time = time.time()

        try:
            publish_result = self.publish_flow.execute(
                agent_name=self.agent_name
            )

            result["success"] = publish_result.success
            result["message"] = publish_result.message

            if publish_result.success:
                logger.info(f"Step 3 (Publish) PASSED: {publish_result.message}")
            else:
                logger.error(f"Step 3 (Publish) FAILED: {publish_result.message}")

        except Exception as e:
            result["message"] = f"Publish exception: {str(e)}"
            logger.error(result["message"])

        result["duration"] = time.time() - start_time
        self.results.append(result)
        return result

    def test_full_flow(self):
        result = {"name": "test_full_flow", "success": False, "message": "", "steps": []}

        logger.info("=" * 60)
        logger.info("Starting Full Flow Test")
        logger.info("=" * 60)

        try:
            step1 = self.test_step_1_login()
            if not step1["success"]:
                result["message"] = "Full flow failed at login step"
                self.results.append(result)
                return result

            step2 = self.test_step_2_create_agent()
            if not step2["success"]:
                result["message"] = "Full flow failed at create agent step"
                self.results.append(result)
                return result

            step3 = self.test_step_3_publish()
            if not step3["success"]:
                result["message"] = "Full flow failed at publish step"
                self.results.append(result)
                return result

            result["success"] = True
            result["message"] = f"Full flow completed successfully for agent: {self.agent_name}"
            logger.info(result["message"])

        except Exception as e:
            result["message"] = f"Full flow exception: {str(e)}"
            logger.error(result["message"])

        self.results.append(result)
        return result

    def run_all_tests(self):
        logger.info("=" * 60)
        logger.info("Starting Full Flow Tests")
        logger.info("=" * 60)

        self.setup()

        try:
            self.test_full_flow()

        finally:
            self.teardown()

        logger.info("=" * 60)
        logger.info("Full Flow Tests Completed")
        logger.info("=" * 60)

        passed = sum(1 for r in self.results if r.get("success", False))
        failed = len(self.results) - passed

        total_duration = sum(r.get("duration", 0) for r in self.results)

        logger.info(f"Results: {passed} passed, {failed} failed")
        logger.info(f"Total duration: {total_duration:.2f}s")

        return {
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "total_duration": total_duration,
            "results": self.results
        }


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
    test = TestFullFlow()
    report = test.run_all_tests()
    print("\n" + "=" * 60)
    print("FULL FLOW TEST REPORT")
    print("=" * 60)
    print(f"Total: {report['total']}")
    print(f"Passed: {report['passed']}")
    print(f"Failed: {report['failed']}")
    print(f"Duration: {report['total_duration']:.2f}s")
    print("\nStep Details:")
    for r in report['results']:
        status = "PASS" if r.get('success', False) else "FAIL"
        step_name = r.get('name', r.get('step', 'unknown'))
        print(f"  [{status}] Step {r.get('step', '')} ({step_name}): {r['message']}")
        if 'duration' in r:
            print(f"      Duration: {r['duration']:.2f}s")
