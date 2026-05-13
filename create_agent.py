#!/usr/bin/env python3
"""
智能体创建器 — 使用 API 直调方式
流程: sentence/gen (AI生成配置) → insertBot (创建智能体)
"""
import sys, json, time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from vibe_agent.browser import BrowserManager
from test_e2e_xfyun import AdPopupHandler, wait_for_stable

USER_DATA_DIR = str(Path.home() / ".vibe" / "xfyun_profile")
PLATFORM_URL = "https://agent.xfyun.cn/home?register_from=xinghuoHome"


def build_payload(gen_data: dict, prompt_text: str) -> dict:
    """构建与 ju(isRAG=false, isNew=false) 一致的 insertBot payload"""
    d = gen_data["data"] if "data" in gen_data else gen_data
    return {
        "name": d.get("botName", ""),
        "botType": d.get("botType", 15),
        "botDesc": d.get("botDesc", ""),
        "supportContext": 0,
        "supportSystem": 0,
        "promptType": 0,  # ju() 硬编码为 0
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


def create_agent(sentence: str = "一个智能助手，可以回答用户的各种问题",
                 headless: bool = True) -> Optional[dict]:
    """
    创建智能体的主函数

    Args:
        sentence: 描述智能体的语句
        headless: 是否使用无头浏览器

    Returns:
        {"botId": int, "botName": str, "botType": int} 或 None
    """
    browser = BrowserManager(headless=headless, browser_type="chromium")
    page = browser.start(user_data_dir=USER_DATA_DIR)

    try:
        print(f"[创建] 导航到平台...")
        page.goto(PLATFORM_URL, wait_until="domcontentloaded", timeout=30000)
        wait_for_stable(page, timeout=10000)
        AdPopupHandler(page).detect_and_close_all()

        # Step 1: AI 生成智能体配置
        print(f"[创建] AI 生成配置...")
        gen = page.evaluate("""async (sentence) => {
            const r = await fetch('/xingchen-api/bot/sentence/gen', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({sentence: sentence}),
            });
            return await r.json();
        }""", sentence)

        if not gen.get("flag"):
            print(f"[创建] ❌ AI 生成失败: {gen.get('message', '')}")
            return None

        d = gen["data"]
        print(f"[创建] 生成: {d['botName']} (类型={d['botType']})")

        # Step 2: 构建 payload 并创建
        print(f"[创建] 调用 insertBot...")
        payload = build_payload(gen, sentence)
        r = page.evaluate("""async (payload) => {
            const res = await fetch('/xingchen-api/bot/insert', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload),
            });
            return await res.json();
        }""", payload)

        flag = r.get("flag")
        bot_id = r.get("data")

        if flag and bot_id:
            result = {
                "botId": bot_id,
                "botName": d["botName"],
                "botType": d["botType"],
            }
            print(f"[创建] ✅ 成功! botId={bot_id}, name={d['botName']}")
            return result
        else:
            code = r.get("code")
            msg = r.get("message", "") or r.get("desc", "")
            print(f"[创建] ❌ insertBot 失败: code={code}, msg={msg[:200]}")

            # 频率限制则等待重试
            if code == 90003:
                print(f"[创建] 频率限制，等待 30 秒...")
                page.wait_for_timeout(30000)
                gen2 = page.evaluate("""async (sentence) => {
                    const r = await fetch('/xingchen-api/bot/sentence/gen', {
                        method: 'POST', headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({sentence: sentence + 'v2'}),
                    });
                    return await r.json();
                }""", sentence)
                if gen2.get("flag"):
                    r2 = page.evaluate("""async (p) => {
                        const res = await fetch('/xingchen-api/bot/insert', {
                            method: 'POST', headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(p),
                        });
                        return await res.json();
                    }""", build_payload(gen2, sentence))
                    if r2.get("flag") and r2.get("data"):
                        print(f"[创建] ✅ 重试成功! botId={r2['data']}")
                        return {"botId": r2["data"], "botName": gen2["data"]["botName"]}

            return None

    except Exception as e:
        print(f"[创建] ❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        browser.close()


def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ("-h", "--help"):
        print("用法: python3 create_agent.py [sentence]")
        print("示例: python3 create_agent.py '一个客服助手'")
        return

    sentence = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "一个智能助手，可以回答用户的各种问题"
    result = create_agent(sentence)
    if result:
        print(f"\n{'='*50}")
        print(f"创建成功！")
        print(f"  botId:   {result['botId']}")
        print(f"  名称:    {result['botName']}")
        print(f"  链接:    https://agent.xfyun.cn/space/config/base?botId={result['botId']}")
        print(f"{'='*50}")
        return 0
    else:
        print("\n❌ 创建失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
