import os
import sys
import json
import asyncio
import pandas as pd

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent

class LeadAnalysisAgent(BaseAgent):
    """
    Lead Analysis Agent loads leads data, queries business knowledge scoring rules,
    calculates lead scores, assigns priority tiers (Hot, Warm, Cold), and ranks them.
    """
    def __init__(self, mcp_manager=None, gemini_client=None):
        super().__init__("Lead Analysis Agent", mcp_manager, gemini_client)

    async def execute(self, task_input: dict) -> dict:
        """
        Calculates scores for leads based on configurable rules.
        
        Args:
            task_input (dict): Contains 'csv_path' (optional) to specify lead dataset.
            
        Returns:
            dict: Scored leads data list and aggregate metrics.
        """
        csv_path = task_input.get("csv_path")
        self.logger.info(f"Starting lead analysis. Dataset source: {csv_path or 'Default Sample'}")
        
        # 1. Fetch lead data from MCP Lead Data Server
        args = {}
        if csv_path:
            args["csv_path"] = csv_path
            
        lead_data_response = await self.call_mcp_tool(
            "Lead Data Server", 
            "load_leads", 
            args
        )
        
        # In mock or real execution, handle response structure
        if isinstance(lead_data_response, str):
            lead_data = json.loads(lead_data_response)
        else:
            lead_data = lead_data_response
            
        if not lead_data.get("success", False):
            raise ValueError(f"Failed to load lead data: {lead_data.get('error')}")
            
        leads = lead_data.get("leads", [])
        self.logger.info(f"Successfully ingested {len(leads)} leads.")
        
        # 2. Fetch scoring rules from MCP Business Knowledge Server
        scoring_rules_response = await self.call_mcp_tool(
            "Business Knowledge Server",
            "get_scoring_rules"
        )
        
        if isinstance(scoring_rules_response, str):
            rules_data = json.loads(scoring_rules_response)
        else:
            rules_data = scoring_rules_response
            
        scoring_rules = rules_data.get("scoring_rules", {})
        priority_tiers = rules_data.get("priority_tiers", {})
        
        # 3. Calculate scores for each lead
        scored_leads = []
        for lead in leads:
            score, explanation = self.score_lead_explainable(lead, scoring_rules)
            
            # Determine Priority Tier
            priority_tier = "Cold"
            for tier, min_score in sorted(priority_tiers.items(), key=lambda x: x[1], reverse=True):
                if score >= min_score:
                    priority_tier = tier
                    break
                    
            lead_copy = lead.copy()
            lead_copy["score"] = score
            lead_copy["priority_tier"] = priority_tier
            lead_copy["score_explanation"] = explanation
            scored_leads.append(lead_copy)
            
        # 4. Sort leads by score descending
        scored_leads_sorted = sorted(scored_leads, key=lambda x: x["score"], reverse=True)
        
        # Calculate summary statistics
        total_leads = len(scored_leads_sorted)
        hot_leads_count = sum(1 for l in scored_leads_sorted if l["priority_tier"] == "Hot")
        warm_leads_count = sum(1 for l in scored_leads_sorted if l["priority_tier"] == "Warm")
        cold_leads_count = sum(1 for l in scored_leads_sorted if l["priority_tier"] == "Cold")
        
        total_pipeline_revenue = sum(float(l.get("annual_revenue", 0)) for l in scored_leads_sorted)
        avg_score = sum(l["score"] for l in scored_leads_sorted) / total_leads if total_leads > 0 else 0
        
        metrics = {
            "total_leads": total_leads,
            "hot_leads": hot_leads_count,
            "warm_leads": warm_leads_count,
            "cold_leads": cold_leads_count,
            "total_revenue": total_pipeline_revenue,
            "avg_score": avg_score
        }
        
        self.logger.info(
            f"Scoring complete. Metrics: {total_leads} leads, {hot_leads_count} Hot, "
            f"Pipeline Revenue: ${total_pipeline_revenue:,.2f}"
        )
        
        return {
            "success": True,
            "leads": scored_leads_sorted,
            "metrics": metrics
        }
        
    def score_lead(self, lead: dict, rules: dict) -> int:
        """
        Helper method to apply scoring math based on business rules.
        """
        score, _ = self.score_lead_explainable(lead, rules)
        return score

    def score_lead_explainable(self, lead: dict, rules: dict) -> tuple[int, dict]:
        """
        Calculates lead score and returns both the score and a detailed points breakdown.
        """
        # A. Revenue Points
        revenue = float(lead.get("annual_revenue", 0))
        rev_brackets = rules.get("revenue_brackets", [])
        revenue_points = 0
        for bracket in sorted(rev_brackets, key=lambda x: x["min"], reverse=True):
            if revenue >= bracket["min"]:
                revenue_points = bracket["points"]
                break
                
        # B. Employee Size Points
        employees = int(lead.get("employee_count", 0))
        emp_brackets = rules.get("employee_brackets", [])
        employee_points = 0
        for bracket in sorted(emp_brackets, key=lambda x: x["min"], reverse=True):
            if employees >= bracket["min"]:
                employee_points = bracket["points"]
                break
                
        # C. Interactions Points
        interactions = int(lead.get("interactions_count", 0))
        interaction_factor = float(rules.get("interaction_factor", 3.0))
        interaction_points = int(interactions * interaction_factor)
        
        # D. Conversion Rate Points
        conv_rate = float(lead.get("estimated_conversion_rate", 0.0))
        conv_weight = float(rules.get("conversion_rate_weight", 20.0))
        conversion_points = int(conv_rate * conv_weight)
        
        total_unfiltered = revenue_points + employee_points + interaction_points + conversion_points
        score = min(total_unfiltered, 100)
        
        explanation = {
            "revenue": {
                "value": f"${revenue:,.2f}",
                "points": revenue_points,
                "description": f"Annual revenue of ${revenue:,.0f} matches bracket tier scoring {revenue_points} points."
            },
            "employees": {
                "value": f"{employees:,}",
                "points": employee_points,
                "description": f"Company size of {employees:,} employees matches bracket tier scoring {employee_points} points."
            },
            "interactions": {
                "value": interactions,
                "points": interaction_points,
                "description": f"{interactions} recorded interactions multiplied by factor {interaction_factor} yields {interaction_points} points."
            },
            "conversion_rate": {
                "value": f"{conv_rate:.2%}",
                "points": conversion_points,
                "description": f"Estimated conversion probability of {conv_rate:.1%} scaled by factor {conv_weight} yields {conversion_points} points."
            },
            "total_unfiltered": total_unfiltered,
            "final_score": score,
            "capped": total_unfiltered > 100,
            "contributors": {
                "agents": ["Lead Analysis Agent"],
                "mcp_tools": [
                    {"server": "Lead Data Server", "tool": "load_leads"},
                    {"server": "Business Knowledge Server", "tool": "get_scoring_rules"}
                ]
            }
        }
        return score, explanation

if __name__ == "__main__":
    # Quick standalone testing
    agent = LeadAnalysisAgent()
    result = asyncio.run(agent.execute({}))
    print(json.dumps(result["metrics"], indent=2))
