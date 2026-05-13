#!/usr/bin/env python3
"""
🏆 企业智能体平台自动化 Skill - 赛事获奖级顶配版
主入口文件
"""
import sys
from pathlib import Path

# 将当前目录加入路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from core.orchestrator import Orchestrator
from core.tools import Logger, ConfigLoader


def main():
    """主函数"""
    # 初始化
    config_loader = ConfigLoader()
    config_loader.load()
    
    logger = Logger.setup("vibe-coding-agent-frameworkAgentMain", config_loader=config_loader)
    logger.info("=" * 60)
    logger.info("🏆 企业智能体平台自动化 Skill - 赛事获奖级顶配版")
    logger.info("=" * 60)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
    else:
        # 默认命令
        command = "执行完整流程：打开→登录→新建→建工作流→保存发布"
    
    logger.info(f"执行命令: {command}")
    
    # 执行
    orchestrator = Orchestrator()
    try:
        result = orchestrator.run(command)
        
        if result["success"]:
            logger.info("✅ 执行成功！")
        else:
            logger.error("❌ 执行失败！")
            logger.error(result["message"])
        
        logger.info(f"详细结果: {result}")
        
    except KeyboardInterrupt:
        logger.info("用户中断执行")
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")
    finally:
        orchestrator.close()


if __name__ == "__main__":
    main()
