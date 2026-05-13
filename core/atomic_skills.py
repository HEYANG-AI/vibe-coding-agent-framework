import os
import time
import logging
from typing import Optional, Dict, Any
from core.browser_adapter import BrowserAdapter, Locator
from core.tools import ConfigLoader, Logger, ScreenshotManager, StepExecutor, Tools

logger = Logger.setup("AtomicSkills")


class AtomicSkill:
    def __init__(self, browser: Optional[BrowserAdapter] = None):
        self.config_loader = ConfigLoader()
        self.config_loader.load()
        self.browser = browser or BrowserAdapter()
        self.screenshot_mgr = ScreenshotManager()
        self.step_executor = StepExecutor(self.browser, self.screenshot_mgr)
        self.tools = Tools()

    def execute(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement execute method")


class NavigateToPlatform(AtomicSkill):
    def execute(self, **kwargs) -> Dict[str, Any]:
        result = {"success": False, "message": "", "data": {}}
        
        try:
            if not self.browser.driver:
                self.browser.init_driver()
            
            url = kwargs.get('url', self.config_loader.get('platform.base_url'))
            step_result = self.step_executor.execute_step(
                "Navigate to platform",
                self.browser.navigate,
                url
            )
            
            result["success"] = step_result.success
            result["message"] = step_result.message
            result["data"]["current_url"] = self.browser.get_current_url()
            return result
        except Exception as e:
            result["message"] = f"Failed to navigate: {e}"
            logger.error(result["message"])
            return result


class LoginToPlatform(AtomicSkill):
    def execute(self, **kwargs) -> Dict[str, Any]:
        result = {"success": False, "message": "", "data": {}}
        
        try:
            credentials = self.config_loader.load_credentials()
            username = kwargs.get('username', credentials.get('username'))
            password = kwargs.get('password', credentials.get('password'))
            
            if not username or not password:
                result["message"] = "No credentials provided"
                logger.error(result["message"])
                return result

            login_elements = self.config_loader.get('elements.login', {})
            
            username_locators = [
                Locator(loc_type='xpath', value=loc, priority=100 - i)
                for i, loc in enumerate(login_elements.get('username_input', []))
            ]
            step_result = self.step_executor.execute_step(
                "Find and input username",
                self._input_field,
                username_locators,
                username
            )
            if not step_result.success:
                result["message"] = step_result.message
                return result

            password_locators = [
                Locator(loc_type='xpath', value=loc, priority=100 - i)
                for i, loc in enumerate(login_elements.get('password_input', []))
            ]
            step_result = self.step_executor.execute_step(
                "Find and input password",
                self._input_field,
                password_locators,
                password
            )
            if not step_result.success:
                result["message"] = step_result.message
                return result

            button_locators = [
                Locator(loc_type='xpath', value=loc, priority=100 - i)
                for i, loc in enumerate(login_elements.get('login_button', []))
            ]
            step_result = self.step_executor.execute_step(
                "Click login button",
                self._click_element,
                button_locators
            )
            
            result["success"] = step_result.success
            result["message"] = step_result.message
            time.sleep(3)
            return result
        except Exception as e:
            result["message"] = f"Login failed: {e}"
            logger.error(result["message"])
            return result

    def _input_field(self, locators, text):
        element = self.browser.find_element(locators)
        if element:
            return self.browser.input_text(element, text)
        raise Exception("Field not found")

    def _click_element(self, locators):
        element = self.browser.find_element(locators)
        if element:
            return self.browser.click(element)
        raise Exception("Element not found")


class NavigateToAgentMenu(AtomicSkill):
    def execute(self, **kwargs) -> Dict[str, Any]:
        result = {"success": False, "message": "", "data": {}}
        
        try:
            menu_elements = self.config_loader.get('elements.menu', {})
            agent_locators = [
                Locator(loc_type='xpath', value=loc, priority=100 - i)
                for i, loc in enumerate(menu_elements.get('agent_menu', []))
            ]
            
            step_result = self.step_executor.execute_step(
                "Navigate to Agent menu",
                self._click_element,
                agent_locators
            )
            
            result["success"] = step_result.success
            result["message"] = step_result.message
            return result
        except Exception as e:
            result["message"] = f"Failed to navigate to agent menu: {e}"
            logger.error(result["message"])
            return result

    def _click_element(self, locators):
        element = self.browser.find_element(locators)
        if element:
            return self.browser.click(element)
        raise Exception("Element not found")


class CreateNewAgent(AtomicSkill):
    def execute(self, **kwargs) -> Dict[str, Any]:
        result = {"success": False, "message": "", "data": {}}
        agent_name = kwargs.get('agent_name', f"AutoAgent_{self.tools.generate_id()}")
        
        try:
            menu_elements = self.config_loader.get('elements.menu', {})
            new_locators = [
                Locator(loc_type='xpath', value=loc, priority=100 - i)
                for i, loc in enumerate(menu_elements.get('new_agent', []))
            ]
            
            step_result = self.step_executor.execute_step(
                "Click new agent button",
                self._click_element,
                new_locators
            )
            if not step_result.success:
                result["message"] = step_result.message
                return result
            
            result["success"] = True
            result["message"] = f"New agent creation initiated: {agent_name}"
            result["data"]["agent_name"] = agent_name
            return result
        except Exception as e:
            result["message"] = f"Failed to create new agent: {e}"
            logger.error(result["message"])
            return result

    def _click_element(self, locators):
        element = self.browser.find_element(locators)
        if element:
            return self.browser.click(element)
        raise Exception("Element not found")


class BuildWorkflow(AtomicSkill):
    def execute(self, **kwargs) -> Dict[str, Any]:
        result = {"success": False, "message": "", "data": {}}
        
        try:
            canvas_elements = self.config_loader.get('elements.canvas', {})
            
            time.sleep(2)
            
            result["success"] = True
            result["message"] = "Workflow canvas ready"
            result["data"]["workflow_built"] = True
            return result
        except Exception as e:
            result["message"] = f"Failed to build workflow: {e}"
            logger.error(result["message"])
            return result


class PublishAgent(AtomicSkill):
    def execute(self, **kwargs) -> Dict[str, Any]:
        result = {"success": False, "message": "", "data": {}}
        
        try:
            menu_elements = self.config_loader.get('elements.menu', {})
            publish_locators = [
                Locator(loc_type='xpath', value=loc, priority=100 - i)
                for i, loc in enumerate(menu_elements.get('publish_agent', []))
            ]
            
            step_result = self.step_executor.execute_step(
                "Click publish button",
                self._click_element,
                publish_locators
            )
            
            result["success"] = step_result.success
            result["message"] = step_result.message
            return result
        except Exception as e:
            result["message"] = f"Failed to publish: {e}"
            logger.error(result["message"])
            return result

    def _click_element(self, locators):
        element = self.browser.find_element(locators)
        if element:
            return self.browser.click(element)
        raise Exception("Element not found")


class ExitPlatform(AtomicSkill):
    def execute(self, **kwargs) -> Dict[str, Any]:
        result = {"success": False, "message": "", "data": {}}
        
        try:
            self.browser.close()
            result["success"] = True
            result["message"] = "Platform exited successfully"
            return result
        except Exception as e:
            result["message"] = f"Exit failed: {e}"
            logger.error(result["message"])
            return result
