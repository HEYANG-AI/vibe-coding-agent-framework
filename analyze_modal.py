#!/usr/bin/env python3
"""仔细分析创建弹窗的结构，找到工作流创建的正确点击方式"""
import sys, time, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from vibe_agent.browser import BrowserManager
from test_e2e_xfyun import AdPopupHandler, wait_for_stable

USER_DATA_DIR = str(Path.home() / ".vibe" / "xfyun_profile")

browser = BrowserManager(headless=True, browser_type="chromium")
page = browser.start(user_data_dir=USER_DATA_DIR)
page.set_viewport_size({"width": 1280, "height": 800})

try:
    page.goto("https://agent.xfyun.cn/home?register_from=xinghuoHome",
              wait_until="domcontentloaded", timeout=30000)
    wait_for_stable(page, timeout=10000)
    AdPopupHandler(page).detect_and_close_all()
    time.sleep(2)

    # 点击创建
    create_btn = page.locator("span._create_text_u2ege_231")
    create_btn.click()
    time.sleep(2)
    print("[1] 点击创建")

    # 分析弹窗的所有可交互元素
    modal_analysis = page.evaluate("""() => {
        const modal = document.querySelector('.ant-modal');
        if (!modal) return 'NO MODAL';

        // 获取弹窗内所有可点击元素
        const clickable = modal.querySelectorAll('a, button, [role="button"], [role="tab"], [role="menuitem"], [onclick], [class*="item"], [class*="Item"], [class*="card"], [class*="Card"], [class*="option"], [class*="Option"], [class*="tab"], [class*="Tab"], div[class*="create"]');

        const results = [];
        clickable.forEach(el => {
            const rect = el.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
                results.push({
                    tag: el.tagName,
                    class: (el.className || '').substring(0, 80),
                    text: (el.innerText || '').trim().substring(0, 60),
                    rect: {x: rect.x, y: rect.y, w: rect.width, h: rect.height},
                    onclick: el.hasAttribute('onclick'),
                    tabindex: el.getAttribute('tabindex') || '',
                    role: el.getAttribute('role') || '',
                    data_attr: Object.keys(el.dataset).join(','),
                    children: el.children.length,
                    // 子元素定位器
                    child_texts: Array.from(el.children).map(c => (c.innerText||'').trim()).filter(t=>t).join(' | '),
                });
            }
        });

        // 获取弹窗 HTML 结构概览
        const structure = [];
        function walk(node, depth) {
            if (depth > 4) return;
            if (node.nodeType === 1) {
                const cn = (node.className || '').substring(0, 60);
                const txt = (node.innerText || '').trim().substring(0, 40);
                if (cn || txt) {
                    structure.push({tag: node.tagName, class: cn, text: txt, depth: depth});
                }
                for (let c of node.children) walk(c, depth + 1);
            }
        }
        walk(modal, 0);

        return {
            clickable_count: clickable.length,
            clickable: results,
            structure: structure.slice(0, 50),
            html: modal.innerHTML.substring(0, 3000),
        };
    }""")

    print(f"\n[2] 弹窗分析:")
    print(f"  可点击元素数: {modal_analysis.get('clickable_count', 0)}")
    print(f"\n  可点击元素:")
    for c in modal_analysis.get('clickable', []):
        print(f"    [{c['tag']}] class={c['class'][:40]}")
        print(f"    text={c['text'][:50]}")
        print(f"    pos=({c['rect']['x']:.0f},{c['rect']['y']:.0f}) size={c['rect']['w']:.0f}x{c['rect']['h']:.0f}")
        print(f"    role={c['role']} tabindex={c['tabindex']} onclick={c['onclick']}")
        print()

    # 特别找工作流创建元素
    wf_items = [c for c in modal_analysis.get('clickable', []) if '工作流' in c['text']]
    print(f"\n[3] 工作流元素:")
    for w in wf_items:
        print(f"    {w}")

    # 尝试点击 - 用 Playwright 的 force=True
    print(f"\n[4] 尝试点击工作流创建...")
    # 定位包含工作流创建文本的元素
    try:
        wf_option = page.locator('.ant-modal-body div').filter(has_text='工作流创建')
        if wf_option.count() > 0:
            print(f"  找到 {wf_option.count()} 个工作流创建选项")
            wf_option.first.click(force=True)
            time.sleep(3)
            print(f"  URL: {page.url}")

            # 检查页面变化
            page_info = page.evaluate("""() => ({
                title: document.title,
                url: window.location.href,
                text: document.body.innerText.substring(0, 3000),
            })""")
            print(f"  Title: {page_info['title']}")
            print(f"  当前页面文本:\n{page_info['text']}")
        else:
            print("  playwrigh t未找到工作流创建选项")
            # 备用：JS dispatch event
            print(f"\n[JS fallback]")
            result = page.evaluate("""() => {
                const modal = document.querySelector('.ant-modal');
                if (!modal) return 'no modal';
                // 找所有div检查
                const divs = modal.querySelectorAll('div');
                for (const d of divs) {
                    if (d.innerText.includes('工作流创建') && d.offsetParent !== null) {
                        // 触发 click 事件
                        d.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                        return 'dispatched: ' + d.className.substring(0,60);
                    }
                }
                return 'not found';
            }""")
            print(f"  JS result: {result}")
            time.sleep(3)
            print(f"  URL: {page.url}")
    except Exception as e:
        print(f"  Error: {e}")

    page.screenshot(path="/tmp/wf_modal_analysis.png")

finally:
    browser.close()
