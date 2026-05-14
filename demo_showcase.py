#!/usr/bin/env python3
"""
vibe-coding-agent-framework 功能展示演示
展示：浏览器管理、页面学习、自愈引擎、工作流构建等核心能力
"""

import sys
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def log(message, level="INFO"):
    """日志输出"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def demo_showcase():
    """功能展示演示"""
    log("=" * 70)
    log("vibe-coding-agent-framework 功能展示")
    log("=" * 70)
    
    browser = None
    results = []
    
    try:
        from vibe_agent.browser import BrowserManager
        from vibe_agent.learner import PageLearner
        from vibe_agent.self_healing import SelfHealingEngine
        from vibe_agent.workflow_builder import WorkflowBuilder
        from vibe_agent.tools import sanitize, generate_test_report
        
        # ============================================
        # 1. 浏览器管理能力
        # ============================================
        log("\n🚀 模块 1: 浏览器管理")
        results.append({"module": "浏览器管理", "status": "started"})
        
        browser = BrowserManager(headless=False, slow_mo=500, browser_type="webkit")
        page = browser.start()
        
        log("✅ 浏览器启动成功 (Safari/WebKit)")
        log(f"   页面尺寸: 1440x900 (适配 MacBook Air 13 M2)")
        log(f"   反检测模式: 启用")
        results.append({"module": "浏览器管理", "status": "success"})
        
        # ============================================
        # 2. 页面访问与截图
        # ============================================
        log("\n🚀 模块 2: 页面访问与截图")
        results.append({"module": "页面访问", "status": "started"})
        
        url = "https://agent.xfyun.cn/home?register_from=xinghuoHome"
        log(f"🔗 访问: {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        browser.random_delay(2000, 3000)
        
        log(f"✅ 页面加载成功")
        log(f"   标题: {page.title()}")
        
        # 截图演示
        screenshot = browser.screenshot("showcase_demo")
        log(f"📷 截图保存: {screenshot}")
        results.append({"module": "页面访问", "status": "success", "screenshot": screenshot})
        
        # ============================================
        # 3. 页面学习引擎
        # ============================================
        log("\n🚀 模块 3: 页面学习引擎")
        results.append({"module": "页面学习引擎", "status": "started"})
        
        learner = PageLearner()
        
        # 页面类型检测
        page_type = learner._detect_page_type(page.url, page.title(), page)
        log(f"🔍 页面类型检测: {page_type}")
        
        # 学习页面结构
        log("📚 学习页面结构...")
        model = learner.learn_page(page, page_type)
        log(f"   识别区域: {len(model.regions)} 个")
        
        # 发现交互元素
        log("🔎 发现交互元素...")
        interactive_map = learner.discover_interactive_map(page)
        inputs = interactive_map.get('inputs', [])
        buttons = interactive_map.get('buttons', [])
        
        log(f"   输入框: {len(inputs)}")
        for i, inp in enumerate(inputs[:3]):
            log(f"     - {inp.get('label', '无标签')}")
        log(f"   按钮: {len(buttons)}")
        for i, btn in enumerate(buttons[:5]):
            log(f"     - {btn.get('text', '无文本')}")
        
        results.append({"module": "页面学习引擎", "status": "success"})
        
        # ============================================
        # 4. 自愈引擎演示
        # ============================================
        log("\n🚀 模块 4: 自愈引擎")
        results.append({"module": "自愈引擎", "status": "started"})
        
        healer = SelfHealingEngine()
        
        # 测试选择器自愈
        test_selector = 'button:has-text("不存在的按钮")'
        log(f"🧪 测试自愈: {test_selector}")
        
        def test_action(selector):
            try:
                element = page.query_selector(selector)
                return element is not None
            except:
                return False
        
        healed = healer.heal_and_retry(page, test_selector, test_action)
        log(f"   自愈结果: {'成功' if healed else '失败'}")
        
        # 测试文本匹配策略
        test_text = "登录"
        text_selector = healer._try_text_match(page, f'button:has-text("{test_text}")')
        log(f"📝 文本匹配结果: {text_selector}")
        
        # 测试角色匹配策略
        role_selector = healer._try_role_match(page, f'button:has-text("{test_text}")')
        log(f"🎭 角色匹配结果: {role_selector}")
        
        results.append({"module": "自愈引擎", "status": "success"})
        
        # ============================================
        # 5. 工作流构建器
        # ============================================
        log("\n🚀 模块 5: 工作流构建器")
        results.append({"module": "工作流构建器", "status": "started"})
        
        builder = WorkflowBuilder(browser)
        
        # 支持的节点类型列表
        log("📋 支持的节点类型:")
        node_types = ["llm", "dialog", "action", "condition", "webhook", "timer", 
                      "database", "file", "email", "sms", "http", "code", 
                      "switch", "loop", "parallel", "delay", "approval", "end"]
        for node_type in node_types[:6]:
            log(f"   - {node_type}")
        if len(node_types) > 6:
            log(f"   ... 还有 {len(node_types) - 6} 种")
        
        # 测试配置键转换
        labels = builder._key_to_labels("welcome_message")
        log(f"🔧 配置键转换示例: 'welcome_message' -> {labels}")
        
        results.append({"module": "工作流构建器", "status": "success"})
        
        # ============================================
        # 6. 工具函数
        # ============================================
        log("\n🚀 模块 6: 工具函数")
        results.append({"module": "工具函数", "status": "started"})
        
        # 脱敏演示
        sensitive_text = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoidGVzdCIsInBhc3MiOiJzZWNyZXQxMjMifQ.xxx"
        sanitized_text = sanitize(sensitive_text)
        log("🔐 数据脱敏示例:")
        log(f"   原始: {sensitive_text}")
        log(f"   脱敏后: {sanitized_text}")
        
        results.append({"module": "工具函数", "status": "success"})
        
        # ============================================
        # 7. CLI 命令展示
        # ============================================
        log("\n🚀 模块 7: CLI 命令")
        results.append({"module": "CLI命令", "status": "started"})
        
        log("💻 可用命令:")
        commands = [
            "vibe login         - 登录平台",
            "vibe create-agent  - 创建智能体",
            "vibe build-workflow - 构建工作流",
            "vibe publish       - 发布智能体",
            "vibe discover      - 发现模式分析页面",
            "vibe learn         - 主动学习页面结构",
            "vibe --browser webkit/chromium/firefox - 选择浏览器"
        ]
        for cmd in commands:
            log(f"   {cmd}")
        
        results.append({"module": "CLI命令", "status": "success"})
        
        # ============================================
        # 完成总结
        # ============================================
        log("\n" + "=" * 70)
        log("🎉 功能展示完成！")
        log("=" * 70)
        
        # 生成报告
        report_path = str(Path(__file__).parent / "showcase_report.md")
        screenshots = [r.get("screenshot") for r in results if r.get("screenshot")]
        generate_test_report(results, screenshots, report_path)
        log("\n📊 演示结果:")
        success_count = sum(1 for r in results if r["status"] == "success")
        log(f"   模块总数: {len(results)}")
        log(f"   成功: {success_count}")
        log(f"   失败: {len(results) - success_count}")
        
        log(f"\n📝 演示报告已保存: {report_path}")
        log("\n浏览器保持打开，可查看页面。")
        log("按 Ctrl+C 关闭浏览器...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log("\n👋 演示结束")
            
        return True
        
    except Exception as e:
        log(f"\n❌ 演示失败: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if browser:
            try:
                browser.close()
            except:
                pass

if __name__ == "__main__":
    success = demo_showcase()
    sys.exit(0 if success else 1)
