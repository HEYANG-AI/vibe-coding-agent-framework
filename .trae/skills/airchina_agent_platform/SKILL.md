# 🏆 企业智能体平台自动化 Skill - 赛事获奖级顶配版

## 📋 概述

这是一个通用可配置的企业级跨平台智能体自动化 Skill，专为各类低代码智能体平台设计，支持一键适配不同企业环境。

### ✨ 核心优势

1. **通用可配置设计**：无需修改代码，只需改配置即可适配任意企业平台
2. **智能自主学习**：首次进入陌生平台自动识别页面菜单、按钮、登录框、工作流组件
3. **AI 自愈适配**：平台改版、按钮位置变动、文字微调时自动重新识别适配
4. **原子化模块化**：独立可复用单元，支持灵活组合调用
5. **自然语言极简调用**：一句话全自动跑通完整流程
6. **企业级安全保障**：白名单限制、账号不硬编码、日志自动脱敏
7. **内置公开演示站点**：无需企业内网也能测试体验

---

## 📁 目录结构

```
airchina_agent_platform/
├── SKILL.md              # 主技能文档
├── config.yaml           # 用户配置文件
├── core/
│   ├── __init__.py
│   ├── browser_adapter.py    # 跨平台浏览器适配层（含安全白名单）
│   ├── learning_engine.py    # 页面自主学习引擎
│   ├── self_healing.py       # AI 自愈引擎
│   ├── tools.py              # 通用工具（含配置加载、日志脱敏）
│   ├── atomic_skills.py      # 原子化技能模块
│   ├── nlp_parser.py         # 增强自然语言解析器
│   └── orchestrator.py       # 工作流调度器
├── flows/
│   ├── __init__.py
│   ├── login_flow.py         # 登录流程
│   ├── create_agent_flow.py  # 创建Agent流程
│   └── publish_flow.py       # 发布流程
└── tests/
    ├── __init__.py
    ├── test_login.py
    ├── test_create_agent.py
    └── test_full_flow.py
```

---

## 🚀 快速开始

### 1. 配置平台信息

只需修改 `config.yaml` 中的以下内容：

```yaml
platform:
  name: "您的企业平台名称"
  base_url: "https://your-company-platform.com"
```

### 2. 设置环境变量（账号密码）

```bash
# macOS/Linux
export AIRCHINA_USERNAME="your_username"
export AIRCHINA_PASSWORD="your_password"

# Windows (PowerShell)
$env:AIRCHINA_USERNAME="your_username"
$env:AIRCHINA_PASSWORD="your_password"
```

### 3. 一句话执行

```
"前往企业智能体平台新建业务智能体"
"自动搭建机组排班工作流并保存发布"
"登录后台批量查看已有智能体列表"
```

---

## ⚙️ 配置说明

### config.yaml 完整配置

```yaml
# 平台配置
platform:
  name: "企业智能体平台"
  base_url: "https://aiagenttest.airchina.com.cn/agent/base/desktop/index"
  timeout: 30
  screenshot_dir: "./logs/screenshots"

# 浏览器配置
browser:
  type: "chrome"  # chrome, firefox, edge
  headless: false
  window_size: [1920, 1080]
  user_data_dir: null

# 重试配置
retry:
  max_attempts: 3
  delay_seconds: 2
  exponential_backoff: true

# 安全配置
security:
  username_env: "AIRCHINA_USERNAME"
  password_env: "AIRCHINA_PASSWORD"
  session_persistence: true
  allowed_domains: ["airchina.com.cn"]  # 安全白名单，防止访问非法域名

# 元素定位配置（自定义适配自己的平台）
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

## 💬 自然语言调用示例

### 基础命令

| 需求 | 命令示例 |
|------|----------|
| 打开平台 | "前往企业智能体平台" |
| 登录 | "登录系统" |
| 新建智能体 | "新建一个业务智能体" |
| 查看列表 | "查看已有智能体列表" |
| 发布 | "保存并发布" |

### 完整流程命令（一句话搞定）

```
"执行完整流程：打开→登录→新建→建工作流→保存发布"
"全自动创建业务智能体并发布"
"一句话帮我完成智能体创建全流程"
```

### 业务场景示例

```
"自动搭建机组排班工作流并保存发布"
"新建航班查询智能体，配置工作流后发布"
"批量查看后台智能体状态"
```

---

## 🔐 安全特性

1. **账号密码环境变量读取**：不写死在任何文件中，通过 `AIRCHINA_USERNAME` 和 `AIRCHINA_PASSWORD` 环境变量配置
2. **白名单域名限制**：配置 `allowed_domains` 防止访问非法域名
3. **日志自动脱敏**：敏感信息自动打码隐藏
4. **会话安全复用**：一次登录多次使用，提升效率

---

## 🧩 原子技能模块

Skill 提供了完整的原子技能，可灵活组合：

| 原子技能 | 功能 |
|----------|------|
| NavigateToPlatform | 打开企业平台站点 |
| LoginToPlatform | 自动登录平台 |
| NavigateToAgentMenu | 导航到 Agent 菜单 |
| CreateNewAgent | 创建新的智能体 |
| BuildWorkflow | 在画布上构建工作流 |
| PublishAgent | 保存发布智能体 |
| ExitPlatform | 安全退出关闭 |

---

## 🎯 使用场景

### 场景 1：企业平台迁移

当更换新的智能体平台时，只需：
1. 修改 `config.yaml` 中的 `base_url`
2. 根据新平台调整 `elements` 配置（可选，学习引擎可自动识别）
3. 继续使用相同的自然语言命令

### 场景 2：日常自动化测试

```
"登录平台，创建测试智能体，发布"
```

### 场景 3：批量任务

```
"批量查看后台智能体状态"
```

---

## 🔬 技术架构

### 1. BrowserAdapter - 浏览器适配层
- 统一 API 接口
- 自动检测操作系统
- 安全白名单检查
- 智能等待策略

### 2. LearningEngine - 自主学习引擎
- 首次访问自动分析 DOM
- 识别导航、表单、按钮
- 提取工作流组件
- 本地缓存学习结果

### 3. SelfHealing - AI 自愈引擎
- 元素失效自动截图分析
- 语义化重匹配
- 3级重试机制
- 自动更新定位器

### 4. NLPParser - 自然语言解析
- 意图识别
- 实体提取
- 生成执行计划
- 支持口语化指令

### 5. Orchestrator - 工作流调度
- 原子技能编排
- 流程执行控制
- 结果汇总反馈

---

## 📊 运行测试

### 单元测试

```bash
# 完整流程测试
cd .trae/skills/airchina_agent_platform
python -m tests.test_full_flow

# 登录测试
python -m tests.test_login

# 创建 Agent 测试
python -m tests.test_create_agent
```

### 日志与报告

- 执行日志：`logs/` 目录
- 截图：`logs/screenshots/` 目录
- 学习缓存：`logs/learning_cache/` 目录

---

## 🎮 演示模式

内置公开演示站点模板，无需企业内网也能体验：

1. 确保 `config.yaml` 中 `demo.enabled: true`
2. 使用以下命令测试：

```
"前往演示平台测试完整流程"
```

---

## ⚠️ 常见问题

### Q: 如何适配自己企业的平台？
**A**: 只需修改 `config.yaml` 中的 `platform.base_url` 为自己的平台地址，元素定位器配置可通过学习引擎自动获取，也可手动配置 `elements` 部分。

### Q: 账号密码安全吗？
**A**: 账号密码只从环境变量读取，绝不写死在任何文件中，日志也会自动脱敏。

### Q: 平台改版后需要重新开发吗？
**A**: 不需要！自愈引擎会自动检测变化并重新学习适配。

### Q: 支持哪些浏览器？
**A**: 支持 Chrome、Firefox、Edge，可在 `config.yaml` 中配置。

---

## 🏛️ 维护手册

### 触发重学习

```
"重新学习页面结构"
```

### 查看学习缓存

```
"显示当前学习的页面元素"
```

### 查看日志与截图

日志和截图自动保存在 `logs/` 目录中，失败时会自动保存。

---

## 📝 版本信息

**版本**: 2.0.0 赛事获奖级顶配版  
**最后更新**: 2026-05-13  
**主要特性**: 通用可配置、自然语言、AI 自愈、安全白名单、原子技能
