"""
CLI 主入口 - 所有自动化操作的命令行接口
"""

import argparse
import json
import sys
import os
from pathlib import Path

from . import __version__
from .browser import BrowserManager
from .login import LoginPage
from .dashboard import Dashboard
from .agent_creator import AgentCreator
from .workflow_builder import WorkflowBuilder
from .publisher import Publisher
from .learner import PageLearner


def setup_logging():
    """配置日志"""
    import logging
    log_dir = Path.home() / ".vibe" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "vibe.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def cmd_login(args):
    """登录平台"""
    browser = BrowserManager(headless=args.headless, browser_type=args.browser)
    try:
        login = LoginPage(browser)
        success = login.login(
            username=args.username,
            password=args.password,
            headless=args.headless,
        )
        if success:
            print("\n✅ 登录成功！")
            if not args.headless:
                print("浏览器保持打开，可继续操作。")
                print("按 Ctrl+C 关闭浏览器。")
                try:
                    import time
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
        else:
            print("\n❌ 登录失败")
            sys.exit(1)
    finally:
        if args.headless:
            browser.close()


def cmd_create_agent(args):
    """创建 Agent"""
    browser = BrowserManager(headless=args.headless, browser_type=args.browser)
    try:
        login = LoginPage(browser)
        if not login.login(headless=args.headless):
            print("❌ 登录失败，无法创建 Agent")
            sys.exit(1)

        creator = AgentCreator(browser)
        agent_id = creator.create_agent(
            name=args.name,
            description=args.description or "",
            template=args.template or "",
        )

        if agent_id and agent_id != "unknown":
            print(f"\n✅ Agent 创建成功！ID: {agent_id}")
            # 保存到文件
            if args.output:
                with open(args.output, "w") as f:
                    json.dump({"agent_id": agent_id, "name": args.name}, f)
                print(f"Agent 信息已保存到: {args.output}")
        else:
            print(f"\n❌ Agent 创建失败")
            sys.exit(1)
    finally:
        if args.headless:
            browser.close()


def cmd_build_workflow(args):
    """构建工作流"""
    browser = BrowserManager(headless=args.headless, browser_type=args.browser)
    try:
        login = LoginPage(browser)
        if not login.login(headless=args.headless):
            print("❌ 登录失败")
            sys.exit(1)

        builder = WorkflowBuilder(browser)

        if args.workflow_file:
            # 从文件加载工作流定义
            with open(args.workflow_file, encoding="utf-8") as f:
                workflow_def = json.load(f)

            if args.agent_id:
                builder.open_workflow_editor(args.agent_id)

            success = builder.build_full_workflow(workflow_def)
        else:
            if not args.agent_id:
                print("❌ 需要指定 --agent-id 或 --workflow-file")
                sys.exit(1)
            builder.open_workflow_editor(args.agent_id)

            # 从命令行参数添加节点
            if args.add_nodes:
                for node_str in args.add_nodes.split(";"):
                    parts = node_str.strip().split(",")
                    ntype = parts[0]
                    label = parts[1] if len(parts) > 1 else ""
                    pos = (int(parts[2]), int(parts[3])) if len(parts) > 3 else None
                    builder.add_node(ntype, position=pos, label=label)

            if args.connect:
                for conn_str in args.connect.split(";"):
                    parts = conn_str.split(",")
                    if len(parts) >= 2:
                        builder.connect_nodes(parts[0], parts[1])

            success = True

        builder.save_workflow()

        if success:
            print(f"\n✅ 工作流构建完成！")
        else:
            print(f"\n❌ 工作流构建失败")
            sys.exit(1)
    finally:
        if args.headless:
            browser.close()


def cmd_add_node(args):
    """在工作流中添加节点"""
    browser = BrowserManager(headless=args.headless, browser_type=args.browser)
    try:
        login = LoginPage(browser)
        if not login.login(headless=args.headless):
            sys.exit(1)

        builder = WorkflowBuilder(browser)
        if args.agent_id:
            builder.open_workflow_editor(args.agent_id)

        pos = None
        if args.position:
            parts = args.position.replace(" ", "").split(",")
            pos = (int(parts[0]), int(parts[1]))

        node_id = builder.add_node(args.node_type, position=pos, label=args.label or "")
        if node_id:
            print(f"✅ 节点添加成功: {node_id}")
        else:
            print(f"❌ 节点添加失败")
            sys.exit(1)
    finally:
        if args.headless:
            browser.close()


def cmd_configure_node(args):
    """配置节点"""
    browser = BrowserManager(headless=args.headless, browser_type=args.browser)
    try:
        login = LoginPage(browser)
        if not login.login(headless=args.headless):
            sys.exit(1)

        builder = WorkflowBuilder(browser)
        if args.agent_id:
            builder.open_workflow_editor(args.agent_id)

        config = json.loads(args.config) if isinstance(args.config, str) else args.config
        success = builder.configure_node(args.source, config)
        if success:
            print(f"✅ 节点配置成功")
        else:
            print(f"❌ 节点配置失败")
            sys.exit(1)
    finally:
        if args.headless:
            browser.close()


def cmd_connect_nodes(args):
    """连接节点"""
    browser = BrowserManager(headless=args.headless, browser_type=args.browser)
    try:
        login = LoginPage(browser)
        if not login.login(headless=args.headless):
            sys.exit(1)

        builder = WorkflowBuilder(browser)
        if args.agent_id:
            builder.open_workflow_editor(args.agent_id)

        success = builder.connect_nodes(args.from_node, args.to_node)
        if success:
            print(f"✅ 节点连接成功")
        else:
            print(f"❌ 节点连接失败")
            sys.exit(1)
    finally:
        if args.headless:
            browser.close()


def cmd_publish(args):
    """发布 Agent"""
    browser = BrowserManager(headless=args.headless, browser_type=args.browser)
    try:
        login = LoginPage(browser)
        if not login.login(headless=args.headless):
            sys.exit(1)

        publisher = Publisher(browser)
        success = publisher.publish(
            agent_id=args.agent_id,
            version=args.version or "",
            message=args.message or "",
        )
        if success:
            print(f"\n✅ 发布成功！")
        else:
            print(f"\n❌ 发布失败")
            sys.exit(1)
    finally:
        if args.headless:
            browser.close()


def cmd_full_workflow(args):
    """一键完成全部流程"""
    browser = BrowserManager(headless=args.headless, browser_type=args.browser)
    try:
        # 1. 登录
        print("=" * 50)
        print("步骤 1/5: 登录平台")
        print("=" * 50)
        login = LoginPage(browser)
        if not login.login(headless=args.headless):
            print("❌ 登录失败")
            sys.exit(1)

        # 2. 创建 Agent
        print("\n" + "=" * 50)
        print("步骤 2/5: 创建 Agent")
        print("=" * 50)
        creator = AgentCreator(browser)
        agent_id = creator.create_agent(
            name=args.name,
            description=args.description or "",
        )
        if not agent_id:
            print("❌ 创建 Agent 失败")
            sys.exit(1)

        # 3. 构建工作流
        print("\n" + "=" * 50)
        print("步骤 3/5: 构建工作流")
        print("=" * 50)
        builder = WorkflowBuilder(browser)
        if args.workflow_file:
            builder.open_workflow_editor(agent_id)
            with open(args.workflow_file, encoding="utf-8") as f:
                workflow_def = json.load(f)
            builder.build_full_workflow(workflow_def)
        else:
            print("跳过工作流构建（未指定 --workflow-file）")

        # 4. 保存
        print("\n" + "=" * 50)
        print("步骤 4/5: 保存工作流")
        print("=" * 50)
        builder.save_workflow()

        # 5. 发布
        print("\n" + "=" * 50)
        print("步骤 5/5: 发布")
        print("=" * 50)
        publisher = Publisher(browser)
        publish_success = publisher.publish(
            agent_id=agent_id,
            version=args.version or "1.0",
            message=args.message or f"初始版本 {args.name}",
        )

        if publish_success:
            print("\n" + "=" * 50)
            print("🎉 全部流程完成！")
            print(f"Agent: {args.name}")
            print(f"Agent ID: {agent_id}")
            print("=" * 50)
        else:
            print("\n⚠️ 发布时出现问题，请检查平台状态")
    finally:
        if args.headless:
            browser.close()


def cmd_discover(args):
    """发现模式 - 分析页面结构"""
    browser = BrowserManager(headless=False, browser_type=args.browser)
    try:
        login = LoginPage(browser)
        login.login(headless=False)

        learner = PageLearner()
        page = browser.page

        print("\n开始分析页面结构...\n")

        # 全面发现
        interactive_map = learner.discover_interactive_map(page)

        print(f"页面: {interactive_map['title']}")
        print(f"URL: {interactive_map['url']}")

        print(f"\n--- 发现 {len(interactive_map['inputs'])} 个输入框 ---")
        for inp in interactive_map['inputs'][:20]:
            hint = inp.get('placeholder') or inp.get('name') or inp.get('id') or ''
            print(f"  <{inp['tag']}> type={inp.get('type','')} hint='{hint}' sel={inp.get('selectors',{}).get('css','')}")

        print(f"\n--- 发现 {len(interactive_map['buttons'])} 个可点击元素 ---")
        for btn in interactive_map['buttons'][:30]:
            print(f"  {btn['text'][:50]} -> {btn['selector']}")

        if interactive_map.get('menus'):
            print(f"\n--- 菜单结构 ---")
            for i, menu in enumerate(interactive_map['menus']):
                items = [item['text'][:20] for item in menu.get('items', [])]
                print(f"  菜单{i+1}: {', '.join(items)}")

        if interactive_map.get('dialogs'):
            print(f"\n--- 弹窗 ---")
            for d in interactive_map['dialogs']:
                if d['visible']:
                    print(f"  弹窗: {d.get('title','')} 按钮: {d.get('buttons',[])}")

        if interactive_map.get('canvas'):
            print(f"\n--- 工作流画布 ---")
            print(f"  大小: {interactive_map['canvas']['size']}")

        # 保存学习模型
        model_types = ["login", "dashboard", "agent-list", "agent-create", "workflow", "publish"]
        for mt in model_types:
            model = learner.load_model(mt)
            if model:
                print(f"\n📚 已加载已学习模型: {mt} (v{model.version})")

        # 学习当前页面
        page_type = learner._detect_page_type(page.url, page.title(), page)
        model = learner.learn_page(page, page_type)
        print(f"\n📚 已学习页面模型: {page_type} (v{model.version})")
        print(f"  发现 {sum(len(r.elements) for r in model.regions)} 个交互元素")
        print(f"  分布在 {len(model.regions)} 个区域")

        if args.output:
            import json
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(interactive_map, f, ensure_ascii=False, indent=2)
            print(f"\n分析结果已保存到: {args.output}")

        print("\n按 Ctrl+C 退出发现模式。")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    finally:
        browser.close()


def cmd_screenshot(args):
    """截图"""
    browser = BrowserManager(headless=False, browser_type=args.browser)
    try:
        login = LoginPage(browser)
        login.login(headless=False)

        path = browser.screenshot(args.output or "screenshot")
        print(f"✅ 截图已保存: {path}")
    finally:
        browser.close()


def cmd_learn(args):
    """主动学习当前页面"""
    browser = BrowserManager(headless=False, browser_type=args.browser)
    try:
        login = LoginPage(browser)
        login.login(headless=False)

        learner = PageLearner()
        page = browser.page

        # 导航到目标
        if args.url:
            page.goto(args.url, wait_until="networkidle")

        browser.random_delay(2000)

        page_type = args.type or learner._detect_page_type(page.url, page.title(), page)
        model = learner.learn_page(page, page_type)

        print(f"✅ 页面学习完成！")
        print(f"  页面类型: {page_type}")
        print(f"  页面标题: {model.title}")
        print(f"  交互元素: {sum(len(r.elements) for r in model.regions)}")
        print(f"  页面区域: {len(model.regions)}")

        for region in model.regions:
            print(f"  📂 {region.name} ({region.element_type}) [{len(region.elements)} 元素]")
            for el in region.elements[:5]:
                best_sel = learner.get_best_selector(el, page_type)
                print(f"    - {el.tag}: \"{el.text[:30]}\" -> {best_sel}")
            if len(region.elements) > 5:
                print(f"    ... 还有 {len(region.elements) - 5} 个元素")

        # 学习导航
        nav_map = learner.learn_navigation(page)
        if nav_map:
            print(f"\n📍 导航结构:")
            for name, href in nav_map.items():
                print(f"   {name} -> {href[:60]}")
    finally:
        browser.close()


def main():
    """CLI 主入口"""
    parser = argparse.ArgumentParser(
        description=f"Air China AI Agent 平台自动化工具 v{__version__}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  vibe login                          # 登录平台
  vibe create-agent --name "客服助手"   # 创建 Agent
  vibe full-workflow --name "客服" --workflow-file workflow.json  # 一键完成
  vibe discover                       # 发现模式分析页面
  vibe learn --type workflow           # 主动学习工作流页面
        """
    )
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    parser.add_argument("--browser", "-b", default="webkit", 
                        choices=["webkit", "chromium", "firefox"],
                        help="浏览器类型：webkit(Safari,默认), chromium(Chrome), firefox")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # login
    p_login = subparsers.add_parser("login", help="登录平台")
    p_login.add_argument("--username", "-u", help="用户名")
    p_login.add_argument("--password", "-p", help="密码")
    p_login.add_argument("--headless", action="store_true")
    p_login.add_argument("--browser", "-b", default="webkit", 
                        choices=["webkit", "chromium", "firefox"],
                        help="浏览器类型：webkit(Safari,默认), chromium(Chrome), firefox")

    # create-agent
    p_create = subparsers.add_parser("create-agent", help="创建 Agent")
    p_create.add_argument("--name", "-n", required=True, help="Agent 名称")
    p_create.add_argument("--description", "-d", help="Agent 描述")
    p_create.add_argument("--template", "-t", help="模板名称")
    p_create.add_argument("--output", "-o", help="保存 Agent 信息到文件")
    p_create.add_argument("--headless", action="store_true")
    p_create.add_argument("--browser", "-b", default="webkit", 
                        choices=["webkit", "chromium", "firefox"],
                        help="浏览器类型：webkit(Safari,默认), chromium(Chrome), firefox")

    # build-workflow
    p_build = subparsers.add_parser("build-workflow", help="构建工作流")
    p_build.add_argument("--agent-id", help="Agent ID")
    p_build.add_argument("--workflow-file", "-f", help="工作流定义 JSON 文件")
    p_build.add_argument("--add-nodes", help="添加节点: type,label,x,y;type2,...")
    p_build.add_argument("--connect", help="连接节点: from,to;from2,to2")
    p_build.add_argument("--headless", action="store_true")
    p_build.add_argument("--browser", "-b", default="webkit", 
                        choices=["webkit", "chromium", "firefox"],
                        help="浏览器类型：webkit(Safari,默认), chromium(Chrome), firefox")

    # add-node
    p_add = subparsers.add_parser("add-node", help="添加工作流节点")
    p_add.add_argument("--agent-id", help="Agent ID")
    p_add.add_argument("--node-type", required=True, help="节点类型")
    p_add.add_argument("--position", help="位置 x,y")
    p_add.add_argument("--label", help="节点标签")
    p_add.add_argument("--headless", action="store_true")
    p_add.add_argument("--browser", "-b", default="webkit", 
                        choices=["webkit", "chromium", "firefox"],
                        help="浏览器类型：webkit(Safari,默认), chromium(Chrome), firefox")

    # configure-node
    p_config = subparsers.add_parser("configure-node", help="配置节点")
    p_config.add_argument("--agent-id", help="Agent ID")
    p_config.add_argument("--source", required=True, help="节点来源（类型或ID）")
    p_config.add_argument("--config", required=True, help="JSON 配置")
    p_config.add_argument("--headless", action="store_true")
    p_config.add_argument("--browser", "-b", default="webkit", 
                        choices=["webkit", "chromium", "firefox"],
                        help="浏览器类型：webkit(Safari,默认), chromium(Chrome), firefox")

    # connect-nodes
    p_conn = subparsers.add_parser("connect-nodes", help="连接节点")
    p_conn.add_argument("--agent-id", required=True)
    p_conn.add_argument("--from", dest="from_node", required=True, help="源节点")
    p_conn.add_argument("--to", dest="to_node", required=True, help="目标节点")
    p_conn.add_argument("--headless", action="store_true")
    p_conn.add_argument("--browser", "-b", default="webkit", 
                        choices=["webkit", "chromium", "firefox"],
                        help="浏览器类型：webkit(Safari,默认), chromium(Chrome), firefox")

    # publish
    p_pub = subparsers.add_parser("publish", help="发布 Agent")
    p_pub.add_argument("--agent-id", required=True)
    p_pub.add_argument("--version", "-v", help="版本号")
    p_pub.add_argument("--message", "-m", help="发布说明")
    p_pub.add_argument("--headless", action="store_true")
    p_pub.add_argument("--browser", "-b", default="webkit", 
                        choices=["webkit", "chromium", "firefox"],
                        help="浏览器类型：webkit(Safari,默认), chromium(Chrome), firefox")

    # full-workflow
    p_full = subparsers.add_parser("full-workflow", help="一键完成全部流程")
    p_full.add_argument("--name", "-n", required=True, help="Agent 名称")
    p_full.add_argument("--description", "-d", help="Agent 描述")
    p_full.add_argument("--workflow-file", "-f", help="工作流定义 JSON 文件")
    p_full.add_argument("--version", help="版本号")
    p_full.add_argument("--message", "-m", help="发布说明")
    p_full.add_argument("--headless", action="store_true")
    p_full.add_argument("--browser", "-b", default="webkit", 
                        choices=["webkit", "chromium", "firefox"],
                        help="浏览器类型：webkit(Safari,默认), chromium(Chrome), firefox")

    # discover
    p_disc = subparsers.add_parser("discover", help="发现模式分析页面")
    p_disc.add_argument("--output", "-o", help="保存分析结果到文件")
    p_disc.add_argument("--browser", "-b", default="webkit", 
                        choices=["webkit", "chromium", "firefox"],
                        help="浏览器类型：webkit(Safari,默认), chromium(Chrome), firefox")

    # screenshot
    p_ss = subparsers.add_parser("screenshot", help="截图调试")
    p_ss.add_argument("--output", "-o", help="保存路径")
    p_ss.add_argument("--agent-id", help="Agent ID")
    p_ss.add_argument("--browser", "-b", default="webkit", 
                        choices=["webkit", "chromium", "firefox"],
                        help="浏览器类型：webkit(Safari,默认), chromium(Chrome), firefox")

    # learn
    p_learn = subparsers.add_parser("learn", help="主动学习页面结构")
    p_learn.add_argument("--url", help="目标 URL")
    p_learn.add_argument("--type", help="页面类型")
    p_learn.add_argument("--browser", "-b", default="webkit", 
                        choices=["webkit", "chromium", "firefox"],
                        help="浏览器类型：webkit(Safari,默认), chromium(Chrome), firefox")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    setup_logging()

    # 检测 headless 参数传递
    if hasattr(args, 'headless'):
        pass  # 各命令自行处理

    # 路由到对应命令
    commands = {
        "login": cmd_login,
        "create-agent": cmd_create_agent,
        "build-workflow": cmd_build_workflow,
        "add-node": cmd_add_node,
        "configure-node": cmd_configure_node,
        "connect-nodes": cmd_connect_nodes,
        "publish": cmd_publish,
        "full-workflow": cmd_full_workflow,
        "discover": cmd_discover,
        "screenshot": cmd_screenshot,
        "learn": cmd_learn,
    }

    cmd = commands.get(args.command)
    if cmd:
        cmd(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
