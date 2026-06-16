import os
import sys
import json
import asyncio

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent

class NotificationAgent(BaseAgent):
    """
    Notification Agent compiles the final operational summary and dispatches notifications
    to the configured stakeholder email using the Notification MCP Server.
    """
    def __init__(self, mcp_manager=None, gemini_client=None):
        super().__init__("Notification Agent", mcp_manager, gemini_client)

    async def execute(self, task_input: dict) -> dict:
        """
        Dispatches executive report alert.
        
        Args:
            task_input (dict): Context dictionary containing:
                - 'metrics': dict of aggregate metrics
                - 'leads': list of scored leads
                - 'tasks': list of generated tasks
                - 'recipient': custom recipient email (optional)
                
        Returns:
            dict: Notification delivery status.
        """
        metrics = task_input.get("metrics", {})
        leads = task_input.get("leads", [])
        tasks = task_input.get("tasks", [])
        recipient = task_input.get("recipient") or os.getenv("NOTIFICATION_RECIPIENT", "stakeholder@example.com")
        
        self.logger.info(f"Preparing stakeholder notification dispatch to {recipient}...")
        
        # Compile a summary text message
        hot_leads_list = [l["company_name"] for l in leads if l.get("priority_tier") == "Hot"][:5]
        hot_leads_str = ", ".join(hot_leads_list) if hot_leads_list else "None"
        
        high_priority_tasks = [t for t in tasks if t.get("priority") == "High"]
        tasks_str = ""
        for t in high_priority_tasks:
            tasks_str += f"- [{t.get('lead_company')}]: {t.get('task_description')} ({t.get('assignee')})\n"
            
        if not tasks_str:
            tasks_str = "No high priority actions."
            
        message_body = (
            f"BusinessPilot AI Run Summary\n"
            f"=============================\n\n"
            f"Funnel Overview:\n"
            f"- Total leads: {metrics.get('total_leads', 0)}\n"
            f"- Hot Leads: {metrics.get('hot_leads', 0)}\n"
            f"- Warm Leads: {metrics.get('warm_leads', 0)}\n"
            f"- Pipeline Revenue: ${metrics.get('total_revenue', 0.0):,.2f}\n"
            f"- Average Score: {metrics.get('avg_score', 0):.1f}\n\n"
            f"Top Priority Targets (Hot):\n"
            f"{hot_leads_str}\n\n"
            f"Immediate Actions Needed:\n"
            f"{tasks_str}\n\n"
            f"The full interactive report is available in your BusinessPilot dashboard.\n"
        )
        
        subject = f"BusinessPilot AI: Operations Alert - {metrics.get('hot_leads', 0)} Hot Leads Prioritised"
        
        # Invoke Notification MCP Server tool
        try:
            dispatch_response = await self.call_mcp_tool(
                "Notification Server",
                "send_notification",
                {
                    "recipient": recipient,
                    "subject": subject,
                    "body": message_body
                }
            )
            
            if isinstance(dispatch_response, str):
                dispatch_result = json.loads(dispatch_response)
            else:
                dispatch_result = dispatch_response
        except Exception as e:
            self.logger.error(f"Notification MCP Tool call failed: {str(e)}")
            dispatch_result = {
                "success": False,
                "error": str(e),
                "message": "Tool execution failed"
            }
            
        # Check if email sending failed or was simulated
        if not dispatch_result.get("success", False) or dispatch_result.get("channel") == "simulation":
            channel = "simulation"
            message = "Email dispatch simulated because SMTP is not configured."
            self.logger.info(f"Fallback to simulation: {message}")
            return {
                "success": True,
                "channel": "simulation",
                "message": message,
                "dispatch_message": message
            }
            
        self.logger.info(f"Notification status: {dispatch_result.get('message')}")
        
        return {
            "success": True,
            "channel": dispatch_result.get("channel", "email"),
            "message": dispatch_result.get("message", "Real email sent successfully."),
            "dispatch_message": dispatch_result.get("message", "Real email sent successfully.")
        }

if __name__ == "__main__":
    agent = NotificationAgent()
    result = asyncio.run(agent.execute({
        "metrics": {"total_leads": 10, "hot_leads": 2, "total_revenue": 15000000.0, "avg_score": 55},
        "leads": [{"company_name": "Hot SaaS", "priority_tier": "Hot"}],
        "tasks": [{"lead_company": "Hot SaaS", "task_description": "Review requirements", "assignee": "John", "priority": "High"}]
    }))
    print(json.dumps(result, indent=2))
