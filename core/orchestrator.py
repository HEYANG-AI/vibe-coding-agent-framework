import logging
from typing import Dict, Any, List
from core.browser_adapter import BrowserAdapter
from core.tools import Logger, ConfigLoader
from core.nlp_parser import NLPParser
from core.atomic_skills import (
    NavigateToPlatform,
    LoginToPlatform,
    NavigateToAgentMenu,
    CreateNewAgent,
    BuildWorkflow,
    PublishAgent,
    ExitPlatform
)

logger = Logger.setup("Orchestrator")


class Orchestrator:
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.config_loader.load()
        self.browser = BrowserAdapter()
        self.nlp_parser = NLPParser()
        
        self.skills = {
            "navigate": NavigateToPlatform(self.browser),
            "login": LoginToPlatform(self.browser),
            "navigate_agent": NavigateToAgentMenu(self.browser),
            "new_agent": CreateNewAgent(self.browser),
            "build_workflow": BuildWorkflow(self.browser),
            "publish": PublishAgent(self.browser),
            "exit": ExitPlatform(self.browser)
        }
        
        self.session_active = False
        
    def run(self, command: str) -> Dict[str, Any]:
        logger.info(f"Received command: {command}")
        
        parsed = self.nlp_parser.parse(command)
        
        if parsed["intent"] == "unknown":
            return {
                "success": False,
                "message": "Unable to understand the command. Please try again.",
                "data": {}
            }
        
        plan = self.nlp_parser.get_action_plan(parsed)
        logger.info(f"Execution plan: {plan}")
        
        results = []
        overall_success = True
        
        for step in plan:
            if step in self.skills:
                skill = self.skills[step]
                logger.info(f"Executing skill: {step}")
                
                result = skill.execute(**parsed["entities"])
                results.append({
                    "skill": step,
                    "result": result
                })
                
                if not result["success"]:
                    overall_success = False
                    logger.error(f"Skill {step} failed: {result['message']}")
                    break
                else:
                    logger.info(f"Skill {step} completed successfully")
        
        return {
            "success": overall_success,
            "message": "Execution completed" if overall_success else "Execution failed",
            "data": {
                "parsed_command": parsed,
                "plan": plan,
                "results": results
            }
        }
    
    def close(self):
        try:
            self.browser.close()
            logger.info("Orchestrator closed successfully")
        except Exception as e:
            logger.error(f"Error closing orchestrator: {e}")
