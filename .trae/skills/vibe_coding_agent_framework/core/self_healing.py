import os
import time
import logging
import re
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import yaml

from .browser_adapter import BrowserAdapter, Locator, PageElement
from .learning_engine import LearningEngine

logger = logging.getLogger(__name__)


@dataclass
class HealingResult:
    success: bool
    element: Optional[Any] = None
    new_locator: Optional[Locator] = None
    attempts: int = 0
    message: str = ""
    screenshot_path: Optional[str] = None


class SelfHealingEngine:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, browser_adapter: Optional[BrowserAdapter] = None,
                 learning_engine: Optional[LearningEngine] = None,
                 config_path: Optional[str] = None):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.browser = browser_adapter or BrowserAdapter(config_path)
        self.learning = learning_engine or LearningEngine(self.browser, config_path)
        self.config = self._load_config(config_path)

        self.enabled = self.config.get('self_healing', {}).get('enabled', True)
        self.max_retry = self.config.get('self_healing', {}).get('max_retry', 3)
        self.screenshot_analysis = self.config.get('self_healing', {}).get('screenshot_analysis', True)
        self.semantic_matching = self.config.get('self_healing', {}).get('semantic_matching', True)

        self._healing_history: List[Dict] = []
        self._current_attempt = 0

        logger.info("SelfHealingEngine initialized")

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"

        if isinstance(config_path, str):
            config_path = Path(config_path)

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def heal_element(self, element_name: str, original_locators: List[Locator],
                     page_url: Optional[str] = None) -> HealingResult:
        if not self.enabled:
            return HealingResult(success=False, message="Self-healing disabled")

        self._current_attempt = 0
        page_url = page_url or self.browser.get_current_url()

        logger.info(f"Starting self-healing for element: {element_name}")

        for attempt in range(self.max_retry):
            self._current_attempt = attempt + 1
            logger.info(f"Healing attempt {self._current_attempt}/{self.max_retry}")

            screenshot_path = None
            if self.screenshot_analysis:
                screenshot_path = self.browser.take_screenshot(f"healing_{element_name}_{int(time.time())}")

            result = self._try_semantic_recovery(element_name, original_locators, page_url)

            if result.success:
                self._record_healing_success(element_name, result)
                return result

            wait_time = 2 ** attempt
            logger.info(f"Waiting {wait_time}s before retry...")
            time.sleep(wait_time)

        self._record_healing_failure(element_name, original_locators)
        return HealingResult(
            success=False,
            attempts=self._current_attempt,
            message=f"Failed to heal element '{element_name}' after {self.max_retry} attempts"
        )

    def _try_semantic_recovery(self, element_name: str, original_locators: List[Locator],
                               page_url: str) -> HealingResult:
        semantic_strategies = [
            self._try_partial_text_match,
            self._try_aria_label_match,
            self._try_similar_class_match,
            self._try_nearby_element,
            self._try_relearn_page,
        ]

        for strategy in semantic_strategies:
            try:
                result = strategy(element_name, original_locators, page_url)
                if result.success:
                    return result
            except Exception as e:
                logger.warning(f"Strategy {strategy.__name__} failed: {e}")
                continue

        return HealingResult(success=False, attempts=self._current_attempt)

    def _try_partial_text_match(self, element_name: str, original_locators: List[Locator],
                                 page_url: str) -> HealingResult:
        try:
            if not element_name or len(element_name) < 2:
                return HealingResult(success=False)

            partial_name = element_name[:len(element_name)//2] if len(element_name) > 4 else element_name[0]

            xpath_patterns = [
                f"//*[contains(text(), '{partial_name}')]",
                f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{partial_name.lower()}')]",
            ]

            for pattern in xpath_patterns:
                try:
                    element = self.browser.driver.find_element("xpath", pattern)
                    if element and self._is_element_valid(element):
                        new_locator = Locator(
                            loc_type='xpath',
                            value=pattern,
                            description=f"Partial text match for {element_name}",
                            priority=50
                        )
                        self.learning.update_element_locator(page_url, element_name, new_locator)
                        return HealingResult(
                            success=True,
                            element=element,
                            new_locator=new_locator,
                            attempts=self._current_attempt
                        )
                except:
                    continue

        except Exception as e:
            logger.warning(f"Partial text match failed: {e}")

        return HealingResult(success=False, attempts=self._current_attempt)

    def _try_aria_label_match(self, element_name: str, original_locators: List[Locator],
                              page_url: str) -> HealingResult:
        try:
            aria_patterns = [
                f"//*[@aria-label='{element_name}']",
                f"//*[@aria-label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{element_name.lower()}')]]",
            ]

            for pattern in aria_patterns:
                try:
                    element = self.browser.driver.find_element("xpath", pattern)
                    if element and self._is_element_valid(element):
                        new_locator = Locator(
                            loc_type='xpath',
                            value=pattern,
                            description=f"Aria-label match for {element_name}",
                            priority=60
                        )
                        self.learning.update_element_locator(page_url, element_name, new_locator)
                        return HealingResult(
                            success=True,
                            element=element,
                            new_locator=new_locator,
                            attempts=self._current_attempt
                        )
                except:
                    continue

        except Exception as e:
            logger.warning(f"Aria-label match failed: {e}")

        return HealingResult(success=False, attempts=self._current_attempt)

    def _try_similar_class_match(self, element_name: str, original_locators: List[Locator],
                                 page_url: str) -> HealingResult:
        try:
            for locator in original_locators:
                if locator.loc_type == 'class':
                    class_name = locator.value
                    similar_patterns = [
                        f"//*[contains(@class, '{class_name}')]",
                        f"//*[contains(concat(' ', @class, ' '), ' {class_name} ')]",
                    ]

                    for pattern in similar_patterns:
                        try:
                            elements = self.browser.driver.find_elements("xpath", pattern)
                            for el in elements:
                                if self._is_element_valid(el):
                                    text = el.text.strip()
                                    if text and element_name.lower() in text.lower():
                                        new_locator = Locator(
                                            loc_type='xpath',
                                            value=pattern,
                                            description=f"Similar class match for {element_name}",
                                            priority=40
                                        )
                                        self.learning.update_element_locator(page_url, element_name, new_locator)
                                        return HealingResult(
                                            success=True,
                                            element=el,
                                            new_locator=new_locator,
                                            attempts=self._current_attempt
                                        )
                        except:
                            continue

        except Exception as e:
            logger.warning(f"Similar class match failed: {e}")

        return HealingResult(success=False, attempts=self._current_attempt)

    def _try_nearby_element(self, element_name: str, original_locators: List[Locator],
                           page_url: str) -> HealingResult:
        try:
            for locator in original_locators:
                if locator.loc_type in ['id', 'name']:
                    try:
                        anchor = self.browser.driver.find_element(
                            locator.loc_type if locator.loc_type != 'xpath' else 'xpath',
                            locator.value
                        )

                        xpath_templates = [
                            "./following-sibling::*//*[contains(text(), '{text}')]",
                            "./preceding-sibling::*//*[contains(text(), '{text}')]",
                            "./ancestor::*//*[contains(text(), '{text}')]",
                            ".//*[contains(text(), '{text}')]",
                        ]

                        for template in xpath_templates:
                            pattern = template.format(text=element_name[:20] if len(element_name) > 20 else element_name)
                            try:
                                elements = self.browser.driver.find_elements("xpath", pattern)
                                for el in elements:
                                    if self._is_element_valid(el):
                                        parent_xpath = self._get_xpath(el)
                                        new_locator = Locator(
                                            loc_type='xpath',
                                            value=parent_xpath,
                                            description=f"Nearby element for {element_name}",
                                            priority=30
                                        )
                                        self.learning.update_element_locator(page_url, element_name, new_locator)
                                        return HealingResult(
                                            success=True,
                                            element=el,
                                            new_locator=new_locator,
                                            attempts=self._current_attempt
                                        )
                            except:
                                continue
                    except:
                        continue

        except Exception as e:
            logger.warning(f"Nearby element search failed: {e}")

        return HealingResult(success=False, attempts=self._current_attempt)

    def _try_relearn_page(self, element_name: str, original_locators: List[Locator],
                          page_url: str) -> HealingResult:
        try:
            logger.info(f"Attempting to relearn page to find {element_name}")
            self.learning.relearn_page(page_url)

            time.sleep(2)

            learned_element = self.learning.find_learned_element(element_name)
            if learned_element:
                for locator in learned_element.locators:
                    try:
                        element = self.browser.driver.find_element(locator.loc_type, locator.value)
                        if element and self._is_element_valid(element):
                            self.learning.update_element_locator(page_url, element_name, locator)
                            return HealingResult(
                                success=True,
                                element=element,
                                new_locator=locator,
                                attempts=self._current_attempt,
                                message="Found via relearning"
                            )
                    except:
                        continue

            page = self.learning.get_learned_page(page_url)
            if page:
                for name, element in page.elements.items():
                    if element_name.lower() in name.lower():
                        for locator in element.locators:
                            try:
                                el = self.browser.driver.find_element(locator.loc_type, locator.value)
                                if el and self._is_element_valid(el):
                                    return HealingResult(
                                        success=True,
                                        element=el,
                                        new_locator=locator,
                                        attempts=self._current_attempt,
                                        message=f"Found similar element: {name}"
                                    )
                            except:
                                continue

        except Exception as e:
            logger.warning(f"Relearn page failed: {e}")

        return HealingResult(success=False, attempts=self._current_attempt)

    def _is_element_valid(self, element) -> bool:
        try:
            return element.is_displayed() and element.is_enabled()
        except:
            return False

    def _get_xpath(self, element) -> str:
        try:
            return self.browser.driver.execute_script(
                "function getXPath(element) {"
                "  if (element.id) return \"//*[@id='\" + element.id + \"']\";"
                "  if (element === document.body) return element.tagName;"
                "  var ix = 0;"
                "  var siblings = element.parentNode.childNodes;"
                "  for (var i = 0; i < siblings.length; i++) {"
                "    var sibling = siblings[i];"
                "    if (sibling === element) {"
                "      var parent = getXPath(element.parentNode);"
                "      var tagName = element.tagName.toLowerCase();"
                "      return parent + '/' + tagName + '[' + (ix + 1) + ']';"
                "    }"
                "    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {"
                "      ix++;"
                "    }"
                "  }"
                "}"
                "return getXPath(arguments[0]);",
                element
            )
        except:
            return ""

    def _record_healing_success(self, element_name: str, result: HealingResult):
        record = {
            'element_name': element_name,
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'attempts': result.attempts,
            'new_locator': str(result.new_locator) if result.new_locator else None,
            'screenshot': result.screenshot_path
        }
        self._healing_history.append(record)
        logger.info(f"Healing SUCCESS for '{element_name}' after {result.attempts} attempt(s)")

    def _record_healing_failure(self, element_name: str, original_locators: List[Locator]):
        record = {
            'element_name': element_name,
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'attempts': self._current_attempt,
            'original_locators': [str(loc) for loc in original_locators]
        }
        self._healing_history.append(record)
        logger.error(f"Healing FAILED for '{element_name}' after {self._current_attempt} attempt(s)")

        if self.config.get('logging', {}).get('screenshot_on_failure', True):
            screenshot_path = self.browser.take_screenshot(f"healing_failure_{element_name}_{int(time.time())}")
            record['failure_screenshot'] = screenshot_path

    def get_healing_history(self) -> List[Dict]:
        return self._healing_history

    def clear_history(self):
        self._healing_history.clear()

    def is_enabled(self) -> bool:
        return self.enabled

    def enable(self):
        self.enabled = True
        logger.info("Self-healing enabled")

    def disable(self):
        self.enabled = False
        logger.info("Self-healing disabled")


class RetryHandler:
    def __init__(self, max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff = backoff

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        last_exception = None
        current_delay = self.delay

        for attempt in range(self.max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1}/{self.max_attempts} failed: {e}")

                if attempt < self.max_attempts - 1:
                    logger.info(f"Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= self.backoff

        raise last_exception

    def execute_with_healing(self, healing_engine: SelfHealingEngine,
                            element_name: str, locators: List[Locator],
                            action: Callable, *args, **kwargs) -> Any:
        result = healing_engine.heal_element(element_name, locators)

        if result.success and result.element:
            return action(result.element, *args, **kwargs)

        for locator in locators:
            try:
                element = healing_engine.browser.driver.find_element(locator.loc_type, locator.value)
                if healing_engine._is_element_valid(element):
                    return action(element, *args, **kwargs)
            except:
                continue

        raise RuntimeError(f"Failed to execute action on element '{element_name}' after healing attempts")
