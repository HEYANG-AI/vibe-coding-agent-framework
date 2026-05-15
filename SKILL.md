# Vibe Coding Platform Automation

**企业内网智能体平台全自动浏览器操作 Skill**

> 一句话指令驱动：登录 → 创建智能体 → 搭建工作流 → 配置节点 → 保存发布
>
> 无需任何平台 API，纯 UI 自动化，适配任意企业内网平台。

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Vibe Coding 自然语言接口                    │
│                    (vibe.py — VibeEngine)                    │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│  登录     │ 创建Agent │ 工作流    │ 发布     │ 学习/发现       │
│ (login)  │(create)  │(workflow)│(publish) │ (discover)      │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│                    编排引擎 (Engine)                         │
│             重试 + 审计 + 凭据管理 + 安全日志                  │
├─────────────────────────────────────────────────────────────┤
│  学习引擎(Learner) │  自愈引擎(Healer) │  安全模块(Security)  │
│  DOM分析→元素提取   │  定位失败→自动恢复  │  凭据/审计/脱敏     │
│  多策略选择器生成    │  4种恢复策略       │  企业级安全合规      │
├─────────────────────────────────────────────────────────────┤
│                    Playwright 浏览器自动化                     │
│             Stealth 模式 / 反检测 / 人类行为模拟               │
└─────────────────────────────────────────────────────────────┘
```

## 核心特性

### 🔥 自学习引擎 (Learner)
- 自动扫描页面 DOM，提取所有交互元素
- 智能聚类到功能区域（表单/菜单/工具栏/画布）
- 多策略选择器生成：`data-testid` > text > ID > CSS > XPath
- 页面模型持久化到 JSON，支持增量更新

### 🛡️ 自愈引擎 (Self-Healing)
- 元素定位失败时自动启用 4 级恢复策略
- 文本重匹配 → 语义角色匹配 → 模糊属性匹配 → 页面刷新
- 截图保存现场 + 完整失败报告
- `Locator` 类透明包装所有定位操作

### 🔐 企业安全 (Security)
- 凭据 3 级回退：环境变量 → `.env` 文件 → 交互输入
- 日志自动脱敏密码/Token/Secret/API Key
- 完整审计追踪：JSONL 按日持久化，90 天保留策略
- 运行环境安全检查（root 警告、文件权限检测）

### 🎯 Vibe Coding 自然语言接口
- `python __main__.py vibe "创建一个客服Agent"`
- `python __main__.py vibe "全自动创建智能体并发布"`
- `python __main__.py vibe "搭建工作流: 开始→LLM→结束"`
- 自动意图识别 + 参数提取 + 流程编排

### 🧪 Demo 模式
- 内置模拟 HTTP 服务器，无需真实平台即可测试
- 模拟登录/Dashboard/Agent 列表/工作流编辑器
- 完整的 REST API 模拟

## 快速开始

### 1. 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 2. 配置

编辑 `config.yaml`，修改：

```yaml
platform:
  base_url: "https://你的内网平台地址"
```

设置凭据（三选一）：

```bash
# 方式 1: 环境变量
export AICHINA_USERNAME=你的用户名
export AICHINA_PASSWORD=你的密码
export AICHINA_URL=https://你的平台地址

# 方式 2: .env 文件
echo "AICHINA_USERNAME=你的用户名" >> .env
echo "AICHINA_PASSWORD=你的密码" >> .env

# 方式 3: 交互输入（运行时会提示）
```

### 3. 运行

```bash
# 查看帮助
python __main__.py --help

# Vibe Coding 自然语言模式
python __main__.py vibe "登录平台"
python __main__.py vibe "创建一个叫客服助手的智能体"

# 传统命令模式
python __main__.py login
python __main__.py create-agent --name "测试Agent"
python __main__.py discover  # 学习页面结构

# Demo 模式（无需真实平台）
python __main__.py demo
```

## 使用场景

| 场景 | 命令 |
|------|------|
| 快速登录 | `python __main__.py login` |
| 创建智能体 | `python __main__.py create-agent --name "XX助手"` |
| 页面学习 | `python __main__.py discover` |
| 全自动流程 | `python __main__.py vibe "全自动创建客服Agent并发布"` |
| 启动演示 | `python __main__.py demo` |
| 查看统计 | `python __main__.py healing-stats` |

## 配置文件结构 (`config.yaml`)

- **platform**: 目标平台地址、备用地址、Demo 模式
- **browser**: 浏览器参数（headless/slow_mo/viewport/stealth）
- **credentials**: 凭据前缀配置
- **retry**: 重试策略（次数/延迟/退避）
- **self_healing**: 自愈引擎配置
- **learning**: 学习引擎配置
- **logging**: 日志及审计配置
- **security**: 安全策略（脱敏模式、保留天数）
- **node_types**: 节点类型与界面标签映射
- **workflow_presets**: 内置工作流模板
- **demo**: Demo 模式参数

## 适配任意平台

只需修改 `config.yaml` 中的 `base_url`：

```yaml
platform:
  base_url: "https://你的内网平台地址"
```

Skill 会自动：
1. 学习你平台的页面结构
2. 自适应 UI 差异（不同的 CSS 框架、布局）
3. 记忆优化后的选择器
4. 持续适应 UI 变更

## 平台适配经验 (2026-05)

### 讯飞星辰平台创建流程
当前版本创建智能体的UI流程为三级导航:
1. 「新建智能体」→ 弹出创建方式选择 (提示词创建/工作流创建/数字人创建)
2. 选择「工作流创建」→ 显示工作流模板库
3. 点击「自定义创建」→ 进入空白画布编辑器

### 通用适配策略
对于其他AI Agent平台，建议按以下顺序探索:
1. 找「创建」或「新建」入口按钮
2. 检查是否有创建方式选择 (提示词/工作流/其他)
3. 看是否有模板库 → 找「空白/自定义」选项
4. 进入编辑器后检测画布类型 (React Flow 使用 `.react-flow` 选择器)
5. 侧边栏节点通过 `[draggable="true"]` 识别拖拽项
6. 节点连线通过 `.react-flow__handle` (handle-right/handle-left) 识别连接点
7. 配置面板通常为 Ant Design 抽屉/弹窗

### 关键技术细节
- **Chrome profile 复用**: 复制 Cookies 文件到临时目录，用 `launch_persistent_context` 启动避免 SIGTRAP
- **API 发现**: 在浏览器 JS bundle 搜索 `api/`、`/xingchen-api/` 等关键字
- **频率限制**: 约10次/分钟，超限返回 code 90003，需 1.5s+ 延迟
- **节点拖拽**: `locator.drag_to()` 配合 `target_position` 参数
- **模型选择**: Ant Design Select 用键盘输入搜索然后选匹配项
- **提示词填充**: contenteditable div 用 `innerHTML = text + dispatchEvent(input)`

## 项目结构

```
vibe-coding-platform-automation/
├── __main__.py          # CLI 入口
├── config.yaml          # 通用企业平台配置
├── requirements.txt     # 依赖清单
├── SKILL.md             # 本文档
├── core/
│   ├── engine.py        # 编排引擎（Config + Engine）
│   ├── security.py      # 安全模块（凭据/脱敏/审计）
│   ├── learner.py       # 自学习引擎 v2
│   ├── self_healing.py  # 自愈引擎
│   └── browser.py       # 浏览器管理器
├── flows/
│   ├── login.py         # 登录流程
│   ├── create_agent.py  # 创建 Agent 流程
│   ├── workflow.py      # 工作流构建流程
│   ├── publish.py       # 发布流程
│   └── demo.py          # Demo 模式服务器
├── vibe.py              # Vibe Coding 自然语言引擎
└── tests/
    └── test_all.py      # 测试套件
```

## 赛事亮点

1. **零 API 依赖** — 纯 Playwright 浏览器自动化，适配任意 web 平台
2. **自学习能力** — 首次访问自动学习页面结构，无需预设选择器
3. **自愈能力** — 元素定位失败自动恢复，4 级策略保障稳定
4. **企业级安全** — 凭据隔离、日志脱敏、审计追踪、权限检查
5. **Vibe Coding 接口** — 自然语言驱动，一句话完成复杂流程
6. **Demo 模式** — 内置模拟服务器，无平台也能展示
7. **全配置驱动** — 修改一行 `base_url` 即可适配任意企业内网平台
8. **跨平台兼容** — macOS/Linux/Windows，Python 3.9+

## 许可证

MIT License
