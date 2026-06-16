import os
import sys
import json
import asyncio

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent

class TaskManagementAgent(BaseAgent):
    """
    Task Management Agent translates priorities and insights into structured follow-up
    tasks using the Gemini API.
    """
    def __init__(self, mcp_manager=None, gemini_client=None):
        super().__init__("Task Management Agent", mcp_manager, gemini_client)

    async def execute(self, task_input: dict) -> dict:
        """
        Creates actionable follow-up tasks from lead priorities and insights.
        
        Args:
            task_input (dict): Context dictionary containing:
                - 'leads': list of scored leads
                - 'executive_summary': executive insights
                
        Returns:
            dict: List of structured follow-up tasks.
        """
        leads = task_input.get("leads", [])
        executive_summary = task_input.get("executive_summary", "")
        
        if not leads:
            self.logger.warning("No leads data available to assign tasks.")
            return {"success": False, "tasks": []}
            
        self.logger.info("Generating action items using Gemini API...")
        
        # Filter top 10 leads to feed into the prompt (to avoid blowing up token limits)
        leads_for_tasks = sorted(leads, key=lambda x: x.get("score", 0), reverse=True)[:10]
        leads_data_subset = []
        for lead in leads_for_tasks:
            leads_data_subset.append({
                "company_name": lead["company_name"],
                "industry": lead["industry"],
                "score": lead["score"],
                "priority_tier": lead["priority_tier"],
                "contact_email": lead.get("contact_email", "")
            })
            
        prompt = f"""
You are an operations assistant. Based on these scored leads and the executive summary, generate a list of 4-7 concrete, assignable follow-up action items.
Each task must target a specific company from the leads list (especially 'Hot' leads) or address a general funnel issue.

Assign roles from this list:
- "Lead Account Executive" (for high value / large revenue deals)
- "Technical Sales Engineer" (for SaaS / complex technical accounts)
- "BizDev Specialist" (for inbound demo follow-ups)
- "Operations Manager" (for general process checks)

Provide the output strictly as a JSON array of objects. Do not wrap it in anything other than the JSON itself.
JSON Schema:
[
  {{
    "lead_company": "Company Name",
    "task_description": "Specific action item description (e.g. Schedule a call to discuss custom pricing)",
    "assignee": "Role Name",
    "priority": "High" or "Medium" or "Low"
  }}
]

Scored Leads Context:
{json.dumps(leads_data_subset, indent=2)}

Executive Summary Context:
{executive_summary}
"""

        tasks = []
        if self.gemini_client:
            try:
                model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
                self.logger.info(f"Invoking Gemini model: {model_name} for task generation")
                
                response = self.gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={"response_mime_type": "application/json"}
                )
                
                tasks = json.loads(response.text)
                self.logger.info(f"Successfully generated {len(tasks)} tasks via Gemini API.")
            except Exception as e:
                self.logger.error(f"Gemini API task generation failed: {str(e)}. Falling back to rule-based tasks.")
                tasks = self._generate_fallback_tasks(leads)
        else:
            self.logger.warning("Gemini Client not provided. Using rule-based fallback tasks.")
            tasks = self._generate_fallback_tasks(leads)
            
        return {
            "success": True,
            "tasks": tasks
        }
        
    def _generate_fallback_tasks(self, leads: list) -> list:
        """
        Creates standard follow-up tasks for Hot and Warm leads.
        """
        tasks = []
        hot_leads = [l for l in leads if l.get("priority_tier") == "Hot"][:3]
        warm_leads = [l for l in leads if l.get("priority_tier") == "Warm"][:2]
        
        for lead in hot_leads:
            assignee = "Lead Account Executive"
            if lead.get("industry") == "SaaS":
                assignee = "Technical Sales Engineer"
                
            tasks.append({
                "lead_company": lead["company_name"],
                "task_description": f"Urgent 24-hour outreach. Prepare high-value pitch custom tailored to {lead['industry']} sector benchmarks.",
                "assignee": assignee,
                "priority": "High"
            })
            
        for lead in warm_leads:
            tasks.append({
                "lead_company": lead["company_name"],
                "task_description": f"Qualify contact requirements and schedule product walkthrough.",
                "assignee": "BizDev Specialist",
                "priority": "Medium"
            })
            
        if not tasks:
            # Fallback if no hot/warm leads
            tasks.append({
                "lead_company": "General Ops",
                "task_description": "Review lead sources and run targeted inbound campaign.",
                "assignee": "Operations Manager",
                "priority": "Low"
            })
            
        return tasks

if __name__ == "__main__":
    agent = TaskManagementAgent()
    result = asyncio.run(agent.execute({
        "leads": [
            {"company_name": "Acme SaaS", "industry": "SaaS", "priority_tier": "Hot", "score": 85},
            {"company_name": "MedCare", "industry": "Healthcare", "priority_tier": "Warm", "score": 55}
        ]
    }))
    print(json.dumps(result["tasks"], indent=2))
