import time
import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from core.browser_adapter import BrowserAdapter, Locator
from core.tools import ConfigLoader

logger = logging.getLogger(__name__)


@dataclass
class HealingResult:
    success: bool
    element: Optional[Any] = None
    message: str = ""


class SelfHealingEngine:
    def __init__(self, browser: BrowserAdapter, config_loader: Optional[ConfigLoader] = None):
        self.browser = browser
        self.config_loader = config_loader or ConfigLoader()
        self.config_loader.load()
        
        self.self_healing_enabled = self.config_loader.get('self_healing.enabled', True)
        self.max_retry = self.config_loader.get('self_healing.max_retry', 3)
        self.screenshot_analysis = self.config_loader.get('self_healing.screenshot_analysis', True)
        self.semantic_matching = self.config_loader.get('self_healing.semantic_matching', True)
        
        self._failed_locators: Dict[str, int] = {}
        self._alternative_locators: Dict[str, List[Locator]] = {}
        
        logger.info("SelfHealingEngine initialized")

    def heal_and_retry(self, name: str, locators: List[Locator], action: callable, *args, **kwargs) -> Any:
        if not self.self_healing_enabled:
            return self._execute_with_retry(locators, action, *args, **kwargs)
        
        logger.info(f"Self-healing attempt for: {name}")
        
        original_locators = locators.copy()
        attempt = 0
        
        while attempt < self.max_retry:
            try:
                result = action(*args, **kwargs)
                logger.info(f"Action succeeded on attempt {attempt + 1}")
                self._clear_failure_history(name)
                return result
                
            except Exception as e:
                attempt += 1
                logger.warning(f"Attempt {attempt} failed: {e}")
                
                if attempt < self.max_retry:
                    if self.semantic_matching:
                        new_locators = self._generate_semantic_alternatives(name, original_locators)
                        if new_locators:
                            logger.info(f"Generated {len(new_locators)} alternative locators")
                            locators = new_locators
                    
                    if self.screenshot_analysis:
                        self._capture_failure_context(name)
                
                time.sleep(1 * attempt)
        
        logger.error(f"Self-healing exhausted after {self.max_retry} attempts")
        self._record_failure(name, original_locators)
        raise Exception(f"Self-healing failed for {name} after {self.max_retry} attempts")

    def _execute_with_retry(self, locators: List[Locator], action: callable, *args, **kwargs) -> Any:
        last_error = None
        
        for attempt in range(self.max_retry):
            try:
                return action(*args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Retry attempt {attempt + 1} failed: {e}")
                time.sleep(1 * (attempt + 1))
        
        raise last_error or Exception("All retry attempts failed")

    def _generate_semantic_alternatives(self, name: str, original_locators: List[Locator]) -> List[Locator]:
        alternatives = []
        import re
        
        for locator in original_locators:
            if locator.loc_type == 'xpath' and 'text()' in locator.value:
                text_match = re.search(r"text\(\)='([^']+)'", locator.value)
                if text_match:
                    text = text_match.group(1)
                    
                    alternatives.append(
                        Locator(
                            loc_type='xpath',
                            value=f"//*[contains(text(), '{text}')]",
                            description=f"Semantic alternative for {name}",
                            priority=locator.priority - 10
                        )
                    )
                    
                    if len(text) > 3:
                        alternatives.append(
                            Locator(
                                loc_type='xpath',
                                value=f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]",
                                description=f"Case-insensitive alternative for {name}",
                                priority=locator.priority - 20
                            )
                        )
        
        return alternatives[:3]

    def _capture_failure_context(self, name: str):
        try:
            screenshot_name = f"self_heal_failure_{name}_{int(time.time())}"
            self.browser.take_screenshot(screenshot_name)
            logger.info(f"Captured failure context: {screenshot_name}")
        except Exception as e:
            logger.warning(f"Failed to capture failure context: {e}")

    def _record_failure(self, name: str, locators: List[Locator]):
        self._failed_locators[name] = self._failed_locators.get(name, 0) + 1
        self._alternative_locators[name] = locators
        logger.warning(f"Recorded failure for {name}. Total failures: {self._failed_locators[name]}")

    def _clear_failure_history(self, name: str):
        if name in self._failed_locators:
            del self._failed_locators[name]
        if name in self._alternative_locators:
            del self._alternative_locators[name]

    def get_failure_count(self, name: str) -> int:
        return self._failed_locators.get(name, 0)

    def has_consistent_failures(self, name: str, threshold: int = 3) -> bool:
        return self.get_failure_count(name) >= threshold

    def heal_element(self, element_name: str, locators: List[Locator]) -> HealingResult:
        if not self.self_healing_enabled:
            return HealingResult(success=False, message="Self-healing is disabled")

        logger.info(f"Attempting to heal element: {element_name}")

        try:
            alternative_locators = self._generate_semantic_alternatives(element_name, locators)
            
            for alt_locator in alternative_locators:
                try:
                    element = self.browser.driver.find_element(alt_locator.loc_type, alt_locator.value)
                    if element and self.browser._is_element_valid(element):
                        logger.info(f"Healing successful: found element using alternative locator: {alt_locator}")
                        return HealingResult(success=True, element=element, message="Element found using semantic alternative")
                except Exception as e:
                    logger.debug(f"Alternative locator failed: {alt_locator}, error: {e}")
                    continue

            if self.screenshot_analysis:
                self._capture_failure_context(element_name)

            self._record_failure(element_name, locators)
            return HealingResult(success=False, message=f"Failed to heal element {element_name} after all attempts")

        except Exception as e:
            logger.error(f"Healing failed with exception: {e}")
            return HealingResult(success=False, message=str(e))
