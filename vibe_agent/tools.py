"""
工具函数 - 日志脱敏、断言、截图、报告生成
"""

import json
import os
import re
import time
from pathlib import Path
from typing import Optional, Any

from playwright.sync_api import Page


# ========== 日志脱敏 ==========

def _make_sanitize_patterns():
    """构建脱敏模式列表。返回 (compiled_pattern, replacement) 对。"""
    import re

    keys = ["password", "token", "secret", "authorization",
            "cookie", "api_key", "apikey", "session"]

    patterns = []
    for key in keys:
        # key=value → 替换为 key=***
        rx = re.compile(
            r"(?P<key>" + key + r"\s*=\s*)(?P<quote>[\"']?)(?P<value>\S+)(?P=quote)",
            re.IGNORECASE
        )
        patterns.append((rx, lambda m: m.group("key") + m.group("quote") + "***" + m.group("quote")))

    # AICHINA_ 环境变量
    rx = re.compile(r"(?P<key>AICHINA_PASSWORD=)\S+", re.IGNORECASE)
    patterns.append((rx, lambda m: m.group("key") + "***"))
    rx = re.compile(r"(?P<key>AICHINA_USERNAME=)\S+", re.IGNORECASE)
    patterns.append((rx, lambda m: m.group("key") + "***"))

    # Authorization: Bearer xxx 格式
    rx = re.compile(r"(?P<key>Authorization\s*:\s*Bearer\s+)\S+", re.IGNORECASE)
    patterns.append((rx, lambda m: m.group("key") + "***"))

    return patterns


SANITIZE_PATTERNS = _make_sanitize_patterns()


def sanitize(text: str) -> str:
    """脱敏敏感信息"""
    for pattern, repl_fn in SANITIZE_PATTERNS:
        text = pattern.sub(repl_fn, text)
    return text


class SanitizedLogger:
    """自动脱敏日志"""

    def __init__(self, name: str = "vibe"):
        import logging
        log_dir = Path.home() / ".vibe" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # 文件处理器
        fh = logging.FileHandler(log_dir / "vibe.log", encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        self.logger.addHandler(fh)

        # 控制台处理器
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        self.logger.addHandler(ch)

    def info(self, msg: str, *args, **kwargs):
        self.logger.info(sanitize(msg), *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(sanitize(msg), *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self.logger.error(sanitize(msg), *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(sanitize(msg), *args, **kwargs)


# ========== 断言工具 ==========

class StepAsserter:
    """步骤断言器 - 每个关键步骤记录+断言"""

    def __init__(self, logger: Optional[SanitizedLogger] = None):
        self.logger = logger or SanitizedLogger()
        self.steps: list[dict] = []
        self.failures: list[dict] = []

    def assert_url_contains(self, page: Page, expected: str, step_name: str = "URL检查") -> bool:
        """断言 URL 包含预期内容"""
        actual = page.url
        if expected in actual:
            self._pass(step_name, f"URL包含'{expected}'")
            return True
        else:
            self._fail(step_name, f"期望URL包含'{expected}', 实际: {actual[:100]}")
            return False

    def assert_element_visible(self, page: Page, selector: str, step_name: str = "元素可见") -> bool:
        """断言元素可见"""
        try:
            el = page.query_selector(selector)
            if el and el.is_visible():
                self._pass(step_name, f"元素可见: {selector[:60]}")
                return True
            else:
                self._fail(step_name, f"元素不可见: {selector[:60]}")
                return False
        except Exception as e:
            self._fail(step_name, f"元素检查异常: {e}")
            return False

    def assert_text_present(self, page: Page, text: str, step_name: str = "文本检查") -> bool:
        """断言页面包含指定文本"""
        try:
            body = page.inner_text("body")
            if text in body:
                self._pass(step_name, f"页面包含文本: '{text[:50]}'")
                return True
            else:
                self._fail(step_name, f"页面不包含文本: '{text[:50]}'")
                return False
        except Exception as e:
            self._fail(step_name, f"文本检查异常: {e}")
            return False

    def assert_page_loaded(self, page: Page, step_name: str = "页面加载") -> bool:
        """断言页面加载完成"""
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
            self._pass(step_name, f"页面加载完成: {page.title()[:50]}")
            return True
        except Exception as e:
            self._fail(step_name, f"页面加载超时: {e}")
            return False

    def _pass(self, step: str, detail: str):
        self.steps.append({"step": step, "status": "PASS", "detail": detail})
        self.logger.info(f"✅ {step}: {detail}")

    def _fail(self, step: str, detail: str):
        entry = {"step": step, "status": "FAIL", "detail": detail}
        self.steps.append(entry)
        self.failures.append(entry)
        self.logger.error(f"❌ {step}: {detail}")

    def summary(self) -> dict:
        """返回断言摘要"""
        return {
            "total": len(self.steps),
            "passed": len(self.steps) - len(self.failures),
            "failed": len(self.failures),
            "steps": self.steps,
        }

    def print_summary(self):
        """打印摘要"""
        s = self.summary()
        print(f"\n{'='*50}")
        print(f"测试摘要: {s['passed']}/{s['total']} 通过")
        if s['failed'] > 0:
            print(f"失败步骤:")
            for f in s['steps']:
                if f['status'] == 'FAIL':
                    print(f"  - {f['step']}: {f['detail']}")
        print(f"{'='*50}\n")


# ========== 截图工具 ==========

def take_screenshot(page: Page, name: str = "screenshot") -> str:
    """截图，返回文件路径"""
    screenshot_dir = Path.home() / ".vibe" / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    path = str(screenshot_dir / f"{name}_{timestamp}.png")
    try:
        page.screenshot(path=path, full_page=True)
    except Exception:
        pass
    return path


def take_critical_screenshot(page: Page, step_name: str) -> str:
    """关键步骤截图"""
    safe_name = re.sub(r'[^\w]', '_', step_name)[:50]
    return take_screenshot(page, safe_name)


# ========== 报告生成 ==========

def generate_test_report(steps: list[dict], screenshots: list[str],
                         output_path: Optional[str] = None) -> str:
    """生成测试报告（JSON）"""
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_steps": len(steps),
        "passed": sum(1 for s in steps if s.get("status") == "PASS"),
        "failed": sum(1 for s in steps if s.get("status") == "FAIL"),
        "steps": steps,
        "screenshots": screenshots,
    }

    path = output_path or str(Path.home() / ".vibe" / f"report_{int(time.time())}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"测试报告: {path}")
    return path


# ========== 等待工具 ==========

def smart_wait(page: Page, condition: str, timeout: int = 30000,
               interval: float = 0.5) -> bool:
    """
    智能等待，支持多种条件:
    - "networkidle": 网络空闲
    - "domcontentloaded": DOM 加载
    - "load": 完全加载
    - url包含xxx: URL 包含指定内容
    """
    import time
    start = time.time()

    if condition in ["networkidle", "domcontentloaded", "load"]:
        try:
            page.wait_for_load_state(condition, timeout=timeout)
            return True
        except Exception:
            return False

    if condition.startswith("url:"):
        expected = condition[4:]
        while time.time() - start < timeout / 1000:
            if expected in page.url:
                return True
            time.sleep(interval)
        return False

    if condition.startswith("text:"):
        expected = condition[5:]
        while time.time() - start < timeout / 1000:
            try:
                body = page.inner_text("body")
                if expected in body:
                    return True
            except Exception:
                pass
            time.sleep(interval)
        return False

    if condition.startswith("selector:"):
        sel = condition[9:]
        try:
            page.wait_for_selector(sel, timeout=timeout)
            return True
        except Exception:
            return False

    return False
