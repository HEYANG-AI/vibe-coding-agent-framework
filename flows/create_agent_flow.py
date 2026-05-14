import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from core.browser_adapter import BrowserAdapter, Locator
from core.learning_engine import LearningEngine
from core.self_healing import SelfHealingEngine
from core.tools import Tools, StepExecutor, ScreenshotManager, AssertHelper

logger = logging.getLogger(__name__)


@dataclass
class CreateAgentResult:
    success: bool
    message: str
    agent_name: str = ""
    screenshot_path: Optional[str] = None
    agent_id: Optional[str] = None


class CreateAgentFlow:
    def __init__(self, browser: Optional[BrowserAdapter] = None,
                 config_path: Optional[str] = None):
        self.browser = browser or BrowserAdapter()
        self.learning = LearningEngine(self.browser, config_path)
        self.healing = SelfHealingEngine(self.browser, self.learning.config_loader)
        self.screenshot_mgr = ScreenshotManager()
        self.step_executor = StepExecutor(self.browser, self.screenshot_mgr)
        self.tools = Tools()
        self.assert_helper = AssertHelper()

        self._menu_agent_locators = [
            Locator(loc_type='xpath', value="//*[contains(text(), 'Agent')]", description="Agent menu item", priority=80),
            Locator(loc_type='xpath', value="//*[contains(text(), '智能体')]", description="Agent menu item Chinese", priority=85),
            Locator(loc_type='xpath', value="//*[contains(@class, 'menu')]//*[contains(text(), 'Agent')]", description="Agent in menu", priority=75),
            Locator(loc_type='xpath', value="//a[contains(@href, 'agent')]", description="Agent link", priority=70),
        ]

        self._new_agent_button_locators = [
            Locator(loc_type='xpath', value="//button[contains(text(), '新建')]", description="New button", priority=85),
            Locator(loc_type='xpath', value="//button[contains(text(), '创建')]", description="Create button", priority=80),
            Locator(loc_type='xpath', value="//button[contains(@class, 'new')]", description="New button by class", priority=70),
            Locator(loc_type='xpath', value="//*[contains(@class, 'btn') and contains(text(), '新建')]", description="New button by class", priority=75),
            Locator(loc_type='xpath', value="//a[contains(text(), '新建')]", description="New link", priority=80),
        ]

        self._agent_name_input_locators = [
            Locator(loc_type='xpath', value="//input[@name='name']", description="Name input", priority=90),
            Locator(loc_type='xpath', value="//input[contains(@placeholder, '名称')]", description="Name by placeholder", priority=80),
            Locator(loc_type='xpath', value="//input[contains(@placeholder, '名字')]", description="Name by placeholder", priority=80),
            Locator(loc_type='xpath', value="//input[contains(@id, 'name')]", description="Name by id", priority=85),
            Locator(loc_type='xpath', value="//textarea[@name='name']", description="Name textarea", priority=80),
        ]

        self._agent_desc_input_locators = [
            Locator(loc_type='xpath', value="//textarea[@name='description']", description="Description textarea", priority=90),
            Locator(loc_type='xpath', value="//textarea[contains(@placeholder, '描述')]", description="Description by placeholder", priority=80),
            Locator(loc_type='xpath', value="//input[@name='description']", description="Description input", priority=80),
        ]

        self._canvas_area_locators = [
            Locator(loc_type='xpath', value="//*[contains(@class, 'canvas')]", description="Canvas area", priority=80),
            Locator(loc_type='xpath', value="//*[contains(@class, 'flow')]", description="Flow area", priority=75),
            Locator(loc_type='xpath', value="//*[contains(@id, 'canvas')]", description="Canvas by id", priority=85),
            Locator(loc_type='xpath', value="//*[contains(@role, 'application')]", description="Application area", priority=70),
        ]

        self._node_buttons = [
            Locator(loc_type='xpath', value="//*[contains(@class, 'node')]//*[contains(@class, 'add')]", description="Add node button", priority=80),
            Locator(loc_type='xpath', value="//button[contains(@class, 'add')]", description="Add button", priority=75),
            Locator(loc_type='xpath', value="//*[contains(text(), '添加节点')]", description="Add node text", priority=85),
            Locator(loc_type='xpath', value="//*[contains(@class, 'toolbar')]//*[contains(text(), '添加')]", description="Add from toolbar", priority=70),
        ]

        self._save_button_locators = [
            Locator(loc_type='xpath', value="//button[contains(text(), '保存')]", description="Save button", priority=90),
            Locator(loc_type='xpath', value="//*[contains(@class, 'btn') and contains(text(), '保存')]", description="Save button by class", priority=85),
            Locator(loc_type='xpath', value="//button[@type='submit']", description="Submit button", priority=70),
        ]

        self._confirm_button_locators = [
            Locator(loc_type='xpath', value="//button[contains(text(), '确认')]", description="Confirm button", priority=90),
            Locator(loc_type='xpath', value="//button[contains(text(), '确定')]", description="OK button", priority=85),
            Locator(loc_type='xpath', value="//*[contains(@class, 'confirm')]", description="Confirm by class", priority=70),
        ]

        logger.info("CreateAgentFlow initialized")

    def execute(self, agent_name: str, description: str = "",
                create_workflow: bool = False) -> CreateAgentResult:
        logger.info("=" * 60)
        logger.info(f"Starting create agent flow: {agent_name}")
        logger.info("=" * 60)

        try:
            self.step_executor.execute_step(
                "Navigate to create agent page",
                self._navigate_to_create_agent
            )

            self.step_executor.execute_step(
                "Click new agent button",
                self._click_new_agent_button
            )

            self.step_executor.execute_step(
                "Enter agent name",
                self._enter_agent_name,
                agent_name
            )

            if description:
                self.step_executor.execute_step(
                    "Enter agent description",
                    self._enter_agent_description,
                    description
                )

            if create_workflow:
                self.step_executor.execute_step(
                    "Navigate to canvas",
                    self._navigate_to_canvas
                )

                self.step_executor.execute_step(
                    "Create workflow on canvas",
                    self._create_workflow
                )

            self.step_executor.execute_step(
                "Save agent",
                self._save_agent
            )

            self.step_executor.execute_step(
                "Confirm creation",
                self._confirm_creation
            )

            summary = self.step_executor.get_summary()

            if summary['failed'] > 0:
                failed_steps = [s for s in summary['steps'] if not s.success]
                logger.error(f"Create agent failed. {summary['failed']} step(s) failed:")
                for step in failed_steps:
                    logger.error(f"  - {step.step_name}: {step.error}")

                return CreateAgentResult(
                    success=False,
                    message=f"Create agent failed: {failed_steps[0].error if failed_steps else 'Unknown error'}",
                    agent_name=agent_name,
                    screenshot_path=failed_steps[0].screenshot_path if failed_steps else None
                )

            logger.info(f"Agent '{agent_name}' created successfully")
            return CreateAgentResult(
                success=True,
                message="Agent created successfully",
                agent_name=agent_name
            )

        except Exception as e:
            logger.error(f"Create agent flow exception: {e}")
            screenshot = self.screenshot_mgr.capture(self.browser.driver, "create_agent_exception")
            return CreateAgentResult(
                success=False,
                message=f"Create agent exception: {str(e)}",
                agent_name=agent_name,
                screenshot_path=screenshot
            )

    def _navigate_to_create_agent(self):
        logger.info("Navigating to create agent page")

        current_url = self.browser.get_current_url()
        logger.info(f"Current URL: {current_url}")

        agent_element = self._find_element_with_healing("agent_menu", self._menu_agent_locators)
        if agent_element:
            self.browser.click(agent_element)
            time.sleep(2)
            logger.info("Clicked agent menu")
        else:
            logger.warning("Could not find agent menu, trying direct navigation")

        new_agent = self._find_element_with_healing("new_agent_button", self._new_agent_button_locators)
        if new_agent:
            self.browser.click(new_agent)
            time.sleep(2)
            logger.info("Clicked new agent button")

        self.browser.take_screenshot("navigate_to_create_agent")

    def _click_new_agent_button(self):
        logger.info("Clicking new agent button")

        element = self._find_element_with_healing("new_agent_button", self._new_agent_button_locators)
        if not element:
            raise Exception("New agent button not found")

        self.browser.click(element)
        time.sleep(3)
        self.browser.take_screenshot("after_new_agent_click")

    def _enter_agent_name(self, name: str):
        logger.info(f"Entering agent name: {name}")

        element = self._find_element_with_healing("agent_name", self._agent_name_input_locators)
        if not element:
            raise Exception("Agent name input not found")

        self.browser.input_text(element, name)
        logger.info("Agent name entered")

    def _enter_agent_description(self, description: str):
        logger.info(f"Entering agent description: {description}")

        element = self._find_element_with_healing("agent_description", self._agent_desc_input_locators)
        if element:
            self.browser.input_text(element, description)
            logger.info("Agent description entered")
        else:
            logger.warning("Description input not found, skipping")

    def _navigate_to_canvas(self):
        logger.info("Navigating to canvas area")

        canvas = self._find_element_with_healing("canvas", self._canvas_area_locators)
        if canvas:
            logger.info("Found canvas area")
            self.browser.take_screenshot("canvas_area")
        else:
            logger.warning("Canvas area not found")

    def _create_workflow(self):
        logger.info("Creating workflow on canvas")

        node_button = self._find_element_with_healing("add_node", self._node_buttons)
        if node_button:
            self.browser.click(node_button)
            time.sleep(2)
            logger.info("Clicked add node button")

            self._select_workflow_node_type()
        else:
            logger.warning("Add node button not found")

        self.browser.take_screenshot("workflow_created")

    def _select_workflow_node_type(self):
        logger.info("Selecting workflow node type")

        node_types = [
            Locator(loc_type='xpath', value="//*[contains(text(), 'LLM')]", description="LLM node", priority=80),
            Locator(loc_type='xpath', value="//*[contains(text(), '开始')]", description="Start node", priority=85),
            Locator(loc_type='xpath', value="//*[contains(text(), '结束')]", description="End node", priority=85),
            Locator(loc_type='xpath', value="//*[contains(@class, 'node-item')]", description="Node item", priority=70),
        ]

        for locator in node_types:
            try:
                element = self.browser.driver.find_element(locator.loc_type, locator.value)
                if element and self.browser._is_element_valid(element):
                    self.browser.click(element)
                    logger.info(f"Selected node type: {locator.description}")
                    time.sleep(2)
                    return
            except:
                continue

        logger.warning("Could not select specific node type")

    def _save_agent(self):
        logger.info("Saving agent")

        element = self._find_element_with_healing("save_button", self._save_button_locators)
        if not element:
            raise Exception("Save button not found")

        self.browser.click(element)
        time.sleep(3)
        self.browser.take_screenshot("agent_saved")

    def _confirm_creation(self):
        logger.info("Confirming agent creation")

        try:
            element = self._find_element_with_healing("confirm_button", self._confirm_button_locators)
            if element:
                self.browser.click(element)
                time.sleep(3)
                logger.info("Clicked confirm button")
        except Exception as e:
            logger.warning(f"Confirm button not found or click failed: {e}")

        self.browser.take_screenshot("agent_creation_complete")

    def _find_element_with_healing(self, element_name: str,
                                   locators: List[Locator]) -> Optional[Any]:
        for locator in locators:
            try:
                element = self.browser.driver.find_element(locator.loc_type, locator.value)
                if element and self.browser._is_element_valid(element):
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

    def get_step_results(self):
        return self.step_executor.get_results()

    def get_summary(self):
        return self.step_executor.get_summary()


class NaturalLanguageCreateAgent:
    def __init__(self, create_agent_flow: CreateAgentFlow):
        self.create_agent_flow = create_agent_flow
        self.tools = Tools()

    def execute(self, task: str) -> CreateAgentResult:
        parsed = self.tools.parse_natural_language(task)

        if parsed['intent'] not in ['create_agent', 'full_flow', 'workflow']:
            return CreateAgentResult(
                success=False,
                message=f"Task '{task}' is not a create agent task"
            )

        entities = parsed['entities']
        agent_name = entities.get('agent_name', 'TestAgent')

        create_workflow = 'workflow' in task.lower() or '工作流' in task

        return self.create_agent_flow.execute(
            agent_name=agent_name,
            description="",
            create_workflow=create_workflow
        )


def run_skill(task: str, browser: Optional[BrowserAdapter] = None,
              config_path: Optional[str] = None) -> CreateAgentResult:
    if browser is None:
        browser = BrowserAdapter(config_path)

    create_agent_flow = CreateAgentFlow(browser, config_path)
    nl_create = NaturalLanguageCreateAgent(create_agent_flow)

    return nl_create.execute(task)
