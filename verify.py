#!/usr/bin/env python3
"""
System Verification Script - Check if all modules can be imported and initialized
"""
import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print("=" * 60)
print("🏆 Enterprise Agent Platform Automation - System Verification")
print("=" * 60)


def test_import(name, module_path):
    """Test module import"""
    try:
        print(f"\n📦 Testing {name} ...", end=" ")
        __import__(module_path)
        print("✅ Success")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_config_loader():
    """Test config loader"""
    try:
        print("\n⚙️  Testing Config Loader ...", end=" ")
        from core.tools import ConfigLoader
        config = ConfigLoader()
        config.load()
        base_url = config.get('platform.base_url')
        print(f"✅ Success (base_url: {base_url})")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_nlp_parser():
    """Test NLP Parser"""
    try:
        print("\n🗣️  Testing NLP Parser ...", end=" ")
        from core.nlp_parser import NLPParser
        parser = NLPParser()

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

        print(f"✅ Success (parsed {len(results)} test commands)")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def main():
    """Main verification function"""
    success = True

    modules = [
        ("Tools Module", "core.tools"),
        ("Browser Adapter", "core.browser_adapter"),
        ("Learning Engine", "core.learning_engine"),
        ("Self-Healing Engine", "core.self_healing"),
        ("Atomic Skills", "core.atomic_skills"),
        ("NLP Parser", "core.nlp_parser"),
        ("Orchestrator", "core.orchestrator"),
    ]

    for name, path in modules:
        if not test_import(name, path):
            success = False

    if not test_config_loader():
        success = False

    if not test_nlp_parser():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("🎉 All system verifications passed!")
        print("💡 Note: Please set environment variables AIRCHINA_USERNAME and AIRCHINA_PASSWORD")
        print("💡 Then run: python3 main.py \"your command\"")
    else:
        print("⚠️  Some verifications failed, please check error messages")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
