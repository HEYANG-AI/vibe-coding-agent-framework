"""
工作流搭建流程 — 全自动工作流编排
====================================
支持: 添加节点、连接节点、配置参数、保存工作流
"""

import json
import re
from typing import Optional, Any

from core.browser import BrowserManager
from core.engine import Config
from core.learner import PageLearner

# 节点类型 → 界面标签映射
NODE_TYPE_LABELS = {
    "start": ["开始", "Start", "开始节点"],
    "end": ["结束", "End", "结束节点"],
    "llm": ["LLM", "大模型", "语言模型", "AI对话", "Chat"],
    "code": ["代码", "Code", "Python", "JavaScript", "JS"],
    "condition": ["条件", "Condition", "判断", "IF", "分支", "Branch"],
    "api": ["API", "接口", "HTTP请求", "HTTP"],
    "knowledge": ["知识库", "Knowledge", "知识检索", "RAG", "检索"],
    "input": ["用户输入", "Input", "用户消息"],
    "output": ["回复", "Output", "输出", "消息回复"],
    "tool": ["工具", "Function", "函数调用", "Tool"],
    "switch": ["Switch", "选择"],
    "loop": ["循环", "Loop"],
    "webhook": ["Webhook"],
    "timer": ["定时", "Timer", "延迟"],
    "database": ["数据库", "DB", "数据查询"],
    "email": ["邮件", "Email"],
}

# 配置键 → 界面标签映射
CONFIG_KEY_MAP = {
    "model": ["模型", "Model", "LLM模型", "AI模型"],
    "temperature": ["温度", "Temperature", "随机性", "创造性"],
    "system_prompt": ["系统提示词", "System Prompt", "提示词", "系统指令", "角色设定"],
    "user_prompt": ["用户提示词", "User Prompt", "用户指令"],
    "max_tokens": ["最大Token", "Max Tokens", "最大长度", "Token上限"],
    "top_p": ["Top P", "核采样"],
    "knowledge_base": ["知识库", "Knowledge Base"],
    "top_k": ["Top K", "返回数量"],
    "description": ["描述", "Description"],
    "label": ["名称", "Label", "显示名称"],
}


def run_build_workflow(preset: str = "", flow: Optional[list] = None,
                       agent_id: str = "", headless: Optional[bool] = None):
    """CLI 入口: 搭建工作流"""
    from core.engine import Engine
    browser = BrowserManager(headless=headless)
    page = browser.start()
    browser.navigate()
    browser.wait_for_load()

    try:
        do_build_workflow(browser, agent_id=agent_id, preset=preset, flow=flow)
    finally:
        browser.close()


def do_build_workflow(browser: BrowserManager, agent_id: str = "",
                      preset: str = "", flow: Optional[list] = None) -> bool:
    """在已登录浏览器中搭建工作流"""
    page = browser.page
    learner = PageLearner()

    # 1. 进入工作流编辑器
    if agent_id:
        _open_workflow_editor(browser, page, agent_id)

    browser.random_delay(1000, 2000)

    # 2. 检测画布 (支持 React Flow / Vue Flow)
    if not _has_flow_canvas(page):
        for kw in ["工作流", "流程", "Workflow", "画布", "编排"]:
            tab = None
            for sel in [f"text='{kw}'", f"[role='tab']:has-text('{kw}')",
                        f"[class*='tab']:has-text('{kw}')"]:
                try:
                    tab = page.query_selector(sel)
                    if tab and tab.is_visible():
                        break
                except Exception:
                    continue
            if tab and tab.is_visible():
                tab.click()
                browser.wait_for_load()
                browser.random_delay(1000, 2000)
                break

    learner.learn(page, "workflow")

    # 3. 检测已有节点 (新平台预置 Start/End)
    existing_nodes = _get_canvas_nodes(page)
    if existing_nodes:
        print(f"[工作流] 画布已有 {len(existing_nodes)} 个节点:")
        for n in existing_nodes:
            print(f"  - {n['text']}")

    # 4. 按预设或定义搭建
    if preset:
        cfg = Config()
        presets = cfg.get("workflow_presets", default={})
        definition = presets.get(preset, {})
        if definition:
            print(f"[工作流] 使用预设: {definition.get('name', preset)}")
            _build_from_definition(browser, definition, existing_nodes)
            return True

    if flow:
        for node_type in flow:
            mapped = _resolve_node_type(node_type)
            if mapped:
                # 跳过已存在的节点
                if any(mapped in n['text'].lower() for n in existing_nodes):
                    print(f"[工作流] 节点已存在: {node_type}")
                    continue
                print(f"[工作流] 添加节点: {node_type} -> {mapped}")
                _add_node_on_canvas(page, browser, mapped)
                browser.random_delay(500, 1000)

    # 5. 连接节点（自动连接顺序节点）
    if flow and len(flow) > 1:
        for i in range(len(flow) - 1):
            from_type = _resolve_node_type(flow[i]) or flow[i]
            to_type = _resolve_node_type(flow[i + 1]) or flow[i + 1]
            _connect_nodes(page, from_type, to_type)
            browser.random_delay(500, 1000)

    # 6. 保存
    _save_workflow(page)
    return True


def _get_canvas_nodes(page) -> list[dict]:
    """获取画布上所有节点的名称和位置"""
    return page.evaluate("""() => {
        const ns = document.querySelectorAll('[class*="react-flow__node-"], [class*="vue-flow__node-"]');
        return Array.from(ns).filter(n => {
            const r = n.getBoundingClientRect();
            return r.width < 800 && r.height < 200;
        }).map(n => {
            const r = n.getBoundingClientRect();
            return {
                text: (n.innerText || '').trim().split('\\n')[0].trim().toLowerCase(),
                x: Math.round(r.left), y: Math.round(r.top),
                w: Math.round(r.width), h: Math.round(r.height),
                cx: Math.round(r.left + r.width/2),
                cy: Math.round(r.top + r.height/2),
                right: Math.round(r.right),
            };
        });
    }""") or []


def _open_workflow_editor(browser, page, agent_id: str):
    """打开工作流编辑器，支持新/旧URL模式"""
    from urllib.parse import urlparse
    parsed = urlparse(page.url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    # 直接检测是否已在编辑器中
    if _has_flow_canvas(page):
        return

    # 新平台: /work_flow/{id}/arrange
    try:
        num_id = int(agent_id)
        url = f"{base}/work_flow/{num_id}/arrange"
        page.goto(url, wait_until="networkidle", timeout=15000)
        browser.random_delay(1000, 2000)
        if _has_flow_canvas(page):
            return
    except ValueError:
        pass

    # 旧平台: 多种 URL 模式
    urls = [
        f"{base}/agent/base/editor/{agent_id}",
        f"{base}/agent/base/workflow/{agent_id}",
        f"{base}/agent/{agent_id}/workflow",
        f"{base}/agent/workflow/edit?agentId={agent_id}",
        f"{base}/agent/{agent_id}",
        f"{base}/agent/base/desktop/{agent_id}",
        f"{base}/workflow/{agent_id}",
    ]
    for url in urls:
        try:
            page.goto(url, wait_until="networkidle", timeout=15000)
            browser.random_delay(1000, 2000)
            if _has_flow_canvas(page):
                return
        except Exception:
            continue


def _has_flow_canvas(page) -> bool:
    """检测是否已加载工作流画布"""
    return bool(page.query_selector(
        ".react-flow, .vue-flow, .react-flow__container, "
        "[class*='canvas'], [class*='workflow'], svg[class*='flow']"
    ))


def _build_from_definition(browser, definition: dict,
                           existing_nodes: Optional[list] = None):
    """根据 JSON 定义构建工作流"""
    page = browser.page
    nodes = definition.get("nodes", [])
    connections = definition.get("connections", [])

    existing_labels = {n['text']: n for n in (existing_nodes or [])}

    for i, node_def in enumerate(nodes):
        ntype = node_def.get("type", "llm")
        label = node_def.get("label", ntype)

        # 跳过已有节点（如预置的 "开始"/"结束"）
        existing = None
        for ex_label, ex_node in existing_labels.items():
            if label.lower() in ex_label or ex_label in label.lower():
                existing = ex_node
                break
        if existing:
            print(f"[工作流] 节点已存在: {label}")
            continue

        pos = node_def.get("position", f"{100 + i * 250},{200}")
        pos_parts = pos.replace(" ", "").split(",")
        position = (int(pos_parts[0]), int(pos_parts[1])) if len(pos_parts) == 2 else None
        _add_node_on_canvas(page, browser, ntype, position, label)
        browser.random_delay()

        config = node_def.get("config", {})
        if config:
            _configure_node(page, label, config)
            browser.random_delay()

    for conn in connections:
        _connect_nodes(page, conn.get("from", ""), conn.get("to", ""))


def _resolve_node_type(node_type: str) -> Optional[str]:
    """将用户输入解析为标准节点类型"""
    node_lower = node_type.lower().strip()
    # 直接匹配
    if node_lower in NODE_TYPE_LABELS:
        return node_lower
    # 反向匹配
    for key, labels in NODE_TYPE_LABELS.items():
        if any(node_lower == l.lower() or node_lower in l.lower() for l in labels):
            return key
    return None


def _add_node_on_canvas(page, browser, node_type: str,
                        position: Optional[tuple] = None, label: str = ""):
    labels = NODE_TYPE_LABELS.get(node_type, [node_type])
    canvas_sel = page.query_selector(".react-flow, .vue-flow, [class*='canvas'], [class*='flow']")

    # 方法1: 拖拽 ([draggable="true"] 是新平台的拖拽方式)
    for label_text in labels:
        try:
            # 新平台: 通过 draggable 属性限定
            item = page.query_selector(f'[draggable="true"]:has-text("{label_text}")')
            if not item or not item.is_visible():
                # 备选: text 直接匹配
                item = page.query_selector(f"text={label_text}")
                if not item or not item.is_visible():
                    continue
            # 检查是否在侧栏区域 (x < 300px)
            box = item.bounding_box()
            if box and box['x'] >= 300:
                continue  # 不是侧栏元素
        except Exception:
            continue

        if canvas_sel:
            if position:
                target = {"x": position[0], "y": position[1]}
            else:
                target = {"x": 700, "y": 400}
            try:
                item.drag_to(canvas_sel, target_position=target, timeout=10000)
            except Exception:
                pass
        print(f"[工作流] 拖拽节点: {label_text}")
        browser.random_delay(1000, 2000)
        return

    # 方法2: 旧平台 — 拖拽/点击放置
    for label_text in labels:
        for sel in [f"text='{label_text}'",
                     f"[class*='node']:has-text('{label_text}')",
                     f"[class*='widget']:has-text('{label_text}')"]:
            item = page.query_selector(sel)
            if item and item.is_visible():
                break
        if not item or not item.is_visible():
            continue
        if canvas_sel and position:
            box = canvas_sel.bounding_box()
            if box:
                try:
                    item.drag_to(canvas_sel, target_position={"x": position[0], "y": position[1]})
                except Exception:
                    pass
        else:
            try:
                item.drag_to(canvas_sel)
            except Exception:
                pass
        print(f"[工作流] 拖拽节点: {label_text}")
        return

    print(f"[工作流] 未找到节点的面板项: {node_type}")


def _connect_nodes(page, from_type: str, to_type: str, from_idx: int = 0, to_idx: int = 0) -> bool:
    """连接两个节点 (支持 React Flow / Vue Flow 手柄)"""
    from_nodes = page.query_selector_all(
        f"[class*='react-flow__node']:has-text('{from_type}'), "
        f"[class*='vue-flow__node']:has-text('{from_type}'), "
        f"[class*='node']:has-text('{from_type}')"
    )
    to_nodes = page.query_selector_all(
        f"[class*='react-flow__node']:has-text('{to_type}'), "
        f"[class*='vue-flow__node']:has-text('{to_type}'), "
        f"[class*='node']:has-text('{to_type}')"
    )
    if len(from_nodes) <= from_idx or len(to_nodes) <= to_idx:
        print(f"[工作流] 找不到节点: {from_type} 或 {to_type}")
        return False

    source = from_nodes[from_idx]
    target = to_nodes[to_idx]

    # 方法1: 手动拖拽 (通过 JavaScript 获取手柄屏幕坐标)
    handles = page.evaluate("""() => {
        const hs = document.querySelectorAll('.react-flow__handle');
        return Array.from(hs).filter(h => {
            const r = h.getBoundingClientRect();
            return r.width > 0;
        }).map(h => {
            const r = h.getBoundingClientRect();
            const cls = h.className;
            return {
                cx: Math.round(r.left + r.width/2),
                cy: Math.round(r.top + r.height/2),
                isRight: cls.includes('handle-right') || cls.includes('output'),
                isLeft: cls.includes('handle-left') || cls.includes('input'),
                parentText: (h.parentElement?.innerText || '').trim().split('\\n')[0].trim().toLowerCase(),
            };
        });
    }""") or []

    # 找源节>目标节手柄
    src_handle = None
    tgt_handle = None
    from_lower = from_type.lower()
    to_lower = to_type.lower()

    for h in handles:
        pt = h.get('parentText', '')
        if from_lower in pt or pt in from_lower:
            if h.get('isRight') or not h.get('isLeft'):
                src_handle = h
        if to_lower in pt or pt in to_lower:
            if h.get('isLeft') or not h.get('isRight'):
                tgt_handle = h

    if src_handle and tgt_handle:
        page.mouse.move(src_handle['cx'], src_handle['cy'])
        page.wait_for_timeout(200)
        page.mouse.down()
        page.wait_for_timeout(200)
        page.mouse.move(tgt_handle['cx'], tgt_handle['cy'], steps=20)
        page.wait_for_timeout(200)
        page.mouse.up()
        page.wait_for_timeout(1000)
        print(f"[工作流] 连接: {from_type} → {to_type}")
        return True

    # 方法2: 节点边界拖拽
    src_box = source.bounding_box()
    tgt_box = target.bounding_box()
    if src_box and tgt_box:
        for off in [0, -15, 15]:
            sx = src_box['x'] + src_box['width']
            sy = src_box['y'] + src_box['height'] / 2 + off
            tx = tgt_box['x'] - 10
            ty = tgt_box['y'] + tgt_box['height'] / 2
            try:
                page.mouse.move(sx, sy)
                page.wait_for_timeout(200)
                page.mouse.down()
                page.wait_for_timeout(200)
                page.mouse.move(tx, ty, steps=20)
                page.wait_for_timeout(200)
                page.mouse.up()
                page.wait_for_timeout(1500)
                # 验证连线
                edges = page.query_selector_all('.react-flow__edge, .vue-flow__edge')
                if edges:
                    print(f"[工作流] 连接: {from_type} → {to_type}")
                    return True
            except Exception:
                continue

    # 方法3: 备选 - 点击连接
    source.click()
    page.wait_for_timeout(300)
    target.click()
    print(f"[工作流] 点击连接: {from_type} → {to_type}")
    return True


def run_configure_node(node_type: str, key: str, value: str,
                       headless: Optional[bool] = None):
    """CLI 入口: 配置节点"""
    browser = BrowserManager(headless=headless)
    page = browser.start()
    browser.navigate()
    browser.wait_for_load()
    try:
        _configure_node(page, node_type, {key: value})
    finally:
        browser.close()


def _configure_node(page, source: str, config: dict[str, Any]) -> bool:
    """配置节点参数 (支持 Ant Design + Flow Editor)"""
    print(f"[配置] 配置节点: {source}")

    # 选中节点 — 支持 React Flow
    node = None
    for sel in [f"[data-node-id='{source}']", f"[class*='react-flow__node']:has-text('{source}')",
                f"[class*='vue-flow__node']:has-text('{source}')",
                f"[class*='node']:has-text('{source}')"]:
        try:
            node = page.query_selector(sel)
            if node and node.is_visible():
                node.click()
                break
        except Exception:
            continue

    if not node:
        # 尝试在画布上定位
        nodes = page.evaluate("""text => {
            const ns = document.querySelectorAll('[class*="react-flow__node-"]');
            for (const n of ns) {
                const r = n.getBoundingClientRect();
                if (r.width < 800 && (n.innerText || '').includes(text)) {
                    return {x: Math.round(r.left + r.width/2), y: Math.round(r.top + 10)};
                }
            }
            return null;
        }""", source)
        if nodes:
            page.mouse.click(nodes['x'], nodes['y'])
        else:
            print(f"[配置] 找不到节点: {source}")
            return False

    page.wait_for_timeout(1000)

    # 检查配置面板是否打开 (Ant Design 侧边面板 / 弹窗)
    panel = page.query_selector(
        ".ant-drawer, .ant-modal, [class*='config'], [role='dialog'], "
        ".config-panel, .property-panel, .el-dialog"
    )
    if not panel:
        # 双击打开
        for sel in [f"[class*='react-flow__node']:has-text('{source}')",
                    f"[class*='node']:has-text('{source}')"]:
            try:
                nd = page.query_selector(sel)
                if nd and nd.is_visible():
                    nd.dblclick()
                    page.wait_for_timeout(500)
                    break
            except Exception:
                continue
        panel = page.query_selector(".ant-drawer, .ant-modal, [role='dialog']")

    # 设置每个字段
    for key, value in config.items():
        if value is None:
            continue
        print(f"[配置] {key} = {value}")
        _set_field(page, key, str(value))
        page.wait_for_timeout(300)

    # 关闭配置面板 (Escape)
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
    except Exception:
        pass

    return True


def _set_field(page, key: str, value: str):
    """在配置面板设置字段 (支持 Ant Design + flow editor)"""
    labels = CONFIG_KEY_MAP.get(key, [key, key.replace("_", " ")])

    # 特殊处理: 模型选择 (Ant Design Select)
    if key in ("model", "模型"):
        try:
            select_input = page.query_selector('.ant-select-selection-search-input')
            if select_input and select_input.is_visible():
                box = select_input.bounding_box()
                if box:
                    page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    page.wait_for_timeout(500)
                    page.keyboard.type(value, delay=20)
                    page.wait_for_timeout(1000)
                    # 从下拉选
                    opt = page.query_selector(f'.ant-select-item-option-content:has-text("{value.split("-")[0]}")')
                    if opt and opt.is_visible():
                        opt.click()
                        return
                    page.keyboard.press("Escape")
                    return
        except Exception:
            pass

    # 特殊处理: 系统提示词 (flow-template-editor)
    if key in ("system_prompt", "系统提示词", "提示词"):
        try:
            editor = page.query_selector('.flow-template-editor')
            if editor:
                page.evaluate("""text => {
                    const ed = document.querySelector('.flow-template-editor');
                    if (ed) { ed.focus(); ed.innerHTML = text;
                    ed.dispatchEvent(new Event('input', {bubbles: true})); }
                }""", value)
                return
            # 备选: contenteditable
            editor = page.query_selector('[contenteditable="true"]')
            if editor:
                editor.click()
                page.wait_for_timeout(200)
                page.keyboard.type(value, delay=10)
                return
        except Exception:
            pass

    # 普通 label 匹配
    for kw in labels:
        try:
            label = page.query_selector(f"label:has-text('{kw}')")
            if label:
                for_attr = label.get_attribute("for")
                if for_attr:
                    el = page.query_selector(f"#{for_attr}")
                    if el:
                        el.fill(value)
                        return
        except Exception:
            continue

    # placeholder/id/name 匹配
    try:
        for handle in page.query_selector_all("input:not([type='hidden']), textarea"):
            attrs = handle.evaluate("""el => ({placeholder: el.placeholder || '', name: el.name || '', id: el.id || ''})""")
            if any(k.lower() in attrs["placeholder"].lower() or k.lower() in attrs["name"].lower()
                   or k.lower() in attrs["id"].lower() for k in labels):
                handle.fill(value)
                return
    except Exception:
        pass


def _save_workflow(page) -> bool:
    """保存工作流"""
    # 先关闭可能的配置面板
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
    except Exception:
        pass

    for text in ["保存", "Save", "保存工作流"]:
        for sel in [f"button:has-text('{text}')", f"[class*='save']:has-text('{text}')", "[title='保存']"]:
            try:
                btn = page.query_selector(sel)
                if btn and btn.is_visible():
                    btn.click()
                    page.wait_for_timeout(2000)
                    print(f"[工作流] 保存成功")
                    return True
            except Exception:
                continue

    # 备选: Ctrl+S
    try:
        page.keyboard.press("Control+s")
        page.wait_for_timeout(2000)
        print(f"[工作流] Ctrl+S 保存")
        return True
    except Exception:
        pass

    print(f"[工作流] 未找到保存按钮")
    return False
