import logging
import re
from typing import Dict, Any, List
from core.tools import Logger

logger = Logger.setup("NLPParser")


class Intent:
    """意图常量"""
    NAVIGATE = "navigate"
    LOGIN = "login"
    NEW_AGENT = "new_agent"
    LIST_AGENTS = "list_agents"
    BUILD_WORKFLOW = "build_workflow"
    PUBLISH = "publish"
    FULL_FLOW = "full_flow"
    EXIT = "exit"


class NLPParser:
    """增强的自然语言解析器，支持口语指令"""
    
    def __init__(self):
        # 关键词映射表
        self.intent_keywords = {
            Intent.NAVIGATE: [
                "前往", "打开", "导航", "进入", "访问", "去"
            ],
            Intent.LOGIN: [
                "登录", "登陆", "登入", "登录系统", "登录平台"
            ],
            Intent.NEW_AGENT: [
                "新建", "创建", "新的", "新增", "建智能体", "建agent", "建立"
            ],
            Intent.LIST_AGENTS: [
                "查看", "列表", "已有", "查看列表", "浏览", "列表查看"
            ],
            Intent.BUILD_WORKFLOW: [
                "搭建", "创建", "构建", "做工作流", "画", "画工作流", "画布"
            ],
            Intent.PUBLISH: [
                "发布", "上线", "保存发布", "部署", "发布上线"
            ],
            Intent.FULL_FLOW: [
                "完整流程", "全流程", "全部", "自动", "全自动", "一句话", "跑通"
            ],
            Intent.EXIT: [
                "退出", "关闭", "结束", "退出关闭", "安全退出"
            ]
        }
        
        # 业务关键词
        self.business_keywords = {
            "agent": ["智能体", "agent", "业务智能体", "ai智能体"],
            "workflow": ["工作流", "流程", "workflow"],
            "platform": ["平台", "企业平台", "智能体平台", "企业智能体平台"]
        }
        
        # 任务关键词
        self.task_keywords = {
            "机组排班": ["机组排班", "排班", "机组"],
            "业务智能体": ["业务智能体", "业务"],
            "批量": ["批量", "多个", "大量"]
        }

    def parse(self, command: str) -> Dict[str, Any]:
        """
        解析自然语言指令
        
        Args:
            command: 用户输入的自然语言指令
            
        Returns:
            包含意图和实体的字典
        """
        command = command.strip()
        logger.info(f"Parsing command: {command}")
        
        result = {
            "intent": "unknown",
            "entities": {},
            "original_command": command
        }
        
        # 检测意图
        intent_scores = self._calculate_intent_scores(command)
        if intent_scores:
            # 选择得分最高的意图
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            result["intent"] = best_intent[0]
            logger.info(f"Detected intent: {result['intent']}")
            
            # 如果是完整流程，进一步分析任务细节
            if result["intent"] == Intent.FULL_FLOW:
                result["entities"] = self._extract_entities(command)
            else:
                result["entities"] = self._extract_entities(command)
        
        return result

    def _calculate_intent_scores(self, command: str) -> Dict[str, int]:
        """计算每个意图的得分"""
        scores = {}
        command_lower = command.lower()
        
        for intent, keywords in self.intent_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in command:
                    score += 1
            if score > 0:
                scores[intent] = score
        
        return scores

    def _extract_entities(self, command: str) -> Dict[str, Any]:
        """从指令中提取实体"""
        entities = {}
        
        # 提取智能体名称
        name_match = re.search(r'(?:名称|名字|叫|新建)([\w\s]+)', command)
        if name_match:
            entities["agent_name"] = name_match.group(1).strip()
        
        # 提取业务类型
        for task_type, keywords in self.task_keywords.items():
            for keyword in keywords:
                if keyword in command:
                    entities["task_type"] = task_type
                    break
        
        # 提取批量标识
        if any(keyword in command for keyword in ["批量", "多个", "大量"]):
            entities["is_batch"] = True
        
        # 提取是否需要登录
        if any(keyword in command for keyword in self.intent_keywords[Intent.LOGIN]):
            entities["need_login"] = True
        
        # 检测业务关键词
        for entity_type, keywords in self.business_keywords.items():
            for keyword in keywords:
                if keyword in command.lower():
                    entities[entity_type] = True
                    break
        
        return entities

    def get_action_plan(self, parsed_command: Dict[str, Any]) -> List[str]:
        """
        根据解析结果生成执行计划
        
        Args:
            parsed_command: 解析后的指令结果
            
        Returns:
            执行计划步骤列表
        """
        intent = parsed_command["intent"]
        entities = parsed_command["entities"]
        
        plans = {
            Intent.NAVIGATE: ["navigate"],
            Intent.LOGIN: ["navigate", "login"],
            Intent.NEW_AGENT: ["navigate", "login", "navigate_agent", "new_agent"],
            Intent.LIST_AGENTS: ["navigate", "login", "navigate_agent"],
            Intent.BUILD_WORKFLOW: ["navigate", "login", "navigate_agent", "new_agent", "build_workflow"],
            Intent.PUBLISH: ["navigate", "login", "navigate_agent", "new_agent", "build_workflow", "publish"],
            Intent.FULL_FLOW: ["navigate", "login", "navigate_agent", "new_agent", "build_workflow", "publish"],
            Intent.EXIT: ["exit"]
        }
        
        # 检查是否需要登录
        if entities.get("need_login") and "login" not in plans.get(intent, []):
            return ["navigate", "login"] + plans.get(intent, [])
        
        return plans.get(intent, [])
