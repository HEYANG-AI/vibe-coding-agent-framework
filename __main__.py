#!/usr/bin/env python3
"""
vibe-coding-agent-framework — 智能体搭建平台自动化框架
默认模式：手动登录 → headless 自动化
"""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from vibe_agent.browser import BrowserManager
from test_e2e_xfyun import AdPopupHandler, wait_for_stable
from vibe_agent.learner import PageLearner

USER_DATA_DIR = str(Path.home() / ".vibe" / "xfyun_profile")
PLATFORM_URL = "https://agent.xfyun.cn/home?register_from=xinghuoHome"


def login():
    """手动登录 — 打开可见浏览器，用户手动操作，会话保存到本地"""
    browser = BrowserManager(headless=False, browser_type="chromium")
    page = browser.start(user_data_dir=USER_DATA_DIR)

    try:
        print("=" * 60)
        print("智能体搭建平台 — 手动登录")
        print("=" * 60)

        print("\n[1/3] 打开平台...")
        page.goto(PLATFORM_URL, wait_until="domcontentloaded", timeout=60000)
        wait_for_stable(page, timeout=15000)
        print(f"  标题: {page.title()}")

        print("\n[2/3] 关闭广告弹窗...")
        handler = AdPopupHandler(page)
        closed = handler.detect_and_close_all()
        print(f"  关闭 {len(closed)} 个弹窗")

        print(f"\n{'='*60}")
        print("  浏览器已打开，请手动登录：")
        print("  1. 点击「点击登录」")
        print("  2. 输入手机号 → 获取验证码")
        print("  3. 完成滑块验证 → 输入短信验证码")
        print("  4. 点击「登录/注册」")
        print(f"{'='*60}")

        print("\n[3/3] 等待手动登录...")
        print("登录完成后，按 Ctrl+C 关闭浏览器继续\n")
        while True:
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n\n浏览器已关闭，会话已保存")
    finally:
        browser.close()


def analyze():
    """Headless 分析平台 — 使用已保存的登录会话"""
    browser = BrowserManager(headless=True, browser_type="chromium")
    page = browser.start(user_data_dir=USER_DATA_DIR)

    try:
        print("=" * 60)
        print("分析平台（headless 后台运行）")
        print("=" * 60)

        print("\n[1/4] 打开平台...")
        page.goto(PLATFORM_URL, wait_until="domcontentloaded", timeout=30000)
        wait_for_stable(page, timeout=10000)
        print(f"  标题: {page.title()}")

        print("\n[2/4] 关闭弹窗...")
        handler = AdPopupHandler(page)
        closed = handler.detect_and_close_all()
        print(f"  关闭 {len(closed)} 个弹窗")

        print("\n[3/4] 分析主页...")
        learner = PageLearner()
        model = learner.learn_page(page, "dashboard")
        print(f"  页面模型: {len(model.regions)} 个区域, 类型={model.page_type}")

        buttons = learner._discover_buttons(page)
        print(f"  按钮 ({len(buttons)}):")
        for b in buttons[:15]:
            print(f"    [{b['tag']}] {b['text'][:60]}")

        path = browser.screenshot("dashboard")
        print(f"  截图: {path}")

        print("\n[4/4] 检查登录状态...")
        has_login = page.evaluate("""() => {
            const text = document.body.innerText;
            return {
                is_logged_in: !text.includes('点击登录'),
                has_create: text.includes('创建智能体') || text.includes('我的智能体'),
            };
        }""")
        print(f"  已登录: {has_login['is_logged_in']}")
        print(f"  有创建入口: {has_login['has_create']}")

        if has_login['is_logged_in']:
            print("\n✅ 登录态有效，可以继续操作")
        else:
            print("\n⚠️  未检测到登录态，请先运行 manual-login")

        print(f"\n{'='*60}")
        print("分析完成")
        print(f"{'='*60}")

    except Exception as e:
        print(f"\n[FAIL] {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.close()


def create_agent():
    """创建智能体 — API 直调方式 (sentence/gen → insertBot)"""
    from create_agent import create_agent as api_create
    sentence = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "一个智能助手，可以回答用户的各种问题"
    result = api_create(sentence, headless=True)
    if result:
        print(f"\n✅ 创建成功: botId={result['botId']}, name={result['botName']}")
    else:
        print("\n❌ 创建失败")
        sys.exit(1)


def print_menu():
    print()
    print("=" * 60)
    print("  vibe-coding-agent-framework — 智能体搭建平台")
    print("=" * 60)
    print()
    print("  用法: python3 __main__.py <命令> [参数]")
    print()
    print("  命令:")
    print("    login              手动登录（可见浏览器，会话保存到本地）")
    print("    analyze            headless 分析已登录的平台")
    print("    create [描述]      API 直调创建智能体")
    print()
    print("  示例:")
    print("    python3 __main__.py login          # 先登录")
    print("    python3 __main__.py create          # 创建（默认描述）")
    print("    python3 __main__.py create 客服助手   # 创建自定义智能体")
    print()
    print("  流程: login → create")
    print("=" * 60)
    print()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print_menu()
        return

    command = sys.argv[1]

    if command == "login":
        login()
    elif command == "analyze":
        analyze()
    elif command == "create":
        create_agent()
    else:
        print(f"未知命令: {command}")
        print_menu()


if __name__ == "__main__":
    main()
