import os
import json
import pandas as pd
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server for Lead Data
mcp = FastMCP("Lead Data Server")

DEFAULT_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "sample_leads.csv"
)

@mcp.tool()
def load_leads(csv_path: str | None = None) -> str:
    """
    Loads raw leads from a CSV file.
    
    Args:
        csv_path (str | None): Absolute or relative path to the leads CSV. Defaults to the sample dataset.
        
    Returns:
        str: JSON string containing the list of leads.
    """
    path = csv_path or DEFAULT_CSV_PATH
    if not os.path.exists(path):
        return json.dumps({"error": f"File not found: {path}"})
    
    try:
        df = pd.read_csv(path)
        # Ensure lead_id exists, convert to dict
        data = df.to_dict(orient="records")
        return json.dumps({"success": True, "count": len(data), "leads": data}, default=str)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
def filter_leads(
    csv_path: str | None = None, 
    industry: str | None = None, 
    min_revenue: float | None = None
) -> str:
    """
    Filter leads based on industry and/or minimum annual revenue.
    
    Args:
        csv_path (str | None): Path to the leads CSV.
        industry (str | None): Industry to filter by (e.g., 'SaaS', 'Finance'). Optional.
        min_revenue (float | None): Minimum annual revenue in USD. Optional.
        
    Returns:
        str: JSON list of filtered leads.
    """
    path = csv_path or DEFAULT_CSV_PATH
    if not os.path.exists(path):
        return json.dumps({"error": f"File not found: {path}"})
    
    try:
        df = pd.read_csv(path)
        
        if industry:
            # Case insensitive comparison
            df = df[df['industry'].str.lower() == industry.lower()]
            
        if min_revenue is not None:
            df = df[df['annual_revenue'] >= min_revenue]
            
        data = df.to_dict(orient="records")
        return json.dumps({"success": True, "count": len(data), "leads": data}, default=str)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
def get_lead_stats(csv_path: str | None = None) -> str:
    """
    Get aggregated summary statistics for the leads dataset.
    
    Args:
        csv_path (str | None): Path to the leads CSV.
        
    Returns:
        str: JSON string containing computed statistics.
    """
    path = csv_path or DEFAULT_CSV_PATH
    if not os.path.exists(path):
        return json.dumps({"error": f"File not found: {path}"})
    
    try:
        df = pd.read_csv(path)
        
        stats = {
            "total_leads": int(len(df)),
            "total_revenue": float(df["annual_revenue"].sum()) if "annual_revenue" in df else 0.0,
            "average_revenue": float(df["annual_revenue"].mean()) if "annual_revenue" in df else 0.0,
            "average_interactions": float(df["interactions_count"].mean()) if "interactions_count" in df else 0.0,
            "average_conversion_rate": float(df["estimated_conversion_rate"].mean()) if "estimated_conversion_rate" in df else 0.0,
            "industry_breakdown": df["industry"].value_counts().to_dict() if "industry" in df else {},
            "source_breakdown": df["lead_source"].value_counts().to_dict() if "lead_source" in df else {}
        }
        return json.dumps({"success": True, "statistics": stats})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

if __name__ == "__main__":
    mcp.run()
