import os
import sys
import json
from mcp.server.fastmcp import FastMCP

# Ensure the parent directory is in the sys.path so config can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import SCORING_RULES, PRIORITY_TIERS, INDUSTRY_BENCHMARKS

# Initialize FastMCP Server for Business Knowledge
mcp = FastMCP("Business Knowledge Server")

@mcp.tool()
def get_scoring_rules() -> str:
    """
    Retrieve default lead scoring rules, factor weights, and priority thresholds.
    
    Returns:
        str: JSON string containing scoring weights and prioritisation tiers.
    """
    rules = {
        "scoring_rules": SCORING_RULES,
        "priority_tiers": PRIORITY_TIERS
    }
    return json.dumps(rules)

@mcp.tool()
def get_industry_benchmarks() -> str:
    """
    Retrieve market sizes, expected conversion rates, and value benchmarks by industry.
    
    Returns:
        str: JSON string containing industry benchmarks.
    """
    return json.dumps(INDUSTRY_BENCHMARKS)

@mcp.tool()
def get_qualification_guidelines() -> str:
    """
    Get qualitative advice on how to identify and target high-value clients.
    
    Returns:
        str: Markdown formatted business guidelines.
    """
    guidelines = (
        "### High-Value Lead Qualification Guidelines\n\n"
        "1. **Strategic Intent**: Look for leads in high-growth industries (SaaS, E-commerce, Finance) "
        "with an estimated conversion rate above 0.50.\n"
        "2. **Revenue Scaling**: Focus outbound executive outreach on companies with revenue exceeding "
        "their industry threshold (e.g., SaaS > $10M, Healthcare > $25M).\n"
        "3. **Engagement Index**: Leads with more than 5 interactions and website demo source "
        "are highly primed. Flag them for fast-track follow-up.\n"
        "4. **Action Items**: Assign follow-ups for 'Hot' leads within 24 hours."
    )
    return guidelines

if __name__ == "__main__":
    mcp.run()
