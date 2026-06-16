import os
import sys
import json
import pandas as pd
import plotly.express as px
import plotly.io as pio
from mcp.server.fastmcp import FastMCP

# Ensure the parent directory is in the sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize FastMCP Server for Reporting
mcp = FastMCP("Reporting Server")

@mcp.tool()
def generate_plotly_charts(leads_json: str) -> str:
    """
    Generate interactive Plotly charts as HTML divs from leads data.
    
    Args:
        leads_json (str): JSON string representing list of scored leads.
        
    Returns:
        str: JSON containing HTML snippets for two charts (score distribution & industry segment).
    """
    try:
        data = json.loads(leads_json)
        # Handle dict wrapping if it's from load_leads
        if isinstance(data, dict) and "leads" in data:
            data = data["leads"]
            
        df = pd.DataFrame(data)
        
        if df.empty:
            return json.dumps({"error": "No lead data to chart"})
            
        # 1. Lead Score Distribution Histogram
        fig_dist = px.histogram(
            df,
            x="score",
            color="priority_tier",
            color_discrete_map={"Hot": "#ef4444", "Warm": "#f59e0b", "Cold": "#3b82f6"},
            title="Lead Score Distribution by Priority Tier",
            labels={"score": "Lead Score", "count": "Number of Leads", "priority_tier": "Priority Tier"},
            category_orders={"priority_tier": ["Hot", "Warm", "Cold"]},
            nbins=15
        )
        fig_dist.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#1f2937',
            title_font_size=16,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # 2. Revenue vs Score Scatter Plot
        fig_scatter = px.scatter(
            df,
            x="annual_revenue",
            y="score",
            color="priority_tier",
            size="interactions_count",
            hover_name="company_name",
            color_discrete_map={"Hot": "#ef4444", "Warm": "#f59e0b", "Cold": "#3b82f6"},
            title="Annual Revenue vs. Lead Score",
            labels={"annual_revenue": "Annual Revenue ($)", "score": "Lead Score", "priority_tier": "Tier"},
            log_x=True
        )
        fig_scatter.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#1f2937',
            title_font_size=16
        )
        
        # Convert to HTML divs without loading full plotly.js (since the dashboard/page can load from CDN)
        chart_dist_html = pio.to_html(fig_dist, full_html=False, include_plotlyjs='cdn')
        chart_scatter_html = pio.to_html(fig_scatter, full_html=False, include_plotlyjs='cdn')
        
        return json.dumps({
            "success": True,
            "charts": {
                "score_distribution": chart_dist_html,
                "revenue_vs_score": chart_scatter_html
            }
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
def compile_html_report(
    executive_summary: str,
    metrics_json: str,
    leads_json: str,
    tasks_json: str
) -> str:
    """
    Compile a professional, styled HTML executive report including metrics cards and leads tables.
    
    Args:
        executive_summary (str): Executive markdown/text insights.
        metrics_json (str): JSON string containing high-level stats.
        leads_json (str): JSON string containing high-priority scored leads.
        tasks_json (str): JSON string of tasks generated.
        
    Returns:
        str: Styled, single-file HTML report.
    """
    try:
        metrics = json.loads(metrics_json)
        leads = json.loads(leads_json)
        if isinstance(leads, dict) and "leads" in leads:
            leads = leads["leads"]
            
        tasks = json.loads(tasks_json)
        
        # Filter leads to show top 10 ranked in table
        leads_sorted = sorted(leads, key=lambda x: x.get("score", 0), reverse=True)[:10]
        
        # Build lead rows
        lead_rows = ""
        for lead in leads_sorted:
            tier_class = f"badge-{lead.get('priority_tier', 'Cold').lower()}"
            lead_rows += f"""
            <tr>
                <td><strong>{lead.get('company_name')}</strong></td>
                <td>{lead.get('industry')}</td>
                <td>${lead.get('annual_revenue', 0):,}</td>
                <td>{lead.get('interactions_count')}</td>
                <td>{lead.get('estimated_conversion_rate')}</td>
                <td><span class="badge {tier_class}">{lead.get('priority_tier')}</span></td>
                <td><span class="score-pill">{lead.get('score')}</span></td>
            </tr>
            """
            
        # Build tasks rows
        task_rows = ""
        for t in tasks:
            priority_class = f"badge-{t.get('priority', 'medium').lower()}"
            task_rows += f"""
            <tr>
                <td><strong>{t.get('lead_company', 'General')}</strong></td>
                <td>{t.get('task_description')}</td>
                <td>{t.get('assignee')}</td>
                <td><span class="badge {priority_class}">{t.get('priority')}</span></td>
            </tr>
            """

        # Convert executive summary newlines to HTML paragraphs or break tags
        summary_html = executive_summary.replace("\n\n", "</p><p>").replace("\n", "<br>")
        if not summary_html.startswith("<p>"):
            summary_html = f"<p>{summary_html}</p>"

        html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>BusinessPilot AI Executive Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #4f46e5;
            --primary-hover: #4338ca;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --dark: #0f172a;
            --light: #f8fafc;
            --border: #e2e8f0;
            --text-main: #334155;
            --text-muted: #64748b;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #f1f5f9;
            color: var(--text-main);
            line-height: 1.6;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            padding: 40px;
        }}
        
        .header {{
            border-bottom: 2px solid var(--border);
            padding-bottom: 30px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .header h1 {{
            font-size: 28px;
            color: var(--dark);
            font-weight: 700;
        }}
        
        .header .subtitle {{
            color: var(--text-muted);
            font-size: 14px;
            margin-top: 5px;
        }}
        
        .logo-text {{
            font-weight: 800;
            color: var(--primary);
            font-size: 24px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .metric-card {{
            background: var(--light);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }}
        
        .metric-card .value {{
            font-size: 28px;
            font-weight: 700;
            color: var(--dark);
            margin-bottom: 5px;
        }}
        
        .metric-card .label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            font-weight: 600;
        }}
        
        .section-title {{
            font-size: 20px;
            color: var(--dark);
            margin-bottom: 20px;
            font-weight: 600;
            border-left: 4px solid var(--primary);
            padding-left: 12px;
        }}
        
        .insight-box {{
            background: #eef2ff;
            border-left: 4px solid var(--primary);
            border-radius: 4px 8px 8px 4px;
            padding: 25px;
            margin-bottom: 40px;
            color: #3730a3;
        }}
        
        .insight-box p {{
            margin-bottom: 12px;
        }}
        .insight-box p:last-child {{
            margin-bottom: 0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 40px;
        }}
        
        th {{
            background-color: var(--light);
            color: var(--dark);
            text-align: left;
            padding: 14px 16px;
            font-weight: 600;
            font-size: 13px;
            border-bottom: 2px solid var(--border);
        }}
        
        td {{
            padding: 14px 16px;
            border-bottom: 1px solid var(--border);
            font-size: 14px;
        }}
        
        tr:hover td {{
            background-color: #fafaf9;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .badge-hot, .badge-high {{
            background-color: #fee2e2;
            color: var(--danger);
        }}
        
        .badge-warm, .badge-medium {{
            background-color: #fef3c7;
            color: var(--warning);
        }}
        
        .badge-cold, .badge-low {{
            background-color: #dbeafe;
            color: var(--primary);
        }}
        
        .score-pill {{
            background-color: #f1f5f9;
            color: var(--dark);
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 12px;
        }}
        
        .footer {{
            text-align: center;
            padding-top: 30px;
            border-top: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 12px;
            margin-top: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>BusinessPilot AI Executive Report</h1>
                <div class="subtitle">Autonomous Lead Prioritisation & Insights Summary</div>
            </div>
            <div class="logo-text">BusinessPilot.AI</div>
        </div>
        
        <!-- Metrics Section -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="value">{metrics.get('total_leads', 0)}</div>
                <div class="label">Total Leads</div>
            </div>
            <div class="metric-card">
                <div class="value">{metrics.get('hot_leads', 0)}</div>
                <div class="label" style="color: var(--danger)">Hot Leads</div>
            </div>
            <div class="metric-card">
                <div class="value">${metrics.get('total_revenue', 0):,.0f}</div>
                <div class="label">Total Pipeline Revenue</div>
            </div>
            <div class="metric-card">
                <div class="value">{metrics.get('avg_score', 0):.1f}</div>
                <div class="label">Avg Lead Score</div>
            </div>
        </div>
        
        <!-- Insights Summary Section -->
        <div class="section-title">Executive Summary & Recommendations</div>
        <div class="insight-box">
            {summary_html}
        </div>
        
        <!-- Leads Prioritisation Table -->
        <div class="section-title">Top Scored Leads Priority List</div>
        <table>
            <thead>
                <tr>
                    <th>Company</th>
                    <th>Industry</th>
                    <th>Annual Revenue</th>
                    <th>Interactions</th>
                    <th>Conv. Rate</th>
                    <th>Priority Tier</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>
                {lead_rows}
            </tbody>
        </table>
        
        <!-- Action Items Table -->
        <div class="section-title">Follow-up Action Items</div>
        <table>
            <thead>
                <tr>
                    <th>Target Lead</th>
                    <th>Task Description</th>
                    <th>Assignee</th>
                    <th>Priority</th>
                </tr>
            </thead>
            <tbody>
                {task_rows}
            </tbody>
        </table>
        
        <div class="footer">
            Report compiled automatically by BusinessPilot AI Orchestrator. Timestamps recorded in system logs.
        </div>
    </div>
</body>
</html>
"""
        return html_template
    except Exception as e:
        return f"<h3>Error compiling report: {str(e)}</h3>"

if __name__ == "__main__":
    mcp.run()
