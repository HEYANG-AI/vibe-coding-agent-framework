"""
Agent 创建流程 — API 直调方式
=================================
使用 sentence/gen → insertBot 两步 API 调用创建智能体
"""

import json
from typing import Optional

from core.browser import BrowserManager


def build_payload(gen_data: dict, prompt_text: str) -> dict:
    """构建与 ju(isRAG=false, isNew=false) 一致的 insertBot payload"""
    d = gen_data.get("data", gen_data)
    return {
        "name": d.get("botName", ""),
        "botType": d.get("botType", 15),
        "botDesc": d.get("botDesc", ""),
        "supportContext": 0,
        "supportSystem": 0,
        "promptType": 0,
        "inputExample": [],
        "maasDatasetList": [],
        "avatar": d.get("avatar", ""),
        "vcnCn": "",
        "vcnEmotion": "",
        "vcnEn": "",
        "vcnSpeed": "",
        "isSentence": 0,
        "openedTool": "",
        "prologue": prompt_text,
        "model": "",
        "prompt": prompt_text,
        "enablePersonality": False,
        "personalityConfig": None,
        "chatBotExtra": {"enableBackground": False, "templateBotId": ""},
        "promptStructList": [],
    }


def do_create_agent(browser, name: str = "", description: str = "") -> Optional[str]:
    """
    使用已有浏览器创建 Agent，返回 agent_id。

    优先: API 直调 (sentence/gen → insertBot)
    备选: UI 创建 (通过工作流创建→自定义创建)
    """
    page = browser.page

    # 尝试 API 方式
    bot_id = _try_api_create(browser, name, description)
    if bot_id:
        return bot_id

    # 备选: UI 创建
    print(f"[创建] API 失败, 尝试 UI 方式...")
    return _create_agent_via_ui(browser, name, description or name)


def _try_api_create(browser, name: str, description: str) -> Optional[str]:
    """通过 API 创建 Agent (sentence/gen → insertBot)"""
    page = browser.page
    sentence = description or name or "一个智能助手"

    # Step 1: AI 生成
    print(f"[创建] AI 生成配置: \"{sentence[:50]}...\"")
    gen = page.evaluate("""async (sentence) => {
        const r = await fetch('/xingchen-api/bot/sentence/gen', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({sentence: sentence}),
        });
        return await r.json();
    }""", sentence)

    if not gen.get("flag"):
        print(f"[创建] ❌ AI 生成失败: {gen.get('message','')[:100]}")
        return None

    d = gen["data"]
    print(f"[创建] 生成: {d['botName']} (类型={d['botType']})")

    # Step 2: insertBot
    print(f"[创建] 调用 insertBot...")
    payload = build_payload(gen, sentence)
    r = page.evaluate("""async (payload) => {
        const res = await fetch('/xingchen-api/bot/insert', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload),
        });
        return await res.json();
    }""", payload)

    if r.get("flag") and r.get("data"):
        bot_id = str(r["data"])
        print(f"[创建] ✅ 成功! botId={bot_id}")
        return bot_id
    else:
        code = r.get("code")
        msg = r.get("message", "") or r.get("desc", "")
        print(f"[创建] ⚠️ API失败(code={code}, msg={msg[:100]})")
        return None


def _create_agent_via_ui(browser, name: str, description: str) -> Optional[str]:
    """
    通过 UI 创建工作流型 Agent:
    1. 导航到 /space/agent
    2. 点击「新建智能体」
    3. 点击「工作流创建」
    4. 点击「自定义创建」
    5. 进入 workflow 编辑器
    """
    page = browser.page

    # 1. 导航到我的智能体页面
    print(f"[创建] 导航到智能体管理...")
    try:
        page.goto(f"https://agent.xfyun.cn/space/agent", wait_until="networkidle", timeout=15000)
    except Exception:
        pass
    browser.random_delay(2000, 3000)

    # 2. 点击「新建智能体」
    print(f"[创建] 点击新建智能体...")
    try:
        btn = page.query_selector('span:has-text("新建智能体")')
        if not btn or not btn.is_visible():
            btn = page.query_selector('[class*="btnText"]:has-text("新建智能体")')
        if btn and btn.is_visible():
            btn.click()
        else:
            page.evaluate("""() => {
                const all = document.querySelectorAll('span');
                for (const el of all) {
                    if (el.innerText && el.innerText.trim() === '新建智能体' && el.offsetParent !== null) {
                        el.click(); return;
                    }
                }
            }""")
    except Exception as e:
        print(f"[创建] 点击新建失败: {e}")

    browser.random_delay(2000, 3000)

    # 3. 点击「工作流创建」
    print(f"[创建] 选择工作流创建模式...")
    try:
        wf_btn = page.query_selector('div:has-text("工作流创建"):has-text("复杂任务")')
        if not wf_btn or not wf_btn.is_visible():
            wf_btn = page.query_selector('text=工作流创建')
        if wf_btn and wf_btn.is_visible():
            wf_btn.click()
        else:
            page.evaluate("""() => {
                const all = document.querySelectorAll('div, span');
                for (const el of all) {
                    if (el.innerText && el.innerText.includes('工作流创建') && el.offsetParent !== null) {
                        el.click(); return;
                    }
                }
            }""")
    except Exception as e:
        print(f"[创建] 点击工作流创建失败: {e}")

    browser.random_delay(2000, 3000)

    # 4. 点击「自定义创建」
    print(f"[创建] 选择自定义创建...")
    try:
        custom_btn = page.query_selector('text=自定义创建')
        if custom_btn and custom_btn.is_visible():
            custom_btn.click()
            browser.random_delay(3000, 4000)
            print(f"[创建] ✅ 进入工作流编辑器")
        else:
            # 可能需要先填写名称
            name_input = page.query_selector("input[placeholder*='名称'], input[id*='name']")
            if name_input and name_input.is_visible():
                name_input.fill(name)
                browser.random_delay(500, 1000)
                for text in ["确认", "创建", "下一步"]:
                    btn = page.query_selector(f"button:has-text('{text}')")
                    if btn and btn.is_visible():
                        btn.click()
                        browser.random_delay(2000, 3000)
                        break
    except Exception as e:
        print(f"[创建] 自定义创建失败: {e}")

    # 5. 从 URL 提取 agent_id 或 workflow_id
    import re
    url = page.url
    m = re.search(r'/work_flow/(\d+)', url)
    if m:
        wf_id = m.group(1)
        print(f"[创建] ✅ 进入工作流编辑器 (ID={wf_id})")
        return wf_id

    m = re.search(r'agentId=([a-zA-Z0-9_]+)', url)
    if m:
        return m.group(1)

    print(f"[创建] ⚠️ 无法提取 ID (URL={url})")
    return None


def _create_agent_via_form(browser, name: str, description: str) -> Optional[str]:
    """通过页面表单创建 Agent (API 不可用时的备选方案)"""
    page = browser.page
    base_url = page.url.rstrip("/")

    # 导航到创建页面
    for url in [f"{base_url}/agent/create", f"{base_url}/agent/new",
                f"{base_url}/agent/base/desktop?action=create"]:
        try:
            page.goto(url, wait_until="networkidle", timeout=15000)
            browser.random_delay(1000, 2000)
            break
        except Exception:
            continue

    # 填写表单
    for handle in page.query_selector_all("input:not([type='password'])"):
        try:
            placeholder = (handle.get_attribute("placeholder") or "").lower()
            if any(k in placeholder for k in ["名称", "名字", "name", "agent"]):
                handle.click()
                handle.fill(name)
                browser.random_delay()
                break
        except Exception:
            continue

    for handle in page.query_selector_all("input, textarea"):
        try:
            placeholder = (handle.get_attribute("placeholder") or "").lower()
            if any(k in placeholder for k in ["描述", "desc"]):
                handle.click()
                handle.fill(description)
                browser.random_delay()
                break
        except Exception:
            continue

    # 提交
    for text in ["创建", "提交", "确认", "Create", "Submit"]:
        btn = page.query_selector(
            f"button:has-text('{text}'), button[type='submit'], [class*='submit']:has-text('{text}')"
        )
        if btn and btn.is_visible():
            btn.click()
            print(f"[创建] 提交表单")
            browser.random_delay(2000, 3000)
            break

    # 获取重定向 URL 中的 ID
    import time
    start = time.time()
    while time.time() - start < 10:
        current_url = page.url
        import re
        m = re.search(r'/(\d+)$', current_url)
        if m:
            return m.group(1)
        page.wait_for_timeout(500)

    print("[创建] 无法获取 bot ID，尝试从页面提取...")
    try:
        text = page.inner_text("body")
        m = re.search(r'(?:ID|id|编号)[：:\s]*(\w+)', text)
        if m:
            return m.group(1)
    except Exception:
        pass

    return name


def run_create_agent(name: str = "", description: str = "",
                     agent_type: str = "",
                     headless: Optional[bool] = None) -> Optional[dict]:
    """CLI 入口: 创建智能体

    Returns:
        {"botId": int, "botName": str} 或 None
    """
    browser = None
    try:
        browser = BrowserManager(headless=headless if headless is not None else True)
        page = browser.start()

        # 导航到平台
        from core.engine import Engine
        engine = Engine()
        base_url = engine.config.base_url()
        print(f"[创建] 导航到平台: {base_url}")
        page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
        browser.wait_for_load()

        # 处理广告弹窗
        try:
            page.evaluate("""() => {
                document.querySelectorAll('.ad-popup-close, .close-btn, [class*="close"]').forEach(el => {
                    if (el.offsetParent !== null) el.click();
                });
            }""")
        except Exception:
            pass

        # 尝试 API 创建
        bot_id = _try_api_create(browser, name, description)
        if bot_id:
            return {"botId": int(bot_id) if bot_id.isdigit() else bot_id, "botName": name}

        # UI 方式创建
        print(f"[创建] API不可用, 尝试UI方式...")
        bot_id = _create_agent_via_ui(browser, name, description or name)
        if bot_id:
            return {"botId": bot_id, "botName": name}

        print(f"[创建] ❌ 所有创建方式均失败")
        return None

    except Exception as e:
        print(f"[创建] ❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if browser:
            browser.close()
