#!/usr/bin/env python3
"""
系统验证脚本 - 检查 Skill 的各个模块是否可以正常导入和初始化
"""
import sys
from pathlib import Path

# 将当前目录加入路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print("=" * 60)
print("🏆 企业智能体平台自动化 Skill - 系统验证")
print("=" * 60)


def test_import(name, module_path):
    """测试模块导入"""
    try:
        print(f"\n📦 测试 {name} ...", end=" ")
        __import__(module_path)
        print("✅ 成功")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_config_loader():
    """测试配置加载器"""
    try:
        print("\n⚙️  测试配置加载器 ...", end=" ")
        from core.tools import ConfigLoader
        config = ConfigLoader()
        config.load()
        base_url = config.get('platform.base_url')
        print(f"✅ 成功 (base_url: {base_url})")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_nlp_parser():
    """测试 NLP 解析器"""
    try:
        print("\n🗣️  测试 NLP 解析器 ...", end=" ")
        from core.nlp_parser import NLPParser
        parser = NLPParser()
        
        # 测试几个简单命令
        test_cases = [
            "前往企业智能体平台",
            "登录系统",
            "新建一个业务智能体",
            "全自动创建业务智能体并发布",
        ]
        
        results = []
        for cmd in test_cases:
            result = parser.parse(cmd)
            results.append(result)
        
        print(f"✅ 成功 (解析了 {len(results)} 个测试命令)")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def main():
    """主验证函数"""
    success = True
    
    # 测试核心模块
    modules = [
        ("工具模块", "core.tools"),
        ("浏览器适配器", "core.browser_adapter"),
        ("学习引擎", "core.learning_engine"),
        ("自愈引擎", "core.self_healing"),
        ("原子技能", "core.atomic_skills"),
        ("NLP 解析器", "core.nlp_parser"),
        ("工作流调度器", "core.orchestrator"),
    ]
    
    for name, path in modules:
        if not test_import(name, path):
            success = False
    
    # 测试功能
    if not test_config_loader():
        success = False
    
    if not test_nlp_parser():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 系统验证全部通过！")
        print("💡 提示：请设置环境变量 AIRCHINA_USERNAME 和 AIRCHINA_PASSWORD")
        print("💡 然后运行: python __main__.py \"你的命令\"")
    else:
        print("⚠️  系统验证部分失败，请检查错误信息")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
