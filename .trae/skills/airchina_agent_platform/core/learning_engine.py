import os
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import asdict, dataclass, field
from datetime import datetime
import yaml

from .browser_adapter import BrowserAdapter, Locator, PageElement

logger = logging.getLogger(__name__)


@dataclass
class LearnedPage:
    url: str
    page_name: str
    elements: Dict[str, PageElement] = field(default_factory=dict)
    menus: List[Dict] = field(default_factory=list)
    buttons: List[Dict] = field(default_factory=list)
    forms: List[Dict] = field(default_factory=list)
    learned_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1


class LearningEngine:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, browser_adapter: Optional[BrowserAdapter] = None, config_path: Optional[str] = None):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.browser = browser_adapter or BrowserAdapter(config_path)
        self.config = self._load_config(config_path)
        self.cache_dir = Path(self.config.get('learning', {}).get('cache_dir', './logs/learning_cache'))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._learned_pages: Dict[str, LearnedPage] = {}
        self._current_page: Optional[LearnedPage] = None

        self._load_learned_data()
        logger.info("LearningEngine initialized")

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"

        if isinstance(config_path, str):
            config_path = Path(config_path)

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def _load_learned_data(self):
        cache_file = self.cache_dir / "learned_pages.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for url, page_data in data.items():
                        self._learned_pages[url] = self._deserialize_page(page_data)
                logger.info(f"Loaded {len(self._learned_pages)} learned pages from cache")
            except Exception as e:
                logger.warning(f"Failed to load learned data: {e}")

    def _serialize_page(self, page: LearnedPage) -> Dict:
        return {
            'url': page.url,
            'page_name': page.page_name,
            'elements': {k: asdict(v) for k, v in page.elements.items()},
            'menus': page.menus,
            'buttons': page.buttons,
            'forms': page.forms,
            'learned_at': page.learned_at,
            'version': page.version
        }

    def _deserialize_page(self, data: Dict) -> LearnedPage:
        elements = {}
        for k, v in data.get('elements', {}).items():
            locators = [Locator(**loc) for loc in v.get('locators', [])]
            elements[k] = PageElement(
                name=v['name'],
                locators=locators,
                element_type=v.get('element_type', 'unknown'),
                parent=v.get('parent'),
                children=v.get('children', []),
                learned_at=v.get('learned_at'),
                hit_count=v.get('hit_count', 0)
            )

        return LearnedPage(
            url=data['url'],
            page_name=data['page_name'],
            elements=elements,
            menus=data.get('menus', []),
            buttons=data.get('buttons', []),
            forms=data.get('forms', []),
            learned_at=data.get('learned_at', ''),
            version=data.get('version', 1)
        )

    def _save_learned_data(self):
        cache_file = self.cache_dir / "learned_pages.json"
        try:
            data = {url: self._serialize_page(page) for url, page in self._learned_pages.items()}
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("Learned data saved to cache")
        except Exception as e:
            logger.error(f"Failed to save learned data: {e}")

    def learn_current_page(self, page_name: Optional[str] = None) -> LearnedPage:
        if not self.browser.driver:
            raise RuntimeError("Browser driver not initialized")

        url = self.browser.get_current_url()
        page_name = page_name or self._extract_page_name(url)

        logger.info(f"Learning page: {page_name} ({url})")

        learned_page = LearnedPage(url=url, page_name=page_name)

        learned_page.menus = self._learn_navigation_menus()
        learned_page.buttons = self._learn_buttons()
        learned_page.forms = self._learn_forms()
        learned_page.elements = self._learn_interactive_elements()

        self._learned_pages[url] = learned_page
        self._current_page = learned_page
        self._save_learned_data()

        logger.info(f"Page learning completed. Found {len(learned_page.elements)} elements")
        return learned_page

    def _extract_page_name(self, url: str) -> str:
        try:
            path = url.split('/agent/base/desktop')[1] if '/agent/base/desktop' in url else url
            return path.strip('/').replace('/', '_') or 'home'
        except:
            return 'unknown'

    def _learn_navigation_menus(self) -> List[Dict]:
        menus = []
        try:
            menu_selectors = [
                "//nav//a",
                "//*[contains(@class, 'menu')]//a",
                "//*[contains(@class, 'nav')]//*[contains(@class, 'item')]",
                "//aside//a",
                "//*[contains(@role, 'navigation')]//a"
            ]

            for selector in menu_selectors:
                try:
                    elements = self.browser.driver.find_elements("xpath", selector)
                    for el in elements:
                        try:
                            text = el.text.strip()
                            href = el.get_attribute('href') or ''
                            if text and len(text) < 50:
                                menus.append({
                                    'text': text,
                                    'href': href,
                                    'locator': selector
                                })
                        except:
                            continue
                except:
                    continue

        except Exception as e:
            logger.warning(f"Failed to learn menus: {e}")

        return menus

    def _learn_buttons(self) -> List[Dict]:
        buttons = []
        try:
            button_selectors = [
                "//button",
                "//*[contains(@class, 'btn')]",
                "//*[contains(@class, 'button')]",
                "//a[contains(@class, 'btn')]",
                "//input[@type='button']",
                "//input[@type='submit']"
            ]

            for selector in button_selectors:
                try:
                    elements = self.browser.driver.find_elements("xpath", selector)
                    for el in elements:
                        try:
                            text = el.text.strip()
                            class_name = el.get_attribute('class') or ''
                            disabled = el.get_attribute('disabled')

                            if text or 'btn' in class_name.lower():
                                buttons.append({
                                    'text': text,
                                    'class': class_name,
                                    'disabled': disabled is not None,
                                    'locator': selector
                                })
                        except:
                            continue
                except:
                    continue

        except Exception as e:
            logger.warning(f"Failed to learn buttons: {e}")

        return buttons

    def _learn_forms(self) -> List[Dict]:
        forms = []
        try:
            form_selectors = [
                "//form",
                "//*[contains(@class, 'form')]",
                "//*[contains(@role, 'form')]"
            ]

            for selector in form_selectors:
                try:
                    elements = self.browser.driver.find_elements("xpath", selector)
                    for el in elements:
                        try:
                            inputs = el.find_elements("xpath", ".//input | .//textarea | .//select")
                            form_data = {
                                'tag': el.tag_name,
                                'class': el.get_attribute('class') or '',
                                'inputs': []
                            }

                            for inp in inputs:
                                form_data['inputs'].append({
                                    'name': inp.get_attribute('name') or '',
                                    'id': inp.get_attribute('id') or '',
                                    'type': inp.get_attribute('type') or 'text',
                                    'placeholder': inp.get_attribute('placeholder') or '',
                                    'locator': f"//input[@name='{inp.get_attribute('name')}']" if inp.get_attribute('name') else ''
                                })

                            if form_data['inputs']:
                                forms.append(form_data)
                        except:
                            continue
                except:
                    continue

        except Exception as e:
            logger.warning(f"Failed to learn forms: {e}")

        return forms

    def _learn_interactive_elements(self) -> Dict[str, PageElement]:
        elements = {}

        try:
            interactive_tags = ['a', 'button', 'input', 'select', 'textarea']
            for tag in interactive_tags:
                try:
                    els = self.browser.driver.find_elements("xpath", f"//{tag}")
                    for el in els:
                        try:
                            name = self._generate_element_name(el, tag)
                            if name and name not in elements:
                                locators = self._generate_locators(el, name)
                                elements[name] = PageElement(
                                    name=name,
                                    locators=locators,
                                    element_type=tag,
                                    learned_at=datetime.now().isoformat()
                                )
                        except:
                            continue
                except:
                    continue

        except Exception as e:
            logger.warning(f"Failed to learn interactive elements: {e}")

        return elements

    def _generate_element_name(self, el, tag: str) -> Optional[str]:
        try:
            text = el.text.strip()
            if text and len(text) < 100:
                return text[:50]

            aria_label = el.get_attribute('aria-label')
            if aria_label:
                return aria_label[:50]

            placeholder = el.get_attribute('placeholder')
            if placeholder:
                return placeholder[:50]

            name = el.get_attribute('name')
            if name:
                return name[:50]

            id_val = el.get_attribute('id')
            if id_val:
                return id_val[:50]

            href = el.get_attribute('href')
            if href:
                return href.split('/')[-1][:50]

            return None
        except:
            return None

    def _generate_locators(self, el, name: str) -> List[Locator]:
        locators = []

        try:
            id_val = el.get_attribute('id')
            if id_val:
                locators.append(Locator(
                    loc_type='id',
                    value=id_val,
                    description=f"ID for {name}",
                    priority=100
                ))
        except:
            pass

        try:
            name_val = el.get_attribute('name')
            if name_val:
                locators.append(Locator(
                    loc_type='name',
                    value=name_val,
                    description=f"Name for {name}",
                    priority=90
                ))
        except:
            pass

        try:
            class_val = el.get_attribute('class')
            if class_val:
                class_name = class_val.strip().split()[0]
                if class_name:
                    locators.append(Locator(
                        loc_type='class',
                        value=class_name,
                        description=f"Class for {name}",
                        priority=70
                    ))
        except:
            pass

        try:
            if el.text.strip():
                locators.append(Locator(
                    loc_type='xpath',
                    value=f"//*[contains(text(), '{el.text.strip()[:30]}')]",
                    description=f"Text contains for {name}",
                    priority=80
                ))
        except:
            pass

        try:
            tag = el.tag_name
            locators.append(Locator(
                loc_type='xpath',
                value=f"//{tag}[@aria-label='{el.get_attribute('aria-label') or ''}']",
                description=f"Tag with aria-label for {name}",
                priority=60
            ))
        except:
            pass

        return locators

    def find_learned_element(self, name: str) -> Optional[PageElement]:
        if self._current_page:
            return self._current_page.elements.get(name)

        for page in self._learned_pages.values():
            if name in page.elements:
                return page.elements[name]

        return None

    def update_element_locator(self, page_url: str, element_name: str, new_locator: Locator):
        if page_url in self._learned_pages:
            page = self._learned_pages[page_url]
            if element_name in page.elements:
                element = page.elements[element_name]
                for loc in element.locators:
                    if loc.loc_type == new_locator.loc_type:
                        loc.value = new_locator.value
                        loc.last_verified = datetime.now().isoformat()
                        break
                else:
                    element.locators.append(new_locator)

                element.hit_count += 1
                page.version += 1
                self._save_learned_data()
                logger.info(f"Updated locator for {element_name} on {page_url}")

    def get_learned_page(self, url: str) -> Optional[LearnedPage]:
        return self._learned_pages.get(url)

    def has_learned_page(self, url: str) -> bool:
        return url in self._learned_pages

    def get_all_learned_pages(self) -> List[str]:
        return list(self._learned_pages.keys())

    def relearn_page(self, url: Optional[str] = None):
        url = url or self.browser.get_current_url()
        if url in self._learned_pages:
            logger.info(f"Relearning page: {url}")
            self.browser.navigate(url)
            time.sleep(2)
            self.learn_current_page()
        else:
            logger.warning(f"Page not found in learned pages: {url}")

    def export_knowledge(self, output_path: str):
        with open(output_path, 'w', encoding='utf-8') as f:
            data = {url: self._serialize_page(page) for url, page in self._learned_pages.items()}
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Knowledge exported to {output_path}")

    def import_knowledge(self, input_path: str):
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for url, page_data in data.items():
                    self._learned_pages[url] = self._deserialize_page(page_data)
            self._save_learned_data()
            logger.info(f"Knowledge imported from {input_path}")
        except Exception as e:
            logger.error(f"Failed to import knowledge: {e}")
