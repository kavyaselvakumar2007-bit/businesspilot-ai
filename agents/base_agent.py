import os
import sys
import logging

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import logger

class BaseAgent:
    """
    Base Agent class that establishes common interfaces for Gemini API calls,
    MCP server tool execution, and unified logging.
    """
    def __init__(self, name: str, mcp_manager=None, gemini_client=None):
        self.name = name
        self.mcp_manager = mcp_manager
        self.gemini_client = gemini_client
        self.logger = logging.getLogger(f"business_pilot.agents.{name.lower()}")
        self.logger.info(f"Agent '{self.name}' initialized.")

    async def execute(self, task_input: dict) -> dict:
        """
        Execute the agent's core capability. Must be implemented by subclasses.
        
        Args:
            task_input (dict): Context dictionary containing inputs from previous agents.
            
        Returns:
            dict: Results dictionary to be merged into orchestrator context.
        """
        raise NotImplementedError("Each agent must implement the execute method.")

    async def call_mcp_tool(self, server_name: str, tool_name: str, arguments: dict = None) -> dict:
        """
        Helper method to call an MCP server tool through the MCP Manager.
        Includes a fallback to direct python calls or mocks if MCP Manager is not running
        (specifically for independent agent testing).
        """
        arguments = arguments or {}
        import time
        start_time = time.time()
        
        callback = getattr(self, "event_callback", None)
        if callback:
            callback(
                stage=self.name,
                message=f"Invoking MCP tool {tool_name} on {server_name}",
                event_type="tool_start",
                details={"server": server_name, "tool": tool_name, "arguments": arguments}
            )
            
        if self.mcp_manager:
            try:
                self.logger.debug(f"Calling MCP tool: {server_name} -> {tool_name} with args: {arguments}")
                result = await self.mcp_manager.call_tool(server_name, tool_name, arguments)
                duration = time.time() - start_time
                if callback:
                    callback(
                        stage=self.name,
                        message=f"Completed MCP tool {tool_name} on {server_name}",
                        event_type="tool_end",
                        duration=duration,
                        details={"server": server_name, "tool": tool_name, "status": "success"}
                    )
                return result
            except Exception as e:
                duration = time.time() - start_time
                self.logger.error(f"Error calling MCP tool {server_name}/{tool_name}: {str(e)}")
                if callback:
                    callback(
                        stage=self.name,
                        message=f"MCP tool {tool_name} on {server_name} failed: {str(e)}",
                        event_type="error",
                        duration=duration,
                        details={"server": server_name, "tool": tool_name, "status": "failed", "error": str(e)}
                    )
                raise e
        else:
            # MCP Manager is not available (independent test mode). Fall back to mock responses or direct execution.
            self.logger.warning(f"MCP Manager not active. Fallback mock execution for {server_name}/{tool_name}")
            result = await self._mock_mcp_call(server_name, tool_name, arguments)
            duration = time.time() - start_time
            if callback:
                callback(
                    stage=self.name,
                    message=f"Completed MCP tool {tool_name} on {server_name} (Mock Fallback)",
                    event_type="tool_end",
                    duration=duration,
                    details={"server": server_name, "tool": tool_name, "status": "mock_success"}
                )
            return result

    async def _mock_mcp_call(self, server_name: str, tool_name: str, arguments: dict) -> dict:
        """
        Fallback mock implementations for unit testing agents without running full MCP processes.
        """
        import json
        
        if server_name == "Lead Data Server" and tool_name == "load_leads":
            return {
                "success": True, 
                "leads": [
                    {"lead_id": "L999", "company_name": "Test Company", "industry": "SaaS", 
                     "annual_revenue": 5000000, "employee_count": 50, "country": "USA", 
                     "lead_source": "Website Demo", "interactions_count": 5, 
                     "estimated_conversion_rate": 0.60}
                ]
            }
        
        if server_name == "Business Knowledge Server" and tool_name == "get_scoring_rules":
            from config.settings import SCORING_RULES, PRIORITY_TIERS
            return {
                "scoring_rules": SCORING_RULES,
                "priority_tiers": PRIORITY_TIERS
            }
            
        if server_name == "Reporting Server":
            if tool_name == "generate_plotly_charts":
                return {
                    "success": True,
                    "charts": {"score_distribution": "<div>Mock Histogram Chart</div>", "revenue_vs_score": "<div>Mock Scatter Plot</div>"}
                }
            elif tool_name == "compile_html_report":
                return "<html><body><h1>Mock Compiled Report</h1></body></html>"
                
        if server_name == "Notification Server" and tool_name == "send_notification":
            return {"success": True, "channel": "mock", "message": "Notification mocked successfully."}
            
        return {"error": f"No mock implementation for {server_name}/{tool_name}"}
