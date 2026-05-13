import time
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from dataclasses import asdict
from core.browser_adapter import BrowserAdapter, PageElement, Locator
from core.tools import ConfigLoader

logger = logging.getLogger(__name__)


class LearningEngine:
    def __init__(self, browser: BrowserAdapter, config_loader: Optional[ConfigLoader] = None):
        self.browser = browser
        self.config_loader = config_loader or ConfigLoader()
        self.config_loader.load()
        
        self.cache_dir = Path(self.config_loader.get('learning.cache_dir', './logs/learning_cache'))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.learning_enabled = self.config_loader.get('learning.enabled', True)
        self._learned_elements: Dict[str, PageElement] = {}
        
        logger.info("LearningEngine initialized")

    def learn_page_structure(self, page_name: str = "default") -> Dict[str, PageElement]:
        if not self.learning_enabled:
            logger.info("Learning is disabled")
            return {}
        
        logger.info(f"Learning page structure: {page_name}")
        
        try:
            page_source = self.browser.get_page_source()
            current_url = self.browser.get_current_url()
            
            elements = self._analyze_page_structure(page_source)
            self._learned_elements[page_name] = elements
            
            self._save_to_cache(page_name, elements)
            
            logger.info(f"Learned {len(elements)} elements from {page_name}")
            return elements
            
        except Exception as e:
            logger.error(f"Failed to learn page structure: {e}")
            return {}

    def _analyze_page_structure(self, page_source: str) -> Dict[str, PageElement]:
        elements = {}
        
        try:
            from selenium.webdriver.common.by import By
            
            buttons = self.browser.driver.find_elements(By.TAG_NAME, "button")
            for idx, button in enumerate(buttons):
                try:
                    text = button.text.strip()
                    if text:
                        element_name = f"button_{text[:20]}"
                        elements[element_name] = PageElement(
                            name=element_name,
                            element_type="button",
                            learned_at=datetime.now().isoformat(),
                            hit_count=0
                        )
                        elements[element_name].locators.append(
                            Locator(
                                loc_type="xpath",
                                value=f"//button[contains(text(), '{text}')]",
                                description=f"Button: {text}",
                                priority=90
                            )
                        )
                except Exception:
                    pass
            
            inputs = self.browser.driver.find_elements(By.TAG_NAME, "input")
            for idx, input_field in enumerate(inputs):
                try:
                    input_type = input_field.get_attribute('type') or 'text'
                    placeholder = input_field.get_attribute('placeholder') or ''
                    
                    element_name = f"input_{input_type}_{idx}"
                    elements[element_name] = PageElement(
                        name=element_name,
                        element_type=f"input_{input_type}",
                        learned_at=datetime.now().isoformat(),
                        hit_count=0
                    )
                    
                    if placeholder:
                        elements[element_name].locators.append(
                            Locator(
                                loc_type="xpath",
                                value=f"//input[@placeholder='{placeholder}']",
                                description=f"Input: {placeholder}",
                                priority=85
                            )
                        )
                    else:
                        elements[element_name].locators.append(
                            Locator(
                                loc_type="xpath",
                                value=f"//input[@type='{input_type}']",
                                description=f"Input type: {input_type}",
                                priority=80
                            )
                        )
                except Exception:
                    pass
            
            links = self.browser.driver.find_elements(By.TAG_NAME, "a")
            for idx, link in enumerate(links):
                try:
                    href = link.get_attribute('href') or ''
                    text = link.text.strip()
                    
                    if text or href:
                        element_name = f"link_{text[:20] if text else href[:20]}"
                        elements[element_name] = PageElement(
                            name=element_name,
                            element_type="link",
                            learned_at=datetime.now().isoformat(),
                            hit_count=0
                        )
                        
                        if text:
                            elements[element_name].locators.append(
                                Locator(
                                    loc_type="xpath",
                                    value=f"//a[contains(text(), '{text}')]",
                                    description=f"Link: {text}",
                                    priority=85
                                )
                            )
                        if href:
                            elements[element_name].locators.append(
                                Locator(
                                    loc_type="xpath",
                                    value=f"//a[@href='{href}']",
                                    description=f"Link href: {href}",
                                    priority=80
                                )
                            )
                except Exception:
                    pass
                    
        except Exception as e:
            logger.error(f"Error analyzing page structure: {e}")
        
        return elements

    def _save_to_cache(self, page_name: str, elements: Dict[str, PageElement]):
        try:
            cache_file = self.cache_dir / f"{page_name}_elements.json"
            
            serialized = {}
            for name, element in elements.items():
                serialized[name] = {
                    'name': element.name,
                    'element_type': element.element_type,
                    'parent': element.parent,
                    'children': element.children,
                    'learned_at': element.learned_at,
                    'hit_count': element.hit_count,
                    'locators': [
                        {
                            'loc_type': loc.loc_type,
                            'value': loc.value,
                            'description': loc.description,
                            'priority': loc.priority,
                            'last_verified': loc.last_verified
                        }
                        for loc in element.locators
                    ]
                }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(serialized, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved learning cache to {cache_file}")
            
        except Exception as e:
            logger.error(f"Failed to save learning cache: {e}")

    def load_from_cache(self, page_name: str) -> Dict[str, PageElement]:
        try:
            cache_file = self.cache_dir / f"{page_name}_elements.json"
            
            if not cache_file.exists():
                logger.warning(f"No cache found for {page_name}")
                return {}
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            elements = {}
            for name, element_data in data.items():
                locators = [
                    Locator(
                        loc_type=loc['loc_type'],
                        value=loc['value'],
                        description=loc.get('description', ''),
                        priority=loc.get('priority', 0),
                        last_verified=loc.get('last_verified')
                    )
                    for loc in element_data.get('locators', [])
                ]
                
                elements[name] = PageElement(
                    name=element_data['name'],
                    element_type=element_data.get('element_type', 'unknown'),
                    parent=element_data.get('parent'),
                    children=element_data.get('children', []),
                    learned_at=element_data.get('learned_at'),
                    hit_count=element_data.get('hit_count', 0)
                )
                elements[name].locators = locators
            
            logger.info(f"Loaded {len(elements)} elements from cache")
            return elements
            
        except Exception as e:
            logger.error(f"Failed to load learning cache: {e}")
            return {}

    def get_learned_element(self, element_name: str) -> Optional[PageElement]:
        return self._learned_elements.get(element_name)

    def increment_hit_count(self, element_name: str):
        if element_name in self._learned_elements:
            self._learned_elements[element_name].hit_count += 1
            logger.debug(f"Hit count for {element_name}: {self._learned_elements[element_name].hit_count}")

    def clear_cache(self):
        try:
            for cache_file in self.cache_dir.glob("*_elements.json"):
                cache_file.unlink()
            self._learned_elements.clear()
            logger.info("Learning cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
