#!/usr/bin/env python3
"""
Skill 功能验证脚本 - 检查 vibe-coding-agent-framework 的各项功能是否正常
"""

import sys
import os
import traceback
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试所有模块导入"""
    print("=" * 60)
    print("测试 1: 模块导入")
    print("=" * 60)
    
    modules = [
        "vibe_agent.cli",
        "vibe_agent.browser",
        "vibe_agent.login",
        "vibe_agent.dashboard",
        "vibe_agent.agent_creator",
        "vibe_agent.workflow_builder",
        "vibe_agent.publisher",
        "vibe_agent.learner",
        "vibe_agent.self_healing",
        "vibe_agent.tools",
        "vibe_agent.config",
    ]
    
    success = 0
    failed = 0
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module} - 导入成功")
            success += 1
        except Exception as e:
            print(f"❌ {module} - 导入失败: {e}")
            failed += 1
    
    print(f"\n导入测试结果: {success}/{len(modules)} 通过")
    return failed == 0

def test_config():
    """测试配置模块"""
    print("\n" + "=" * 60)
    print("测试 2: 配置模块")
    print("=" * 60)
    
    try:
        from vibe_agent.config import get_config, DEFAULT_CONFIG, load_yaml
        
        # 测试默认配置
        cfg = get_config()
        print(f"✅ 配置加载成功")
        print(f"   base_url: {cfg.get('base_url', 'N/A')}")
        print(f"   timeout: {cfg.get('timeout', 'N/A')}")
        print(f"   headless: {cfg.get('headless', 'N/A')}")
        
        # 测试选择器配置（从 DEFAULT_CONFIG 获取）
        selectors = DEFAULT_CONFIG.get("selectors", {})
        if "login_page" in selectors and "dashboard" in selectors:
            print(f"✅ 选择器配置完整")
        else:
            print(f"❌ 选择器配置不完整")
            return False
        
        return True
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        traceback.print_exc()
        return False

def test_cli_parser():
    """测试 CLI 参数解析"""
    print("\n" + "=" * 60)
    print("测试 3: CLI 参数解析")
    print("=" * 60)
    
    try:
        from vibe_agent.cli import main
        import argparse
        
        # 测试空参数（帮助信息）
        sys.argv = ["vibe"]
        try:
            main()
        except SystemExit:
            print("✅ 空参数（帮助信息）正常")
        
        # 测试 login 命令
        sys.argv = ["vibe", "login", "--help"]
        try:
            main()
        except SystemExit:
            print("✅ login 命令帮助正常")
        
        # 测试 create-agent 命令
        sys.argv = ["vibe", "create-agent", "--help"]
        try:
            main()
        except SystemExit:
            print("✅ create-agent 命令帮助正常")
        
        # 测试 build-workflow 命令
        sys.argv = ["vibe", "build-workflow", "--help"]
        try:
            main()
        except SystemExit:
            print("✅ build-workflow 命令帮助正常")
        
        # 测试 publish 命令
        sys.argv = ["vibe", "publish", "--help"]
        try:
            main()
        except SystemExit:
            print("✅ publish 命令帮助正常")
        
        # 测试 discover 命令
        sys.argv = ["vibe", "discover", "--help"]
        try:
            main()
        except SystemExit:
            print("✅ discover 命令帮助正常")
        
        return True
    except Exception as e:
        print(f"❌ CLI 测试失败: {e}")
        traceback.print_exc()
        return False

def test_browser_manager():
    """测试浏览器管理器（不实际启动浏览器）"""
    print("\n" + "=" * 60)
    print("测试 4: 浏览器管理器")
    print("=" * 60)
    
    try:
        from vibe_agent.browser import BrowserManager
        
        # 测试初始化
        browser = BrowserManager(headless=True)
        print(f"✅ 浏览器管理器初始化成功")
        print(f"   headless: {browser.headless}")
        print(f"   timeout: {browser.timeout}")
        print(f"   slow_mo: {browser.slow_mo}")
        
        # 测试截图目录创建
        print(f"✅ 截图目录: {browser.screenshot_dir}")
        assert browser.screenshot_dir.exists(), "截图目录未创建"
        
        return True
    except Exception as e:
        print(f"❌ 浏览器管理器测试失败: {e}")
        traceback.print_exc()
        return False

def test_learner():
    """测试页面学习引擎"""
    print("\n" + "=" * 60)
    print("测试 5: 页面学习引擎")
    print("=" * 60)
    
    try:
        from vibe_agent.learner import PageLearner
        
        learner = PageLearner()
        print(f"✅ 学习引擎初始化成功")
        print(f"   模型目录: {learner.model_dir}")
        
        # 测试页面类型检测
        url = "https://example.com/login"
        title = "登录页"
        from unittest.mock import MagicMock
        mock_page = MagicMock()
        mock_page.inner_text.return_value = "用户名 密码 登录"
        page_type = learner._detect_page_type(url, title, mock_page)
        print(f"✅ 页面类型检测: '{url}' -> {page_type}")
        
        # 测试区域模式获取
        patterns = learner._get_region_patterns("login")
        print(f"✅ 区域模式加载: {len(patterns)} 个模式")
        
        return True
    except Exception as e:
        print(f"❌ 学习引擎测试失败: {e}")
        traceback.print_exc()
        return False

def test_self_healing():
    """测试自愈引擎"""
    print("\n" + "=" * 60)
    print("测试 6: 自愈引擎")
    print("=" * 60)
    
    try:
        from vibe_agent.self_healing import SelfHealingEngine, Locator
        
        engine = SelfHealingEngine()
        print(f"✅ 自愈引擎初始化成功")
        print(f"   自愈目录: {engine.healing_dir}")
        print(f"   最大重试: {engine.max_retries}")
        
        # 测试统计功能
        stats = engine.get_stats()
        print(f"✅ 统计功能正常: {stats}")
        
        # 测试选择器文本提取
        selector = "button:has-text('登录')"
        texts = engine._extract_text_from_selector(selector)
        print(f"✅ 选择器文本提取: '{selector}' -> {texts}")
        
        # 测试元素类型检测
        el_type = engine._detect_element_type("button.login-btn")
        print(f"✅ 元素类型检测: 'button.login-btn' -> {el_type}")
        
        return True
    except Exception as e:
        print(f"❌ 自愈引擎测试失败: {e}")
        traceback.print_exc()
        return False

def test_workflow_builder():
    """测试工作流构建器"""
    print("\n" + "=" * 60)
    print("测试 7: 工作流构建器")
    print("=" * 60)
    
    try:
        from vibe_agent.workflow_builder import WorkflowBuilder, NODE_TYPE_LABELS
        
        print(f"✅ 节点类型定义: {len(NODE_TYPE_LABELS)} 种")
        
        # 测试键到标签的转换
        key_labels = WorkflowBuilder._key_to_labels(WorkflowBuilder, "model")
        print(f"✅ 键转换: 'model' -> {key_labels}")
        
        key_labels = WorkflowBuilder._key_to_labels(WorkflowBuilder, "temperature")
        print(f"✅ 键转换: 'temperature' -> {key_labels}")
        
        return True
    except Exception as e:
        print(f"❌ 工作流构建器测试失败: {e}")
        traceback.print_exc()
        return False

def test_tools():
    """测试工具函数"""
    print("\n" + "=" * 60)
    print("测试 8: 工具函数")
    print("=" * 60)
    
    try:
        from vibe_agent.tools import sanitize, SanitizedLogger, StepAsserter, generate_test_report
        
        # 测试脱敏功能
        test_text = "password=secret123 token=abcdef12345"
        sanitized = sanitize(test_text)
        assert "secret123" not in sanitized, "脱敏失败"
        assert "abcdef12345" not in sanitized, "脱敏失败"
        print(f"✅ 脱敏功能正常")
        
        # 测试日志器（捕获权限错误）
        try:
            logger = SanitizedLogger("test")
            logger.info("测试日志")
            print(f"✅ 日志器正常")
        except PermissionError:
            print(f"⚠️  日志器初始化（权限限制，跳过）")
        
        # 测试断言器
        asserter = StepAsserter()
        print(f"✅ 断言器正常")
        
        # 测试报告生成
        steps = [{"step": "测试", "status": "PASS", "detail": "测试通过"}]
        report_path = generate_test_report(steps, [])
        print(f"✅ 报告生成正常: {report_path}")
        
        return True
    except Exception as e:
        print(f"❌ 工具函数测试失败: {e}")
        traceback.print_exc()
        return False

def test_login_page():
    """测试登录页面模块"""
    print("\n" + "=" * 60)
    print("测试 9: 登录页面模块")
    print("=" * 60)
    
    try:
        from vibe_agent.login import LoginPage
        from vibe_agent.browser import BrowserManager
        
        # 测试初始化
        browser = BrowserManager(headless=True)
        login = LoginPage(browser)
        print(f"✅ 登录页面初始化成功")
        
        # 测试 SSO 检测
        from unittest.mock import MagicMock
        mock_page = MagicMock()
        
        # 测试非 SSO 页面
        mock_page.query_selector.return_value = None
        mock_page.url = "https://example.com/login"
        is_sso = login._is_sso_page(mock_page)
        print(f"✅ SSO 检测: 普通登录页 -> {is_sso}")
        
        return True
    except Exception as e:
        print(f"❌ 登录页面测试失败: {e}")
        traceback.print_exc()
        return False

def test_publisher():
    """测试发布模块"""
    print("\n" + "=" * 60)
    print("测试 10: 发布模块")
    print("=" * 60)
    
    try:
        from vibe_agent.publisher import Publisher
        from vibe_agent.browser import BrowserManager
        
        browser = BrowserManager(headless=True)
        publisher = Publisher(browser)
        print(f"✅ 发布模块初始化成功")
        
        return True
    except Exception as e:
        print(f"❌ 发布模块测试失败: {e}")
        traceback.print_exc()
        return False

def test_agent_creator():
    """测试 Agent 创建模块"""
    print("\n" + "=" * 60)
    print("测试 11: Agent 创建模块")
    print("=" * 60)
    
    try:
        from vibe_agent.agent_creator import AgentCreator
        from vibe_agent.browser import BrowserManager
        
        browser = BrowserManager(headless=True)
        creator = AgentCreator(browser)
        print(f"✅ Agent 创建模块初始化成功")
        
        # 测试 URL 中的 Agent ID 提取逻辑（直接测试正则）
        import re
        url = "https://example.com/agent/12345/detail"
        patterns = [
            r'/agent/(\d+)',
            r'/agent/([a-f0-9-]{36})',
            r'/bot/(\d+)',
            r'/detail/(\d+)',
            r'id=(\d+)',
            r'agentId=([^&]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                print(f"✅ Agent ID 提取测试: {url} -> {match.group(1)}")
                break
        
        return True
    except Exception as e:
        print(f"❌ Agent 创建模块测试失败: {e}")
        traceback.print_exc()
        return False

def test_dashboard():
    """测试仪表板导航模块"""
    print("\n" + "=" * 60)
    print("测试 12: 仪表板导航模块")
    print("=" * 60)
    
    try:
        from vibe_agent.dashboard import Dashboard
        from vibe_agent.browser import BrowserManager
        
        browser = BrowserManager(headless=True)
        dashboard = Dashboard(browser)
        print(f"✅ 仪表板导航模块初始化成功")
        
        return True
    except Exception as e:
        print(f"❌ 仪表板导航模块测试失败: {e}")
        traceback.print_exc()
        return False

def test_playwright_installation():
    """测试 Playwright 是否安装"""
    print("\n" + "=" * 60)
    print("测试 13: Playwright 安装验证")
    print("=" * 60)
    
    try:
        import playwright
        from playwright.sync_api import sync_playwright
        
        print(f"✅ Playwright 模块导入成功")
        
        # 获取 Playwright 版本
        import pkg_resources
        try:
            version = pkg_resources.get_distribution("playwright").version
            print(f"   版本: {version}")
        except Exception:
            print(f"   版本: 无法获取")
        
        # 检查浏览器是否安装
        import subprocess
        try:
            result = subprocess.run(
                ["playwright", "install", "--dry-run"],
                capture_output=True, text=True
            )
            if "already installed" in result.stdout or result.returncode == 0:
                print(f"✅ Playwright 浏览器已安装")
            else:
                print(f"⚠️  Playwright 浏览器可能未安装")
        except FileNotFoundError:
            # playwright 命令行工具未安装，但模块可用
            print(f"⚠️  Playwright 命令行工具未安装（使用 python -m playwright）")
        
        return True
    except ImportError:
        print(f"❌ Playwright 未安装")
        return False
    except Exception as e:
        print(f"❌ Playwright 测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试入口"""
    print("=" * 60)
    print("vibe-coding-agent-framework 功能验证")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_imports),
        ("配置模块", test_config),
        ("CLI 参数解析", test_cli_parser),
        ("浏览器管理器", test_browser_manager),
        ("页面学习引擎", test_learner),
        ("自愈引擎", test_self_healing),
        ("工作流构建器", test_workflow_builder),
        ("工具函数", test_tools),
        ("登录页面模块", test_login_page),
        ("发布模块", test_publisher),
        ("Agent 创建模块", test_agent_creator),
        ("仪表板导航模块", test_dashboard),
        ("Playwright 安装", test_playwright_installation),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ {name} 异常: {e}")
            traceback.print_exc()
            failed += 1
    
    # 汇总
    print("\n" + "=" * 60)
    print(f"验证结果: {passed}/{len(tests)} 通过")
    print("=" * 60)
    
    if failed > 0:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查相关模块")
        sys.exit(1)
    else:
        print("\n🎉 所有测试通过！Skill 功能验证完成")
        sys.exit(0)

if __name__ == "__main__":
    main()
