import os
import sys
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
SKILL_DIR = Path(__file__).parent

sys.path.insert(0, str(SKILL_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

os.chdir(SKILL_DIR)

from core.browser_adapter import BrowserAdapter, Locator
from core.learning_engine import LearningEngine
from core.self_healing import SelfHealingEngine
from core.tools import Tools, Logger, ConfigLoader, StepExecutor, ScreenshotManager
from flows.login_flow import LoginFlow, NaturalLanguageLogin
from flows.create_agent_flow import CreateAgentFlow, NaturalLanguageCreateAgent
from flows.publish_flow import PublishFlow, NaturalLanguagePublish

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("vibe-coding-agent-frameworkAgentRunner")


class vibe-coding-agent-frameworkAgentPlatform:
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.config_loader.load(str(SKILL_DIR / "config.yaml"))
        self.browser = None
        self.login_flow = None
        self.create_agent_flow = None
        self.publish_flow = None

    def initialize(self):
        logger.info("Initializing vibe-coding-agent-framework Agent Platform Runner...")
        self.browser = BrowserAdapter(str(SKILL_DIR / "config.yaml"))
        self.login_flow = LoginFlow(self.browser, str(SKILL_DIR / "config.yaml"))
        self.create_agent_flow = CreateAgentFlow(self.browser, str(SKILL_DIR / "config.yaml"))
        self.publish_flow = PublishFlow(self.browser, str(SKILL_DIR / "config.yaml"))
        logger.info("Initialization complete")

    def close(self):
        if self.browser:
            self.browser.close()
        logger.info("Browser closed")

    def login(self, username: str = None, password: str = None):
        return self.login_flow.execute(username=username, password=password)

    def create_agent(self, agent_name: str, description: str = "", create_workflow: bool = False):
        return self.create_agent_flow.execute(
            agent_name=agent_name,
            description=description,
            create_workflow=create_workflow
        )

    def publish(self, agent_name: str = None):
        return self.publish_flow.execute(agent_name=agent_name)

    def execute_full_flow(self, agent_name: str = None, description: str = ""):
        logger.info("=" * 60)
        logger.info("Starting Full Flow Execution")
        logger.info("=" * 60)

        try:
            login_result = self.login()
            if not login_result.success:
                logger.error(f"Login failed: {login_result.message}")
                return {"success": False, "step": "login", "message": login_result.message}

            agent_name = agent_name or f"AutoAgent_{int(os.time.time())}"

            create_result = self.create_agent(agent_name, description, create_workflow=True)
            if not create_result.success:
                logger.error(f"Create agent failed: {create_result.message}")
                return {"success": False, "step": "create_agent", "message": create_result.message}

            publish_result = self.publish(agent_name)
            if not publish_result.success:
                logger.error(f"Publish failed: {publish_result.message}")
                return {"success": False, "step": "publish", "message": publish_result.message}

            logger.info("Full flow completed successfully!")
            return {
                "success": True,
                "agent_name": agent_name,
                "message": "Full flow completed successfully"
            }

        except Exception as e:
            logger.error(f"Full flow exception: {e}")
            return {"success": False, "message": str(e)}
        finally:
            self.close()

    def execute_natural_language(self, task: str):
        logger.info(f"Received natural language task: {task}")

        tools = Tools()
        parsed = tools.parse_natural_language(task)

        logger.info(f"Parsed intent: {parsed['intent']}")
        logger.info(f"Entities: {parsed['entities']}")

        self.initialize()

        try:
            if parsed['intent'] == 'login':
                return self.login(
                    username=parsed['entities'].get('username'),
                    password=parsed['entities'].get('password')
                )

            elif parsed['intent'] == 'create_agent':
                return self.create_agent(
                    agent_name=parsed['entities'].get('agent_name', 'TestAgent'),
                    description=""
                )

            elif parsed['intent'] == 'workflow':
                return self.create_agent(
                    agent_name=parsed['entities'].get('agent_name', 'TestAgent'),
                    description="",
                    create_workflow=True
                )

            elif parsed['intent'] == 'publish':
                return self.publish()

            elif parsed['intent'] == 'full_flow':
                return self.execute_full_flow(
                    agent_name=parsed['entities'].get('agent_name'),
                    description=""
                )

            else:
                return {"success": False, "message": f"Unknown intent: {parsed['intent']}"}

        finally:
            self.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="vibe-coding-agent-framework Agent Platform Automation")
    parser.add_argument('--task', type=str, help='Natural language task')
    parser.add_argument('--username', type=str, help='Username for login')
    parser.add_argument('--password', type=str, help='Password for login')
    parser.add_argument('--agent-name', type=str, help='Agent name for creation')
    parser.add_argument('--description', type=str, default='', help='Agent description')
    parser.add_argument('--flow', type=str, choices=['login', 'create', 'publish', 'full'],
                       default='full', help='Flow to execute')

    args = parser.parse_args()

    platform = vibe-coding-agent-frameworkAgentPlatform()

    if args.task:
        result = platform.execute_natural_language(args.task)
        print(f"\nResult: {result}")
        return

    platform.initialize()

    try:
        if args.flow == 'login':
            result = platform.login(args.username, args.password)
        elif args.flow == 'create':
            if not args.agent_name:
                print("Error: --agent-name is required for create flow")
                return
            result = platform.create_agent(args.agent_name, args.description)
        elif args.flow == 'publish':
            result = platform.publish(args.agent_name)
        elif args.flow == 'full':
            result = platform.execute_full_flow(args.agent_name, args.description)

        print(f"\n{'='*60}")
        print("EXECUTION RESULT")
        print(f"{'='*60}")
        print(f"Success: {result.get('success', False)}")
        print(f"Message: {result.get('message', '')}")
        if 'agent_name' in result:
            print(f"Agent Name: {result['agent_name']}")

    finally:
        platform.close()


if __name__ == "__main__":
    main()
