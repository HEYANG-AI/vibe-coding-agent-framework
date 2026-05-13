#!/usr/bin/env python3
"""
🏆 Enterprise Agent Platform Automation Framework
Main Entry Point
"""
import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from core.orchestrator import Orchestrator
from core.tools import Logger, ConfigLoader


def main():
    """Main function"""
    config_loader = ConfigLoader()
    config_loader.load()

    logger = Logger.setup("AirChinaAgentMain", config_loader=config_loader)
    logger.info("=" * 60)
    logger.info("🏆 Enterprise Agent Platform Automation Framework")
    logger.info("=" * 60)

    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
    else:
        command = "执行完整流程：打开→登录→新建→建工作流→保存发布"

    logger.info(f"Command: {command}")

    orchestrator = Orchestrator()
    try:
        result = orchestrator.run(command)

        if result["success"]:
            logger.info("✅ Execution successful!")
        else:
            logger.error("❌ Execution failed!")
            logger.error(result["message"])

        logger.info(f"Result: {result}")

    except KeyboardInterrupt:
        logger.info("User interrupted")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        orchestrator.close()


if __name__ == "__main__":
    main()
