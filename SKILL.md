# 🏆 Enterprise Agent Platform Automation Skill - Competition Winning Top Version

## 📋 Overview

This is a universal configurable enterprise-grade cross-platform intelligent agent automation Skill, designed for various low-code agent platforms, supporting one-click adaptation to different enterprise environments.

### ✨ Core Advantages

1. **Universal Configurable Design**: No code changes needed, just modify config to adapt to any enterprise platform
2. **Autonomous Learning**: Automatically identifies page menus, buttons, login boxes, workflow components on first visit
3. **AI Self-Healing**: Automatically re-identifies and adapts when platform UI changes
4. **Atomic Modular Architecture**: Independent reusable units for flexible composition
5. **Natural Language Interface**: Execute complex workflows with simple commands
6. **Enterprise Security**: Whitelist protection, no hardcoded credentials, automatic log masking
7. **Built-in Public Demo Site**: Test and experience without enterprise intranet

---

## 📁 Directory Structure

```
airchina_agent_platform/
├── SKILL.md              # Main skill documentation
├── config.yaml           # User configuration file
├── core/
│   ├── __init__.py
│   ├── browser_adapter.py    # Cross-platform browser adapter (with security whitelist)
│   ├── learning_engine.py    # Page autonomous learning engine
│   ├── self_healing.py       # AI self-healing engine
│   ├── tools.py              # Common tools (config loader, log masking)
│   ├── atomic_skills.py      # Atomic skills module
│   ├── nlp_parser.py         # Enhanced NLP parser
│   └── orchestrator.py       # Workflow orchestrator
├── flows/
│   ├── __init__.py
│   ├── login_flow.py         # Login flow
│   ├── create_agent_flow.py  # Create Agent flow
│   └── publish_flow.py       # Publish flow
└── tests/
    ├── __init__.py
    ├── test_login.py
    ├── test_create_agent.py
    └── test_full_flow.py
```

---

## 🚀 Quick Start

### 1. Configure Platform

Just modify the following in `config.yaml`:

```yaml
platform:
  name: "Your Enterprise Platform Name"
  base_url: "https://your-company-platform.com"
```

### 2. Set Environment Variables (Credentials)

```bash
# macOS/Linux
export AIRCHINA_USERNAME="your_username"
export AIRCHINA_PASSWORD="your_password"

# Windows (PowerShell)
$env:AIRCHINA_USERNAME="your_username"
$env:AIRCHINA_PASSWORD="your_password"
```

### 3. Execute with One Command

```
"前往企业智能体平台新建业务智能体"
"自动搭建机组排班工作流并保存发布"
"登录后台批量查看已有智能体列表"
```

---

## ⚙️ Configuration Guide

### Complete config.yaml

```yaml
# Platform Configuration
platform:
  name: "Enterprise Agent Platform"
  base_url: "https://aiagenttest.airchina.com.cn/agent/base/desktop/index"
  timeout: 30
  screenshot_dir: "./logs/screenshots"

# Browser Configuration
browser:
  type: "chrome"  # chrome, firefox, edge
  headless: false
  window_size: [1920, 1080]
  user_data_dir: null

# Retry Configuration
retry:
  max_attempts: 3
  delay_seconds: 2
  exponential_backoff: true

# Security Configuration
security:
  username_env: "AIRCHINA_USERNAME"
  password_env: "AIRCHINA_PASSWORD"
  session_persistence: true
  allowed_domains: ["airchina.com.cn"]  # Security whitelist

# Element Locator Configuration (customize to adapt your platform)
elements:
  login:
    username_input: ["//input[@type='text']", "//input[@name='username']"]
    password_input: ["//input[@type='password']"]
    login_button: ["//button[@type='submit']"]
  menu:
    agent_menu: ["//*[contains(text(), 'Agent')]"]
    new_agent: ["//button[contains(text(), '新建')]"]
    publish_agent: ["//button[contains(text(), '发布')]"]
```

---

## 💬 Natural Language Command Examples

### Basic Commands

| Requirement | Command Example |
|-------------|-----------------|
| Open Platform | "前往企业智能体平台" |
| Login | "登录系统" |
| Create Agent | "新建一个业务智能体" |
| View List | "查看已有智能体列表" |
| Publish | "保存并发布" |

### Full Flow Commands (One command)

```
"执行完整流程：打开→登录→新建→建工作流→保存发布"
"全自动创建业务智能体并发布"
"一句话帮我完成智能体创建全流程"
```

### Business Scenario Examples

```
"自动搭建机组排班工作流并保存发布"
"新建航班查询智能体，配置工作流后发布"
"批量查看后台智能体状态"
```

---

## 🔐 Security Features

1. **Environment Variable Credentials**: Credentials read from environment variables, never hardcoded in any file via `AIRCHINA_USERNAME` and `AIRCHINA_PASSWORD`
2. **Domain Whitelist**: Configure `allowed_domains` to prevent accessing unauthorized domains
3. **Automatic Log Masking**: Sensitive information automatically redacted
4. **Secure Session Reuse**: Login once, use multiple times for efficiency

---

## 🧩 Atomic Skills Module

The Skill provides complete atomic skills for flexible composition:

| Atomic Skill | Function |
|--------------|----------|
| NavigateToPlatform | Open enterprise platform |
| LoginToPlatform | Auto login to platform |
| NavigateToAgentMenu | Navigate to Agent menu |
| CreateNewAgent | Create new agent |
| BuildWorkflow | Build workflow on canvas |
| PublishAgent | Save and publish agent |
| ExitPlatform | Safe exit and close |

---

## 🎯 Use Cases

### Scenario 1: Enterprise Platform Migration

When switching to a new agent platform:
1. Modify `base_url` in `config.yaml`
2. Optionally adjust `elements` config (learning engine can auto-identify)
3. Continue using the same natural language commands

### Scenario 2: Daily Automation Testing

```
"登录平台，创建测试智能体，发布"
```

### Scenario 3: Batch Tasks

```
"批量查看后台智能体状态"
```

---

## 🔬 Technical Architecture

### 1. BrowserAdapter - Browser Abstraction Layer
- Unified API interface
- Auto OS detection
- Security whitelist
- Smart wait strategies

### 2. LearningEngine - Autonomous Learning Engine
- First visit auto DOM analysis
- Navigation, form, button recognition
- Workflow component extraction
- Local cache

### 3. SelfHealing - AI Self-Healing Engine
- Element failure auto screenshot analysis
- Semantic re-matching
- 3-level retry mechanism
- Auto locator update

### 4. NLPParser - Natural Language Parser
- Intent recognition
- Entity extraction
- Execution plan generation
- Spoken command support

### 5. Orchestrator - Workflow Orchestration
- Atomic skill orchestration
- Flow execution control
- Result aggregation

---

## 📊 Running Tests

### Unit Tests

```bash
# Full flow test
python3 -m tests.test_full_flow

# Login test
python3 -m tests.test_login

# Create Agent test
python3 -m tests.test_create_agent
```

### Logs and Reports

- Execution logs: `logs/` directory
- Screenshots: `logs/screenshots/` directory
- Learning cache: `logs/learning_cache/` directory

---

## 🎮 Demo Mode

Built-in public demo site template, experience without enterprise intranet:

1. Ensure `demo.enabled: true` in `config.yaml`
2. Test with the following command:

```
"前往演示平台测试完整流程"
```

---

## ⚠️ FAQ

### Q: How to adapt to my company's platform?
**A**: Just modify `platform.base_url` in `config.yaml` to your platform address. Element locators can be automatically obtained through the learning engine, or manually configured in the `elements` section.

### Q: Is my credentials safe?
**A**: Credentials are only read from environment variables, never hardcoded in any file, and logs are automatically masked.

### Q: Do I need to rework after platform updates?
**A**: No! The self-healing engine automatically detects changes and re-learns to adapt.

### Q: Which browsers are supported?
**A**: Chrome, Firefox, Edge are supported, configurable in `config.yaml`.

---

## 🏛️ Maintenance Manual

### Trigger Re-learning

```
"重新学习页面结构"
```

### View Learning Cache

```
"显示当前学习的页面元素"
```

### View Logs and Screenshots

Logs and screenshots are automatically saved in `logs/` directory, and automatically saved on failure.

---

## 📝 Version Information

**Version**: 2.0.0 Competition Winning Top Version
**Last Updated**: 2026-05-13
**Key Features**: Universal configurable, Natural Language, AI Self-Healing, Security Whitelist, Atomic Skills
