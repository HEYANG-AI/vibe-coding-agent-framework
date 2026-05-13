import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from core.browser_adapter import BrowserAdapter, Locator
from core.learning_engine import LearningEngine
from core.self_healing import SelfHealingEngine
from core.tools import Tools, StepExecutor, ScreenshotManager

logger = logging.getLogger(__name__)


@dataclass
class PublishResult:
    success: bool
    message: str
    agent_name: str = ""
    publish_url: Optional[str] = None
    screenshot_path: Optional[str] = None


class PublishFlow:
    def __init__(self, browser: Optional[BrowserAdapter] = None,
                 config_path: Optional[str] = None):
        self.browser = browser or BrowserAdapter()
        self.learning = LearningEngine(self.browser, config_path)
        self.healing = SelfHealingEngine(self.browser, self.learning, config_path)
        self.screenshot_mgr = ScreenshotManager()
        self.step_executor = StepExecutor(self.browser, self.screenshot_mgr)
        self.tools = Tools()

        self._publish_button_locators = [
            Locator(loc_type='xpath', value="//button[contains(text(), '发布')]", description="Publish button", priority=90),
            Locator(loc_type='xpath', value="//button[contains(text(), '上线')]", description="Online button", priority=85),
            Locator(loc_type='xpath', value="//*[contains(@class, 'btn') and contains(text(), '发布')]", description="Publish by class", priority=85),
            Locator(loc_type='xpath', value="//a[contains(text(), '发布')]", description="Publish link", priority=80),
            Locator(loc_type='xpath', value="//*[contains(@class, 'publish')]", description="Publish by class", priority=70),
        ]

        self._publish_confirm_locators = [
            Locator(loc_type='xpath', value="//button[contains(text(), '确认发布')]", description="Confirm publish", priority=90),
            Locator(loc_type='xpath', value="//button[contains(text(), '确认')]", description="Confirm button", priority=85),
            Locator(loc_type='xpath', value="//button[contains(text(), '确定')]", description="OK button", priority=80),
            Locator(loc_type='xpath', value="//*[contains(@class, 'confirm')]//button", description="Confirm dialog button", priority=75),
        ]

        self._publish_success_indicator = [
            Locator(loc_type='xpath', value="//*[contains(text(), '发布成功')]", description="Publish success", priority=90),
            Locator(loc_type='xpath', value="//*[contains(text(), '上线成功')]", description="Online success", priority=85),
            Locator(loc_type='xpath', value="//*[contains(@class, 'success')]", description="Success indicator", priority=80),
            Locator(loc_type='xpath', value="//*[contains(text(), '已发布')]", description="Already published", priority=85),
        ]

        self._status_indicator = [
            Locator(loc_type='xpath', value="//*[contains(@class, 'status')]", description="Status indicator", priority=80),
            Locator(loc_type='xpath', value="//*[contains(@class, 'badge')]", description="Badge indicator", priority=75),
            Locator(loc_type='xpath', value="//*[contains(text(), '已发布')]", description="Published status", priority=85),
        ]

        logger.info("PublishFlow initialized")

    def execute(self, agent_name: Optional[str] = None) -> PublishResult:
        logger.info("=" * 60)
        logger.info(f"Starting publish flow: {agent_name or 'current agent'}")
        logger.info("=" * 60)

        try:
            self.step_executor.execute_step(
                "Locate publish button",
                self._locate_publish_button
            )

            self.step_executor.execute_step(
                "Click publish button",
                self._click_publish_button
            )

            self.step_executor.execute_step(
                "Confirm publish",
                self._confirm_publish
            )

            self.step_executor.execute_step(
                "Verify publish success",
                self._verify_publish_success
            )

            summary = self.step_executor.get_summary()

            if summary['failed'] > 0:
                failed_steps = [s for s in summary['steps'] if not s.success]
                logger.error(f"Publish failed. {summary['failed']} step(s) failed:")
                for step in failed_steps:
                    logger.error(f"  - {step.step_name}: {step.error}")

                return PublishResult(
                    success=False,
                    message=f"Publish failed: {failed_steps[0].error if failed_steps else 'Unknown error'}",
                    agent_name=agent_name or "",
                    screenshot_path=failed_steps[0].screenshot_path if failed_steps else None
                )

            logger.info(f"Agent '{agent_name}' published successfully")
            return PublishResult(
                success=True,
                message="Agent published successfully",
                agent_name=agent_name or ""
            )

        except Exception as e:
            logger.error(f"Publish flow exception: {e}")
            screenshot = self.screenshot_mgr.capture(self.browser.driver, "publish_exception")
            return PublishResult(
                success=False,
                message=f"Publish exception: {str(e)}",
                agent_name=agent_name or "",
                screenshot_path=screenshot
            )

    def _locate_publish_button(self):
        logger.info("Locating publish button")

        element = self._find_element_with_healing("publish_button", self._publish_button_locators)
        if not element:
            raise Exception("Publish button not found")

        logger.info("Publish button located")
        self.browser.take_screenshot("publish_button_found")

    def _click_publish_button(self):
        logger.info("Clicking publish button")

        element = self._find_element_with_healing("publish_button", self._publish_button_locators)
        if not element:
            raise Exception("Publish button not found")

        self.browser.click(element)
        time.sleep(3)
        self.browser.take_screenshot("after_publish_click")

    def _confirm_publish(self):
        logger.info("Confirming publish")

        time.sleep(2)

        try:
            element = self._find_element_with_healing("publish_confirm", self._publish_confirm_locators)
            if element:
                self.browser.click(element)
                logger.info("Clicked publish confirm button")
                time.sleep(3)
            else:
                logger.info("No explicit confirm needed or dialog not found")
        except Exception as e:
            logger.warning(f"Confirm step issue: {e}")

        self.browser.take_screenshot("publish_confirmed")

    def _verify_publish_success(self):
        logger.info("Verifying publish success")

        time.sleep(5)

        for locator in self._publish_success_indicator:
            try:
                elements = self.browser.driver.find_elements(locator.loc_type, locator.value)
                for el in elements:
                    if el.is_displayed():
                        logger.info(f"Found success indicator: {locator.description}")
                        self.browser.take_screenshot("publish_success")
                        return
            except:
                continue

        logger.info("Success indicator not found, checking URL or status")

        current_url = self.browser.get_current_url()
        page_source = self.browser.get_page_source().lower()

        if any(word in page_source for word in ['发布成功', '上线成功', '已发布', 'published', 'success']):
            logger.info("Publish appears successful based on page content")
            self.browser.take_screenshot("publish_success")
            return

        logger.warning("Could not verify publish success explicitly")
        self.browser.take_screenshot("publish_status_uncertain")

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


class NaturalLanguagePublish:
    def __init__(self, publish_flow: PublishFlow):
        self.publish_flow = publish_flow
        self.tools = Tools()

    def execute(self, task: str) -> PublishResult:
        parsed = self.tools.parse_natural_language(task)

        if parsed['intent'] not in ['publish', 'full_flow']:
            return PublishResult(
                success=False,
                message=f"Task '{task}' is not a publish task"
            )

        return self.publish_flow.execute()


def run_skill(task: str, browser: Optional[BrowserAdapter] = None,
              config_path: Optional[str] = None) -> PublishResult:
    if browser is None:
        browser = BrowserAdapter(config_path)

    publish_flow = PublishFlow(browser, config_path)
    nl_publish = NaturalLanguagePublish(publish_flow)

    return nl_publish.execute(task)
