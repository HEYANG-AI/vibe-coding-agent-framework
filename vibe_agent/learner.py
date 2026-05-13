"""
自学习引擎 - 自主分析页面 DOM，构建页面交互模型

核心能力：
1. 扫描页面所有可交互元素（按钮、输入框、下拉框、弹窗等）
2. 构建页面结构树（菜单层级、页面布局）
3. 为每个元素生成多策略选择器
4. 持久化存储页面模型到本地
5. 检测 UI 变化并自动适配
"""

import json
import time
import re
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field, asdict

from playwright.sync_api import Page


@dataclass
class ElementInfo:
    """页面元素信息"""
    tag: str
    text: str = ""
    placeholder: str = ""
    element_id: str = ""
    class_name: str = ""
    name: str = ""
    type: str = ""
    href: str = ""
    data_testid: str = ""
    data_test: str = ""
    aria_label: str = ""
    role: str = ""
    rect: Optional[dict] = None
    selector_css: str = ""
    selector_text: str = ""
    selector_xpath: str = ""
    selector_testid: str = ""
    is_visible: bool = True
    parent_tags: list[str] = field(default_factory=list)
    siblings_text: list[str] = field(default_factory=list)


@dataclass
class PageRegion:
    """页面区域定义"""
    name: str
    selector: str
    element_type: str  # menu, form, dialog, table, canvas, panel, button-group
    elements: list[ElementInfo] = field(default_factory=list)
    confidence: float = 1.0  # 识别置信度


@dataclass
class PageModel:
    """完整页面模型"""
    url: str
    title: str
    page_type: str  # login, dashboard, agent-list, agent-create, workflow, publish
    regions: list[PageRegion] = field(default_factory=list)
    learned_at: float = field(default_factory=time.time)
    version: int = 1


class PageLearner:
    """
    页面自学习引擎。
    访问页面 -> 分析 DOM -> 构建模型 -> 持久化存储。
    """

    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = Path(model_dir or Path.home() / ".vibe" / "page_models")
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self._model_cache: dict[str, PageModel] = {}

    # ========== 核心学习流程 ==========

    def learn_page(self, page: Page, page_type: Optional[str] = None) -> PageModel:
        """
        学习当前页面，构建页面模型。
        page_type 提示（login, dashboard 等），为 None 则自动检测。
        """
        url = page.url
        title = page.title()

        if page_type is None:
            page_type = self._detect_page_type(url, title, page)

        # 提取页面上所有交互元素
        elements = self._extract_all_elements(page)

        # 聚类元素到区域
        regions = self._cluster_into_regions(page, elements, page_type)

        # 为每个元素生成选择器
        for region in regions:
            for el in region.elements:
                selectors = self._generate_selectors(el)
                el.selector_css = selectors.get("css", "")
                el.selector_text = selectors.get("text", "")
                el.selector_xpath = selectors.get("xpath", "")
                el.selector_testid = selectors.get("testid", "")

        model = PageModel(
            url=url,
            title=title,
            page_type=page_type,
            regions=regions,
        )

        self._save_model(model)
        self._model_cache[page_type] = model
        return model

    def learn_navigation(self, page: Page) -> dict[str, str]:
        """
        学习导航结构。
        遍历菜单/侧边栏，构建页面导航映射。
        返回 {菜单名称: 跳转URL/选择器}
        """
        navigation_map = {}

        # 常见的导航元素选择器
        nav_selectors = [
            "nav a", ".menu a", ".sidebar a", ".nav a",
            ".el-menu a", ".ant-menu a", "[role='menuitem']",
            ".tabs a", ".tab a", "header a",
        ]

        for selector in nav_selectors:
            try:
                links = page.query_selector_all(selector)
                for link in links:
                    try:
                        text = link.inner_text().strip()
                        href = link.get_attribute("href") or ""
                        if text and href and len(text) < 50:
                            navigation_map[text] = href
                    except Exception:
                        continue
            except Exception:
                continue

        return navigation_map

    def detect_ui_changes(self, page: Page, known_model: PageModel) -> list[dict]:
        """
        检测 UI 变化。对比已知模型和当前页面。
        返回变更列表 [{type: 'added'|'removed'|'changed', element: ..., detail: ...}]
        """
        changes = []
        current_elements = self._extract_all_elements(page)
        known_elements = []
        for region in known_model.regions:
            known_elements.extend(region.elements)

        # 将已知元素转索引
        known_map = {}
        for el in known_elements:
            key = f"{el.tag}:{el.text[:30]}:{el.name}:{el.element_id}"
            known_map[key] = el

        current_map = {}
        for el in current_elements:
            key = f"{el.tag}:{el.text[:30]}:{el.name}:{el.element_id}"
            current_map[key] = el

        # 检查移除的元素
        for key, el in known_map.items():
            if key not in current_map:
                changes.append({
                    "type": "removed",
                    "element": asdict(el),
                    "detail": f"元素 '{el.text or el.name or el.tag}' 已不存在",
                })

        # 检查新增元素
        for key, el in current_elements[:len(current_elements)]:
            key = f"{el.tag}:{el.text[:30]}:{el.name}:{el.element_id}"
            if key not in known_map:
                changes.append({
                    "type": "added",
                    "element": asdict(el),
                    "detail": f"新增元素 '{el.text or el.name or el.tag}'",
                })

        return changes

    def adapt_to_changes(self, page: Page, known_model: PageModel) -> PageModel:
        """检测变化并自动适配，返回更新后的模型"""
        changes = self.detect_ui_changes(page, known_model)
        if changes:
            new_model = self.learn_page(page, known_model.page_type)
            new_model.version = known_model.version + 1
            self._save_model(new_model)
            return new_model
        return known_model

    # ========== 页面类型检测 ==========

    def _detect_page_type(self, url: str, title: str, page: Page) -> str:
        """自动检测页面类型"""
        url_lower = url.lower()
        title_lower = title.lower()

        # 基于 URL 模式
        if any(k in url_lower for k in ["login", "signin", "auth", "sso"]):
            return "login"
        if any(k in url_lower for k in ["workflow", "flow", "pipeline"]):
            return "workflow"
        if any(k in url_lower for k in ["publish", "deploy", "release"]):
            return "publish"

        # 基于页面标题
        if any(k in title_lower for k in ["登录", "login", "认证"]):
            return "login"
        if any(k in title_lower for k in ["工作流", "流程编辑"]) or "workflow" in title_lower:
            return "workflow"

        # 基于按钮文本检测
        body_text = page.inner_text("body").lower()
        if any(k in body_text for k in ["登录", "密码", "忘记密码"]):
            return "login"
        if any(k in body_text for k in ["工作流", "画布", "节点", "连接"]):
            return "workflow"
        if any(k in body_text for k in ["发布", "上线", "部署版本"]):
            return "publish"
        if any(k in body_text for k in ["创建agent", "创建智能体", "新建agent", "新建机器人"]):
            return "agent-create"
        if any(k in body_text for k in ["agent列表", "智能体列表", "我的agent", "机器人管理"]):
            return "agent-list"

        # 检测登录表单
        if page.query_selector("input[type='password']"):
            return "login"

        return "dashboard"

    # ========== 元素提取 ==========

    def _extract_all_elements(self, page: Page) -> list[ElementInfo]:
        """提取页面所有交互元素"""
        elements = []

        # 核心交互元素选择器
        selector_patterns = [
            "button", "input", "textarea", "select",
            "a[href]", "[role='button']", "[role='tab']", "[role='menuitem']",
            "[role='checkbox']", "[role='radio']", "[role='switch']",
            "[class*='btn']", "[class*='button']", "[class*='menu-item']",
            "[class*='tab']", "[class*='node']", "[class*='widget']",
            ".el-button", ".ant-btn", ".el-menu-item", ".ant-menu-item",
            ".el-tab", ".ant-tabs-tab", ".el-dialog", ".ant-modal",
            ".el-select", ".ant-select", ".el-switch", ".ant-switch",
            "[data-testid]", "[data-test]",
        ]

        seen = set()
        for pattern in selector_patterns:
            try:
                handles = page.query_selector_all(pattern)
                for handle in handles:
                    try:
                        elem = self._extract_element_info(handle)
                        # 去重
                        dedup_key = f"{elem.tag}:{elem.text[:50]}:{elem.name}:{elem.element_id}"
                        if dedup_key not in seen and elem.text != "...":
                            seen.add(dedup_key)
                            elements.append(elem)
                    except Exception:
                        continue
            except Exception:
                continue

        return elements

    def _extract_element_info(self, handle) -> ElementInfo:
        """从 DOM 句柄提取元素信息"""
        info = handle.evaluate("""el => {
            const rect = el.getBoundingClientRect();
            const getParents = (node, depth=0) => {
                if (!node || depth > 5) return [];
                const parent = node.parentElement;
                if (!parent) return [];
                return [parent.tagName.toLowerCase(), ...getParents(parent, depth+1)];
            };
            const siblings = el.parentElement
                ? Array.from(el.parentElement.children)
                    .filter(c => c !== el && c.textContent)
                    .map(c => c.textContent.trim().substring(0, 30))
                    .filter(t => t)
                : [];
            return {
                tag: el.tagName.toLowerCase(),
                text: (el.textContent || '').trim().substring(0, 100),
                placeholder: el.placeholder || el.getAttribute('placeholder') || '',
                id: el.id || '',
                className: el.className || '',
                name: el.name || el.getAttribute('name') || '',
                type: el.type || el.getAttribute('type') || '',
                href: el.href || el.getAttribute('href') || '',
                dataTestid: el.getAttribute('data-testid') || el.getAttribute('data-test') || '',
                dataTest: el.getAttribute('data-test') || '',
                ariaLabel: el.getAttribute('aria-label') || '',
                role: el.getAttribute('role') || '',
                rect: {top: rect.top, left: rect.left, width: rect.width, height: rect.height},
                isVisible: rect.width > 0 && rect.height > 0,
                parentTags: getParents(el),
                siblingsText: siblings,
            };
        }""")

        return ElementInfo(
            tag=info["tag"],
            text=info["text"],
            placeholder=info["placeholder"],
            element_id=info["id"],
            class_name=str(info["className"]),
            name=info["name"],
            type=info["type"],
            href=info["href"],
            data_testid=info["dataTestid"],
            data_test=info["dataTest"],
            aria_label=info["ariaLabel"],
            role=info["role"],
            rect=info["rect"],
            is_visible=info["isVisible"],
            parent_tags=info["parentTags"],
            siblings_text=info["siblingsText"],
        )

    # ========== 区域聚类 ==========

    def _cluster_into_regions(self, page: Page, elements: list[ElementInfo], page_type: str) -> list[PageRegion]:
        """将元素聚类到功能区域"""
        regions = []
        unassigned = list(elements)

        # 根据页面类型定义区域模式
        region_patterns = self._get_region_patterns(page_type)

        for pattern in region_patterns:
            matched = []
            remaining = []
            for el in unassigned:
                if self._matches_region(el, pattern):
                    matched.append(el)
                else:
                    remaining.append(el)

            if matched:
                regions.append(PageRegion(
                    name=pattern["name"],
                    selector=pattern.get("selector", ""),
                    element_type=pattern["type"],
                    elements=matched,
                ))
            unassigned = remaining

        # 剩余元素归类到"其他"
        if unassigned:
            regions.append(PageRegion(
                name="其他",
                selector="",
                element_type="other",
                elements=unassigned,
                confidence=0.5,
            ))

        return regions

    def _get_region_patterns(self, page_type: str) -> list[dict]:
        """获取指定页面类型的区域模式"""
        patterns = {
            "login": [
                {"name": "登录表单", "type": "form", "selector": "form, .login-form, [class*='login']",
                 "matchers": [{"attr": "type", "value": "password"}, {"attr": "placeholder", "pattern": "密码|用户|账号|验证"}]},
                {"name": "登录按钮", "type": "button-group", "selector": "button:has-text('登录'), .login-btn",
                 "matchers": [{"attr": "text", "pattern": "登录|登 录|注册|sign"}]},
                {"name": "SSO区域", "type": "button-group", "selector": "text=SSO, text=企业登录",
                 "matchers": [{"attr": "text", "pattern": "SSO|企业登录|统一认证"}]},
            ],
            "dashboard": [
                {"name": "主导航", "type": "menu", "selector": "nav, .sidebar, .menu, aside, .el-menu",
                 "matchers": [{"attr": "tag", "value": "nav"}, {"attr": "class", "pattern": "sidebar|menu|nav|aside"}]},
                {"name": "页面标题", "type": "panel", "selector": "h1, h2, .page-title",
                 "matchers": [{"attr": "tag", "value": "h1"}, {"attr": "tag", "value": "h2"}]},
                {"name": "操作区域", "type": "button-group", "selector": ".actions, .toolbar, [class*='action']",
                 "matchers": [{"attr": "class", "pattern": "action|toolbar|header"}]},
            ],
            "agent-list": [
                {"name": "列表区域", "type": "table", "selector": "table, .el-table, .list, [class*='list']",
                 "matchers": [{"attr": "tag", "value": "table"}, {"attr": "class", "pattern": "table|list"}]},
                {"name": "搜索过滤", "type": "form", "selector": ".search, .filter, [class*='search']",
                 "matchers": [{"attr": "placeholder", "pattern": "搜索|查找|过滤"}]},
                {"name": "创建按钮", "type": "button-group", "selector": "button:has-text('创建'), .create-btn",
                 "matchers": [{"attr": "text", "pattern": "创建|新建|添加"}]},
            ],
            "agent-create": [
                {"name": "创建表单", "type": "form", "selector": "form, .el-form, [class*='form']",
                 "matchers": [{"attr": "class", "pattern": "form"}, {"attr": "placeholder", "pattern": "名称|描述|名字"}]},
                {"name": "提交按钮", "type": "button-group", "selector": "button:has-text('确定'), button:has-text('创建')",
                 "matchers": [{"attr": "text", "pattern": "确定|创建|保存"}]},
            ],
            "workflow": [
                {"name": "节点面板", "type": "panel", "selector": "[class*='node-palette'], [class*='widget'], [class*='component-list']",
                 "matchers": [{"attr": "class", "pattern": "node|widget|component|palette"}]},
                {"name": "画布区域", "type": "canvas", "selector": ".workflow-canvas, .flow-canvas, #canvas, [class*='flow']",
                 "matchers": [{"attr": "class", "pattern": "canvas|flow|workflow"}]},
                {"name": "配置面板", "type": "panel", "selector": "[class*='config'], [class*='property'], [class*='setting']",
                 "matchers": [{"attr": "class", "pattern": "config|property|setting"}]},
                {"name": "操作栏", "type": "button-group", "selector": ".toolbar, [class*='toolbar'], .actions",
                 "matchers": [{"attr": "text", "pattern": "保存|发布|撤销|重做"}]},
            ],
        }
        return patterns.get(page_type, patterns["dashboard"])

    def _matches_region(self, element: ElementInfo, pattern: dict) -> bool:
        """判断元素是否匹配区域模式"""
        if "matchers" not in pattern:
            return False

        for matcher in pattern["matchers"]:
            attr = matcher.get("attr", "")
            value = matcher.get("value", "")
            pattern_str = matcher.get("pattern", "")

            element_value = ""
            if attr == "tag":
                element_value = element.tag
            elif attr == "text":
                element_value = element.text
            elif attr == "class":
                element_value = element.class_name
            elif attr == "placeholder":
                element_value = element.placeholder
            elif attr == "name":
                element_value = element.name
            elif attr == "type":
                element_value = element.type
            elif attr == "id":
                element_value = element.element_id

            if value and value in element_value:
                return True
            if pattern_str and re.search(pattern_str, element_value, re.IGNORECASE):
                return True

        return False

    # ========== 选择器生成 ==========

    def _generate_selectors(self, element: ElementInfo) -> dict[str, str]:
        """为元素生成多种策略的选择器"""
        selectors = {}

        # data-testid 优先（最稳定）
        if element.data_testid:
            selectors["testid"] = f"[data-testid='{element.data_testid}']"
        elif element.data_test:
            selectors["testid"] = f"[data-test='{element.data_test}']"

        # ID 选择器
        if element.element_id:
            selectors["css"] = f"#{element.element_id}"

        # 文本选择器（最人类可读）
        if element.text and len(element.text) < 60:
            escaped = element.text.replace("'", "\\'")
            selectors["text"] = f"text='{escaped}'"

        # CSS class + tag
        if element.class_name:
            classes = element.class_name.replace(".", "").split()
            class_selector = ".".join(classes[:3])
            selectors["css"] = selectors.get("css", "") or f"{element.tag}.{class_selector}"

        # placeholder
        if element.placeholder:
            selectors["css"] = f"[placeholder='{element.placeholder}']"

        # 组合选择器
        if element.name:
            selectors["css"] = f"{element.tag}[name='{element.name}']"

        # XPath（fallback）
        text_condition = ""
        if element.text and len(element.text) < 60:
            text_condition = f"[contains(text(),'{element.text[:30]}')]"
        elif element.placeholder:
            text_condition = f"[@placeholder='{element.placeholder}']"

        selectors["xpath"] = f"//{element.tag}{text_condition}"

        return selectors

    # ========== 持久化 ==========

    def _save_model(self, model: PageModel):
        """保存页面模型到磁盘"""
        path = self.model_dir / f"{model.page_type}.json"
        data = {
            "url": model.url,
            "title": model.title,
            "page_type": model.page_type,
            "learned_at": model.learned_at,
            "version": model.version,
            "regions": [
                {
                    "name": r.name,
                    "selector": r.selector,
                    "element_type": r.element_type,
                    "confidence": r.confidence,
                    "elements": [asdict(e) for e in r.elements],
                }
                for r in model.regions
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_model(self, page_type: str) -> Optional[PageModel]:
        """加载已保存的页面模型"""
        path = self.model_dir / f"{page_type}.json"
        if not path.exists():
            return None
        if page_type in self._model_cache:
            return self._model_cache[page_type]

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        regions = [
            PageRegion(
                name=r["name"],
                selector=r.get("selector", ""),
                element_type=r["element_type"],
                confidence=r.get("confidence", 1.0),
                elements=[ElementInfo(**e) for e in r.get("elements", [])],
            )
            for r in data.get("regions", [])
        ]

        model = PageModel(
            url=data["url"],
            title=data["title"],
            page_type=data["page_type"],
            regions=regions,
            learned_at=data.get("learned_at", 0),
            version=data.get("version", 1),
        )
        self._model_cache[page_type] = model
        return model

    def get_learned_pages(self) -> list[str]:
        """获取已学习的页面类型列表"""
        return [p.stem for p in self.model_dir.glob("*.json")]

    def get_best_selector(self, element: ElementInfo, page_type: str) -> str:
        """获取元素的最佳选择器（按优先级）"""
        # 优先级: testid > text > id > css > xpath
        if element.data_testid:
            return f"[data-testid='{element.data_testid}']"
        if element.data_test:
            return f"[data-test='{element.data_test}']"
        if element.text and len(element.text) < 60:
            return f"text={element.text}"
        if element.element_id:
            return f"#{element.element_id}"
        if element.name:
            return f"{element.tag}[name='{element.name}']"
        if element.placeholder:
            return f"[placeholder='{element.placeholder}']"
        if element.class_name:
            cls = element.class_name.replace(".", "").split()[0]
            return f"{element.tag}.{cls}"
        return element.selector_xpath or f"//{element.tag}"

    # ========== 交互发现模式 ==========

    def discover_interactive_map(self, page: Page) -> dict:
        """
        完整发现页面交互地图。
        返回整个页面结构，包括：
        - 所有可点击元素
        - 所有输入框
        - 菜单层级
        - 弹窗/对话框
        """
        return {
            "url": page.url,
            "title": page.title(),
            "inputs": self._discover_inputs(page),
            "buttons": self._discover_buttons(page),
            "menus": self._discover_menus(page),
            "dialogs": self._discover_dialogs(page),
            "canvas": self._discover_canvas(page),
        }

    def _discover_inputs(self, page: Page) -> list[dict]:
        """发现所有输入类元素"""
        inputs = []
        for handle in page.query_selector_all("input, textarea, select"):
            try:
                info = handle.evaluate("""el => ({
                    tag: el.tagName.toLowerCase(),
                    type: el.type || el.getAttribute('type') || '',
                    name: el.name || '',
                    placeholder: el.placeholder || '',
                    id: el.id || '',
                    className: el.className || '',
                    required: el.required || false,
                    disabled: el.disabled || false,
                    rect: el.getBoundingClientRect(),
                })""")
                info["selectors"] = self._generate_selectors(ElementInfo(
                    tag=info["tag"], element_id=info["id"], name=info["name"],
                    placeholder=info["placeholder"], class_name=info["className"],
                    type=info["type"],
                ))
                inputs.append(info)
            except Exception:
                continue
        return inputs

    def _discover_buttons(self, page: Page) -> list[dict]:
        """发现所有可点击元素"""
        buttons = []
        for handle in page.query_selector_all("button, a[href], [role='button'], [onclick], [class*='btn'], [class*='button']"):
            try:
                text = handle.inner_text().strip()
                if not text:
                    continue
                buttons.append({
                    "text": text[:80],
                    "selector": f"text={text}",
                    "visible": handle.is_visible(),
                    "tag": handle.evaluate("el => el.tagName.toLowerCase()"),
                })
            except Exception:
                continue
        return buttons

    def _discover_menus(self, page: Page) -> list[dict]:
        """发现菜单结构"""
        menus = []
        menu_containers = page.query_selector_all(
            "nav, .menu, .sidebar, .el-menu, .ant-menu, [role='navigation'], [role='menubar']"
        )
        for container in menu_containers:
            try:
                items = container.query_selector_all("a, [role='menuitem'], .el-menu-item, .ant-menu-item, li")
                menu_items = []
                for item in items:
                    try:
                        text = item.inner_text().strip()
                        href = item.get_attribute("href") or ""
                        if text and len(text) < 50:
                            menu_items.append({"text": text, "href": href})
                    except Exception:
                        continue
                if menu_items:
                    menus.append({"items": menu_items})
            except Exception:
                continue
        return menus

    def _discover_dialogs(self, page: Page) -> list[dict]:
        """发现弹窗/对话框"""
        dialogs = []
        for handle in page.query_selector_all(".el-dialog, .ant-modal, .modal, .dialog, [role='dialog']"):
            try:
                visible = handle.is_visible()
                title_el = handle.query_selector(".el-dialog__title, .ant-modal-title, .modal-title, h3, h4")
                title = title_el.inner_text().strip() if title_el else ""
                buttons = []
                for btn in handle.query_selector_all("button, .el-button, .ant-btn"):
                    try:
                        buttons.append(btn.inner_text().strip()[:30])
                    except Exception:
                        continue
                dialogs.append({
                    "visible": visible,
                    "title": title,
                    "buttons": buttons,
                })
            except Exception:
                continue
        return dialogs

    def _discover_canvas(self, page: Page) -> Optional[dict]:
        """发现工作流画布"""
        for selector in [".workflow-canvas", ".flow-canvas", "#canvas", ".vue-flow", ".react-flow", "[class*='flow']"]:
            handle = page.query_selector(selector)
            if handle:
                try:
                    return {
                        "selector": selector,
                        "size": handle.evaluate("el => ({w: el.clientWidth, h: el.clientHeight})"),
                        "nodes": self._discover_canvas_nodes(page),
                    }
                except Exception:
                    continue
        return None

    def _discover_canvas_nodes(self, page: Page) -> list[dict]:
        """发现画布上的节点"""
        nodes = []
        for selector in [".vue-flow__node", ".react-flow__node", ".node", "[class*='node']"]:
            for handle in page.query_selector_all(selector):
                try:
                    text = handle.inner_text().strip()[:50]
                    rect = handle.evaluate("el => el.getBoundingClientRect()")
                    nodes.append({
                        "text": text,
                        "position": {"x": rect["x"], "y": rect["y"]},
                    })
                except Exception:
                    continue
        return nodes
