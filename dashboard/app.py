import os
import sys
import asyncio
import json
import time
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import logger, GEMINI_API_KEY
from orchestrator.mcp_manager import MCPManager
from orchestrator.orchestrator import BusinessPilotOrchestrator
from agents.lead_analysis_agent import LeadAnalysisAgent
from agents.business_insights_agent import BusinessInsightsAgent
from agents.task_management_agent import TaskManagementAgent
from agents.report_generation_agent import ReportGenerationAgent
from agents.notification_agent import NotificationAgent

# Page Configuration
st.set_page_config(
    page_title="BusinessPilot AI - Operations Hub",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Streamlit session state defaults safely
if "results" not in st.session_state:
    st.session_state["results"] = {}

if "tasks" not in st.session_state:
    st.session_state["tasks"] = []

if "logs" not in st.session_state:
    st.session_state["logs"] = []

if "current_run_id" not in st.session_state:
    st.session_state["current_run_id"] = None

if "run_timestamp" not in st.session_state:
    st.session_state["run_timestamp"] = None

if "app_mode" not in st.session_state:
    st.session_state["app_mode"] = "📊 Executive Dashboard"

if "running" not in st.session_state:
    st.session_state["running"] = False

if "timeline" not in st.session_state:
    st.session_state["timeline"] = []

# Custom Premium Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main-title {
        font-size: 42px;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    
    .subtitle {
        font-size: 16px;
        color: #64748b;
        margin-bottom: 30px;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        text-align: center;
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.08);
    }
    
    .metric-val {
        font-size: 32px;
        font-weight: 700;
        color: #1e293b;
    }
    
    .metric-lbl {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        font-weight: 600;
        margin-top: 5px;
    }
    
    .timeline-log {
        background: #0f172a;
        color: #38bdf8;
        font-family: 'Courier New', monospace;
        padding: 15px;
        border-radius: 8px;
        font-size: 13px;
        line-height: 1.5;
        max-height: 350px;
        overflow-y: auto;
        border-left: 4px solid #6366f1;
        margin-bottom: 20px;
    }
    
    .kanban-column {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 15px;
        min-height: 400px;
    }
    
    .kanban-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .priority-high { border-left: 4px solid #ef4444; }
    .priority-medium { border-left: 4px solid #f59e0b; }
    .priority-low { border-left: 4px solid #3b82f6; }
</style>
""", unsafe_allow_html=True)

# Clean string to be safe for Helvetica PDF rendering (replaces emojis and non-latin1 characters)
def clean_pdf_text(text):
    if not text:
        return ""
    text = text.replace("✅", "[SUCCESS]").replace("❌", "[FAILED]")
    text = text.replace("🚀", "[AGENT]").replace("⚙️", "[TOOL]")
    text = text.replace("✔️", "[COMPLETED]").replace("⚠️", "[WARNING]")
    text = text.replace("💰", "Revenue").replace("👥", "Employees")
    text = text.replace("⚡", "Interactions").replace("📈", "Conversion")
    text = text.replace("🏢", "Company").replace("👤", "Assignee")
    text = text.replace("🔴", "HIGH").replace("🟡", "MEDIUM").replace("🔵", "LOW")
    text = text.replace("📋", "TO DO").replace("⚡", "IN PROGRESS")
    text = text.replace("✔️", "COMPLETED")
    
    cleaned = []
    for char in text:
        if ord(char) < 256:
            cleaned.append(char)
        else:
            cleaned.append("?")
    return "".join(cleaned)

# PDF compiler using fpdf2
def compile_pdf_report(executive_summary, metrics, leads, tasks, output_path):
    try:
        from fpdf import FPDF
        
        class PDFReport(FPDF):
            def header(self):
                self.set_font("Helvetica", "B", 14)
                self.cell(0, 10, "BusinessPilot AI - Executive Operations Report", 0, 1, "C")
                self.set_draw_color(180, 180, 180)
                self.line(10, 20, 200, 20)
                self.ln(10)
            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", "I", 8)
                self.cell(0, 10, f"Page {self.page_no()}/{{nb}} - Generated by BusinessPilot AI", 0, 0, "C")
                
        pdf = PDFReport()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # Section 1: Executive Summary Metrics
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "1. Executive Funnel Metrics Summary", 0, 1)
        pdf.set_font("Helvetica", "", 10)
        
        pdf.cell(0, 6, clean_pdf_text(f"Total Ingested Leads: {metrics.get('total_leads', 0)}"), 0, 1)
        pdf.cell(0, 6, clean_pdf_text(f"Hot Leads (Score >= 70): {metrics.get('hot_leads', 0)}"), 0, 1)
        pdf.cell(0, 6, clean_pdf_text(f"Warm Leads (40-69): {metrics.get('warm_leads', 0)}"), 0, 1)
        pdf.cell(0, 6, clean_pdf_text(f"Cold Leads (< 40): {metrics.get('cold_leads', 0)}"), 0, 1)
        pdf.cell(0, 6, clean_pdf_text(f"Total Pipeline Revenue: ${metrics.get('total_revenue', 0.0):,.2f}"), 0, 1)
        pdf.cell(0, 6, clean_pdf_text(f"Average Lead Score: {metrics.get('avg_score', 0.0):.1f}"), 0, 1)
        pdf.ln(5)
        
        # Section 2: Market Insights & Sales Trends
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "2. Market Insights & Sales Trends", 0, 1)
        pdf.set_font("Helvetica", "", 10)
        
        summary_clean = clean_pdf_text(executive_summary)
        pdf.multi_cell(0, 5, summary_clean)
        pdf.ln(5)
        
        # Section 3: Top Scored Leads Priority List
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "3. Top Scored Leads Priority List", 0, 1)
        
        # Draw table headers
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(60, 6, "Company", 1, 0)
        pdf.cell(30, 6, "Industry", 1, 0)
        pdf.cell(40, 6, "Revenue", 1, 0)
        pdf.cell(20, 6, "Score", 1, 0)
        pdf.cell(30, 6, "Priority", 1, 1)
        
        pdf.set_font("Helvetica", "", 9)
        for lead in sorted(leads, key=lambda x: x.get("score", 0), reverse=True)[:10]:
            pdf.cell(60, 6, clean_pdf_text(str(lead.get("company_name", ""))[:30]), 1, 0)
            pdf.cell(30, 6, clean_pdf_text(str(lead.get("industry", ""))), 1, 0)
            pdf.cell(40, 6, clean_pdf_text(f"${float(lead.get('annual_revenue', 0)):,.0f}"), 1, 0)
            pdf.cell(20, 6, clean_pdf_text(str(lead.get("score", 0))), 1, 0)
            pdf.cell(30, 6, clean_pdf_text(str(lead.get("priority_tier", ""))), 1, 1)
        pdf.ln(5)
        
        # Section 4: Follow-up Tasks Table
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "4. Follow-up Action Items (Kanban)", 0, 1)
        
        # Draw table headers
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(50, 6, "Company", 1, 0)
        pdf.cell(90, 6, "Description", 1, 0)
        pdf.cell(30, 6, "Assignee", 1, 0)
        pdf.cell(20, 6, "Priority", 1, 1)
        
        pdf.set_font("Helvetica", "", 8)
        for task in tasks:
            pdf.cell(50, 6, clean_pdf_text(str(task.get("lead_company", ""))[:25]), 1, 0)
            desc = clean_pdf_text(str(task.get("task_description", ""))[:55])
            pdf.cell(90, 6, desc, 1, 0)
            pdf.cell(30, 6, clean_pdf_text(str(task.get("assignee", ""))), 1, 0)
            pdf.cell(20, 6, clean_pdf_text(str(task.get("priority", ""))), 1, 1)
            
        pdf.output(output_path)
        return True
    except Exception as e:
        logger.error(f"Failed to generate PDF report: {str(e)}")
        return False

# Helper to compile timeline to premium visual HTML
def compile_timeline_to_html(events):
    if not events:
        return "<p style='color: #64748b; font-family: sans-serif;'>Waiting for execution to start...</p>"
        
    html = """
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap">
<div style="font-family: 'Outfit', sans-serif; background: #0f172a; padding: 20px; border-radius: 12px; border: 1px solid #1e293b; max-height: 410px; overflow-y: auto;">
<div style="position: relative; border-left: 2px solid #334155; margin-left: 15px; padding-left: 20px; padding-top: 5px;">
"""
    
    for event in events:
        timestamp = event["timestamp"].split(" ")[-1] if " " in event["timestamp"] else event["timestamp"]
        stage = event["stage"]
        event_type = event["event_type"]
        message = event["message"]
        duration = event["duration"]
        
        # Decide bullet color and icon
        if event_type == "agent_start":
            bullet_color = "#3b82f6"
            icon = "🚀"
        elif event_type == "agent_end":
            bullet_color = "#10b981"
            icon = "✅"
        elif event_type == "tool_start":
            bullet_color = "#a855f7"
            icon = "⚙️"
        elif event_type == "tool_end":
            bullet_color = "#8b5cf6"
            icon = "✔️"
        elif event_type == "error":
            bullet_color = "#ef4444"
            icon = "❌"
        elif event_type == "retry":
            bullet_color = "#f59e0b"
            icon = "⚠️"
        else:
            bullet_color = "#64748b"
            icon = "ℹ️"
            
        dur_str = f" <span style='color: #a855f7; font-size: 11px; font-weight: bold;'>({duration:.2f}s)</span>" if duration is not None else ""
        
        html += f"""
<div style="margin-bottom: 20px; position: relative;">
<span style="position: absolute; left: -29px; top: 2px; background: {bullet_color}; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; font-size: 9px; border: 2px solid #0f172a; box-shadow: 0 0 8px {bullet_color};"></span>
<div style="color: #f8fafc; font-size: 13px; font-weight: 700; display: flex; justify-content: space-between; align-items: center;">
<span>{icon} {stage} {dur_str}</span>
<span style="color: #64748b; font-size: 10px; font-weight: 400;">{timestamp}</span>
</div>
<div style="color: #94a3b8; font-size: 12px; margin-top: 3px; font-family: monospace; line-height: 1.4;">
{message}
</div>
</div>
"""
        
    html += """
</div>
</div>
"""
    cleaned_lines = [line.strip() for line in html.split("\n")]
    return "\n".join(cleaned_lines)

# Helper to render timeline using native Streamlit status components
def render_timeline_native(events, placeholder):
    if not events:
        placeholder.info("The live multi-agent execution timeline will appear here in real-time once you run BusinessPilot AI.")
        return

    with placeholder.container():
        for event in events:
            timestamp = event.get("timestamp", "")
            if " " in timestamp:
                timestamp = timestamp.split(" ")[-1]
            stage = event.get("stage", "Unknown Agent")
            event_type = event.get("event_type", "info")
            message = event.get("message", "")
            duration = event.get("duration")
            
            dur_str = f" ({duration:.2f}s)" if duration is not None else ""
            
            icon = "⚪"
            if event_type in ["agent_end", "tool_end"]:
                icon = "🟢"
                status_func = st.success
            elif event_type in ["agent_start", "tool_start", "info"]:
                icon = "🔵"
                status_func = st.info
            elif event_type == "error":
                icon = "🔴"
                status_func = st.error
            elif event_type == "retry":
                icon = "🟡"
                status_func = st.warning
            else:
                icon = "🔵"
                status_func = st.info
                
            status_func(f"{icon} [{timestamp}]\n\n{stage}\n\n{message}{dur_str}")

# Helper function to move Kanban task status and persist changes
def move_task(task_index, new_status):
    tasks = st.session_state.get("tasks", [])
    if task_index < len(tasks):
        tasks[task_index]["status"] = new_status
        st.session_state["tasks"] = tasks
        # Persist to active run JSON file
        run_id = st.session_state.get("current_run_id")
        if run_id:
            history_dir = os.path.join("data", "history")
            history_file_path = os.path.join(history_dir, f"{run_id}.json")
            if os.path.exists(history_file_path):
                try:
                    with open(history_file_path, "r", encoding="utf-8") as f:
                        run_data = json.load(f)
                    run_data["tasks"] = tasks
                    with open(history_file_path, "w", encoding="utf-8") as f:
                        json.dump(run_data, f, indent=2, default=str)
                    # also update results context tasks
                    results = st.session_state.get("results", {})
                    if results and "context" in results:
                        results["context"]["tasks"] = tasks
                        st.session_state["results"] = results
                except Exception as e:
                    logger.error(f"Failed to persist task status update: {str(e)}")

# Helper function to execute async orchestrator pipeline with UI updates
async def run_pipeline_streamed(csv_path, recipient, api_key, timeline_placeholder):
    """
    Executes the multi-agent orchestration steps sequentially,
    updating Streamlit components as each agent runs.
    """
    import time
    st.session_state["logs"] = []
    st.session_state["timeline"] = []
    
    def log_timeline_event(stage, message, event_type="info", duration=None, details=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        event = {
            "timestamp": timestamp,
            "stage": stage,
            "event_type": event_type,
            "message": message,
            "duration": duration,
            "details": details or {}
        }
        timeline = st.session_state.get("timeline", [])
        timeline.append(event)
        st.session_state["timeline"] = timeline
        
        # also print standard string log for compatibility
        time_str = datetime.now().strftime("%H:%M:%S")
        logs = st.session_state.get("logs", [])
        logs.append(f"[{time_str}] [{stage}] {message}")
        st.session_state["logs"] = logs
        logger.info(f"[{stage}] [{event_type}] {message}")
        
        # render timeline dynamically
        html = compile_timeline_to_html(timeline)
        timeline_placeholder.markdown(html, unsafe_allow_html=True)
    
    log_timeline_event("Initialization", "Initializing BusinessPilot AI Multi-Agent Pipeline...", "info")
    
    # Setup Gemini API key
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
        from google import genai
        try:
            gemini_client = genai.Client(api_key=api_key)
            log_timeline_event("Initialization", "Gemini Client connected successfully.", "info")
        except Exception as e:
            gemini_client = None
            log_timeline_event("Initialization", f"Failed to load Gemini Client: {str(e)}. Fallback mode active.", "retry")
    else:
        gemini_client = None
        log_timeline_event("Initialization", "No Gemini API Key provided. Running in fallback mode.", "retry")
        
    mcp_manager = MCPManager()
    
    context = {
        "csv_path": csv_path,
        "recipient": recipient,
        "leads": [],
        "metrics": {},
        "executive_summary": "",
        "tasks": [],
        "report_results": {},
        "notification_results": {}
    }
    
    try:
        # Step 1: Boot MCP Servers
        log_timeline_event("MCP Boot", "Spawning Lead, Knowledge, Reporting, and Notification MCP Servers...", "info")
        await mcp_manager.start_all()
        log_timeline_event("MCP Boot", "MCP Servers online. Dynamic tools registered.", "info")
        
        # Instantiate Agents
        lead_agent = LeadAnalysisAgent(mcp_manager, gemini_client)
        insights_agent = BusinessInsightsAgent(mcp_manager, gemini_client)
        task_agent = TaskManagementAgent(mcp_manager, gemini_client)
        report_agent = ReportGenerationAgent(mcp_manager, gemini_client)
        notify_agent = NotificationAgent(mcp_manager, gemini_client)
        
        # Inject timeline event callback to intercept MCP tool invocations
        lead_agent.event_callback = log_timeline_event
        insights_agent.event_callback = log_timeline_event
        task_agent.event_callback = log_timeline_event
        report_agent.event_callback = log_timeline_event
        notify_agent.event_callback = log_timeline_event
        
        # Step 2: Lead Analysis
        log_timeline_event("Lead Analysis Agent", "Ingesting and prioritizing lead database...", "agent_start")
        start_t = time.time()
        
        lead_results = None
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                lead_results = await lead_agent.execute(context)
                if not lead_results.get("success", False):
                    raise RuntimeError(lead_results.get("error", "Lead scoring returned failure status"))
                break
            except Exception as e:
                if attempt < max_retries:
                    log_timeline_event("Lead Analysis Agent", f"Attempt {attempt+1} failed: {str(e)}. Retrying...", "retry")
                    await asyncio.sleep(1)
                else:
                    log_timeline_event("Lead Analysis Agent", f"Failed after {max_retries} retries: {str(e)}", "error")
                    raise e
                    
        duration = time.time() - start_t
        context["leads"] = lead_results["leads"]
        context["metrics"] = lead_results["metrics"]
        log_timeline_event("Lead Analysis Agent", f"Completed scoring. prioritized {len(context['leads'])} leads.", "agent_end", duration=duration)
        
        # Step 3: Business Insights
        log_timeline_event("Business Insights Agent", "Generating summary analysis and sales insights...", "agent_start")
        start_t = time.time()
        
        insights_results = None
        for attempt in range(max_retries + 1):
            try:
                insights_results = await insights_agent.execute(context)
                if not insights_results.get("success", False):
                    raise RuntimeError(insights_results.get("error", "Insights returned failure status"))
                break
            except Exception as e:
                if attempt < max_retries:
                    log_timeline_event("Business Insights Agent", f"Attempt {attempt+1} failed: {str(e)}. Retrying...", "retry")
                    await asyncio.sleep(1)
                else:
                    log_timeline_event("Business Insights Agent", f"Failed after {max_retries} retries: {str(e)}", "error")
                    raise e
                    
        duration = time.time() - start_t
        context["executive_summary"] = insights_results["executive_summary"]
        log_timeline_event("Business Insights Agent", "Completed summary trend analysis.", "agent_end", duration=duration)
        
        # Step 4: Task Management
        log_timeline_event("Task Management Agent", "Translating insights into actionable Kanban follow-up items...", "agent_start")
        start_t = time.time()
        
        task_results = None
        for attempt in range(max_retries + 1):
            try:
                task_results = await task_agent.execute(context)
                if not task_results.get("success", False):
                    raise RuntimeError(task_results.get("error", "Task generator returned failure status"))
                break
            except Exception as e:
                if attempt < max_retries:
                    log_timeline_event("Task Management Agent", f"Attempt {attempt+1} failed: {str(e)}. Retrying...", "retry")
                    await asyncio.sleep(1)
                else:
                    log_timeline_event("Task Management Agent", f"Failed after {max_retries} retries: {str(e)}", "error")
                    raise e
                    
        duration = time.time() - start_t
        context["tasks"] = task_results["tasks"]
        log_timeline_event("Task Management Agent", f"Completed. Generated {len(context['tasks'])} tasks.", "agent_end", duration=duration)
        
        # Step 5: Report Generation
        log_timeline_event("Report Generation Agent", "Compiling executive dashboard report HTML...", "agent_start")
        start_t = time.time()
        
        report_results = None
        for attempt in range(max_retries + 1):
            try:
                report_results = await report_agent.execute(context)
                if not report_results.get("success", False):
                    raise RuntimeError(report_results.get("error", "Report compiler returned failure status"))
                break
            except Exception as e:
                if attempt < max_retries:
                    log_timeline_event("Report Generation Agent", f"Attempt {attempt+1} failed: {str(e)}. Retrying...", "retry")
                    await asyncio.sleep(1)
                else:
                    log_timeline_event("Report Generation Agent", f"Failed after {max_retries} retries: {str(e)}", "error")
                    raise e
                    
        duration = time.time() - start_t
        context["report_results"] = report_results
        log_timeline_event("Report Generation Agent", "Completed HTML executive report compilation.", "agent_end", duration=duration)
        
        # Step 6: Notification Dispatch
        log_timeline_event("Notification Agent", "Dispatching final operations alert to stakeholder...", "agent_start")
        start_t = time.time()
        
        notify_results = None
        for attempt in range(max_retries + 1):
            try:
                notify_results = await notify_agent.execute(context)
                if not notify_results.get("success", False):
                    raise RuntimeError(notify_results.get("error", "Notification dispatch returned failure status"))
                break
            except Exception as e:
                if attempt < max_retries:
                    log_timeline_event("Notification Agent", f"Attempt {attempt+1} failed: {str(e)}. Retrying...", "retry")
                    await asyncio.sleep(1)
                else:
                    log_timeline_event("Notification Agent", f"Failed after {max_retries} retries: {str(e)}", "error")
                    raise e
                    
        duration = time.time() - start_t
        context["notification_results"] = notify_results
        log_timeline_event("Notification Agent", f"Completed. Channel: {notify_results.get('channel')}.", "agent_end", duration=duration)
        
        # PERSISTENCE IMPLEMENTATION
        # Generate Run ID
        run_id = f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        st.session_state["current_run_id"] = run_id
        st.session_state["run_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save HTML and Markdown reports
        reports_dir = os.path.join("data", "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        html_report_path = os.path.join(reports_dir, f"{run_id}_report.html")
        md_report_path = os.path.join(reports_dir, f"{run_id}_report.md")
        pdf_report_path = os.path.join(reports_dir, f"{run_id}_report.pdf")
        
        with open(html_report_path, "w", encoding="utf-8") as f:
            f.write(context["report_results"].get("html_content", ""))
            
        with open(md_report_path, "w", encoding="utf-8") as f:
            f.write(context["report_results"].get("md_content", ""))
            
        # Compile PDF Report
        pdf_success = compile_pdf_report(
            executive_summary=context["executive_summary"],
            metrics=context["metrics"],
            leads=context["leads"],
            tasks=context["tasks"],
            output_path=pdf_report_path
        )
        
        if pdf_success:
            log_timeline_event("Report Generation Agent", "Compiled PDF report saved to data/reports.", "info")
        else:
            log_timeline_event("Report Generation Agent", "Failed to compile PDF report. Fallback to HTML/Markdown only.", "retry")
            
        # Add status field and timestamp to tasks
        for t in context["tasks"]:
            t["status"] = "To Do"
            t["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        # Store tasks in session state
        st.session_state["tasks"] = context["tasks"]
        
        # Save historical run JSON
        history_dir = os.path.join("data", "history")
        os.makedirs(history_dir, exist_ok=True)
        
        run_data = {
            "run_id": run_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dataset_name": os.path.basename(csv_path) if csv_path else "sample_leads.csv",
            "dataset_path": csv_path or "data/sample_leads.csv",
            "metrics": context["metrics"],
            "leads": context["leads"],
            "tasks": context["tasks"],
            "executive_summary": context["executive_summary"],
            "timeline": st.session_state.get("timeline", []),
            "html_report_path": html_report_path,
            "md_report_path": md_report_path,
            "pdf_report_path": pdf_report_path if pdf_success else "",
            "html_content": context["report_results"].get("html_content", ""),
            "md_content": context["report_results"].get("md_content", ""),
            "status": "Success"
        }
        
        history_file_path = os.path.join(history_dir, f"{run_id}.json")
        with open(history_file_path, "w", encoding="utf-8") as f:
            json.dump(run_data, f, indent=2, default=str)
            
        log_timeline_event("Persistence", f"Execution run {run_id} metadata and reports saved successfully.", "info")
        
        log_timeline_event("Success", "BusinessPilot AI multi-agent pipeline executed successfully.", "info")
        return {"success": True, "context": context}
        
    except Exception as e:
        log_timeline_event("Failed", f"Pipeline aborted due to exception: {str(e)}", "error")
        return {"success": False, "error": str(e)}
        
    finally:
        # Crucial cleanup
        log_timeline_event("Cleanup", "Shutting down MCP server subprocesses...", "info")
        await mcp_manager.stop_all()
        log_timeline_event("Cleanup", "Orchestrator cleanup finished.", "info")

# Initialize session state for navigation
if "app_mode" not in st.session_state:
    st.session_state["app_mode"] = "📊 Executive Dashboard"

# Sidebar Panel
st.sidebar.markdown("## ✈️ BusinessPilot AI")
app_mode = st.sidebar.radio(
    "Navigation",
    ["📊 Executive Dashboard", "🔧 MCP Observability", "📜 Pipeline History", "🏛️ System Architecture", "ℹ️ About BusinessPilot AI", "🚀 Capabilities & Demo Guide", "📈 Project Statistics"],
    index=["📊 Executive Dashboard", "🔧 MCP Observability", "📜 Pipeline History", "🏛️ System Architecture", "ℹ️ About BusinessPilot AI", "🚀 Capabilities & Demo Guide", "📈 Project Statistics"].index(st.session_state.get("app_mode", "📊 Executive Dashboard"))
)
st.session_state["app_mode"] = app_mode

st.sidebar.markdown("### 🛠️ Configuration")

# API Key Security Check
if GEMINI_API_KEY:
    st.sidebar.success("Gemini API: Configured ✅")
else:
    st.sidebar.error("Gemini API: Missing ❌")

# Stakeholder Email
recipient_input = st.sidebar.text_input(
    "Stakeholder Email",
    value="stakeholder@example.com",
    help="Stakeholder notification recipient email."
)

# Resolve dataset and show preview
target_csv_path = None
df = pd.DataFrame()

st.sidebar.markdown("### 📊 Dataset Source")
uploaded_file = st.sidebar.file_uploader("Upload custom Leads CSV", type=["csv"])

if uploaded_file is not None:
    # 1. Enforce max size (5MB limit)
    MAX_SIZE_BYTES = 5 * 1024 * 1024
    if uploaded_file.size > MAX_SIZE_BYTES:
        st.sidebar.error("❌ Upload aborted: File exceeds the maximum allowed size of 5MB.")
    else:
        # 2. Enforce file type extension and reject dangerous patterns
        filename = uploaded_file.name
        # Sanitize filename (remove characters that could be used for path traversal)
        safe_filename = os.path.basename(filename)
        safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in [".", "-", "_"])
        
        if not safe_filename.lower().endswith(".csv"):
            st.sidebar.error("❌ Upload aborted: Rejected file format. Only CSV files are accepted.")
        else:
            os.makedirs(os.path.join("data", "uploads"), exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_csv_path = os.path.join("data", "uploads", f"{timestamp}_{safe_filename}")
            
            try:
                with open(target_csv_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                df = pd.read_csv(target_csv_path)
            except Exception as e:
                st.sidebar.error(f"❌ Error loading uploaded file: {str(e)}")
else:
    sample_path = os.path.join("data", "sample_leads.csv")
    if os.path.exists(sample_path):
        target_csv_path = sample_path
        try:
            df = pd.read_csv(sample_path)
        except Exception as e:
            st.sidebar.error(f"Error reading sample file: {str(e)}")
    else:
        st.sidebar.error("Sample leads CSV not found!")

# Show dataset preview in sidebar
if not df.empty:
    with st.sidebar.expander("📄 Dataset Ingestion Preview", expanded=True):
        st.write(f"**File:** {uploaded_file.name if uploaded_file else 'sample_leads.csv'}")
        st.write(f"**Rows:** {len(df)}")
        st.write(f"**Columns:** {', '.join(df.columns.tolist())}")
        st.markdown("**First 5 rows:**")
        st.dataframe(df.head(5), height=150)

# Sidebar Persistence & Runs Section
st.sidebar.markdown("### 💾 Persistence & Runs")
history_dir = os.path.join("data", "history")
os.makedirs(history_dir, exist_ok=True)
run_files = [f for f in os.listdir(history_dir) if f.endswith(".json")]
num_runs = len(run_files)

active_run_id = st.session_state.get("current_run_id")

if active_run_id:
    st.sidebar.success(f"Current Run: `{active_run_id}`")
    st.sidebar.caption("Reports saved successfully in `data/reports/` ✅")
else:
    st.sidebar.info("No active run ID. Load history or execute pipeline.")

st.sidebar.metric("Historical Runs Available", num_runs)

# Sidebar Filters (only if pipeline has been run successfully)
filtered_df = pd.DataFrame()
if st.session_state.get("results", {}).get("success", False):
    leads_df = pd.DataFrame(
        st.session_state.get("results", {})
        .get("context", {})
        .get("leads", [])
    )

    if not leads_df.empty and "industry" in leads_df.columns:
        st.sidebar.markdown("### 🔍 Filter Leads")
        unique_industries = sorted(
            leads_df["industry"].dropna().unique().tolist()
        )
        selected_industries = st.sidebar.multiselect(
            "Select Industry",
            options=unique_industries,
            default=unique_industries
        )
        unique_tiers = ["Hot", "Warm", "Cold"]
        selected_tiers = st.sidebar.multiselect(
            "Select Lead Tier",
            options=unique_tiers,
            default=unique_tiers
        )
        filtered_df = leads_df[
            (leads_df["industry"].isin(selected_industries)) &
            (leads_df["priority_tier"].isin(selected_tiers))
        ]

# Route to MCP Observability page if selected
if app_mode == "🔧 MCP Observability":
    st.markdown("<div class='main-title'>🔧 Model Context Protocol (MCP) Observability</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Real-time tool inspection and multi-agent system registry</div>", unsafe_allow_html=True)
    
    # Beginners Guide Expander
    with st.expander("📚 Beginner's Guide: What is MCP and Why it Matters?", expanded=True):
        st.write("""
        ### What is Model Context Protocol (MCP)?
        The **Model Context Protocol (MCP)** is an open-standard communication protocol designed by Anthropic. It allows LLMs (Large Language Models) to interact with external data sources and execution environments (called "tools") using a standardized API client-server architecture.
        
        ### Why Tool Interoperability Matters
        Normally, coupling an AI agent to a database or API requires writing custom glue code for every agent. MCP decouples the LLM from the services:
        1. **Standardization:** Any client supporting MCP can query tools from any server supporting MCP without custom code.
        2. **Modularity:** Developers can modify tools, databases, or API protocols on the server side without rebuilding the core agent orchestration.
        3. **Security:** MCP servers run in isolated sandboxes or subprocesses, exposing only specific methods (tools) via stdio JSON-RPC channels.
        
        ### How BusinessPilot AI uses MCP Servers
        BusinessPilot AI launches **four independent FastMCP Python servers** as local subprocesses:
        * **Lead Data Server:** Loads and filters lead CSV records.
        * **Business Knowledge Server:** Hosts standard lead scoring weights and benchmarks.
        * **Reporting Server:** Builds Plotly figures and compiles executive HTML report files.
        * **Notification Server:** Connects to SMTP systems to dispatch alerts.
        
        During execution, agents invoke these tools dynamically via standard JSON-RPC packets sent over standard input/output.
        """)
        
    st.markdown("### 🏛️ Active MCP Server Registry")
    
    # We display details for each server
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        with st.container(border=True):
            st.markdown("#### 📂 Lead Data Server")
            st.write("**Script Path:** `mcp_servers/lead_data_server.py` ")
            st.write("**Exposed Tools:**")
            st.markdown("- `load_leads` *(Ingest lead lists)*")
            st.markdown("- `filter_leads` *(Search by industry/revenue)*")
            st.markdown("- `get_lead_stats` *(Calculate raw dataset aggregates)*")
            
        with st.container(border=True):
            st.markdown("#### 📊 Reporting Server")
            st.write("**Script Path:** `mcp_servers/reporting_server.py` ")
            st.write("**Exposed Tools:**")
            st.markdown("- `generate_plotly_charts` *(Render chart HTML divs)*")
            st.markdown("- `compile_html_report` *(Compile executive report page)*")
            
    with col_s2:
        with st.container(border=True):
            st.markdown("#### 🧠 Business Knowledge Server")
            st.write("**Script Path:** `mcp_servers/business_knowledge_server.py` ")
            st.write("**Exposed Tools:**")
            st.markdown("- `get_scoring_rules` *(Fetch scoring point brackets)*")
            st.markdown("- `get_industry_benchmarks` *(Fetch industry average targets)*")
            st.markdown("- `get_qualification_guidelines` *(Fetch sales advice markdown)*")
            
        with st.container(border=True):
            st.markdown("#### 🔔 Notification Server")
            st.write("**Script Path:** `mcp_servers/notification_server.py` ")
            st.write("**Exposed Tools:**")
            st.markdown("- `send_notification` *(SMTP Gmail / simulated console logs)*")
            
    st.markdown("---")
    st.markdown("### ⚡ Live Agent ↔ MCP Interoperability Telemetry")
    
    # We compute tools call stats from st.session_state.get("timeline")
    timeline = st.session_state.get("timeline", [])
    if timeline:
        # filter for tool end events
        tool_ends = [e for e in timeline if e.get("event_type") == "tool_end" or e.get("event_type") == "error"]
        
        if tool_ends:
            telemetry_data = []
            for e in tool_ends:
                details = e.get("details", {})
                status = "Success ✅" if details.get("status") == "success" or details.get("status") == "mock_success" else "Failed ❌"
                telemetry_data.append({
                    "Timestamp": e["timestamp"],
                    "Agent (Client)": e["stage"],
                    "MCP Server": details.get("server", "Unknown"),
                    "MCP Tool": details.get("tool", "Unknown"),
                    "Duration (s)": f"{e.get('duration', 0.0):.3f}s",
                    "Status": status
                })
            st.dataframe(pd.DataFrame(telemetry_data), use_container_width=True)
            
            # Simple metrics summary
            st.markdown("##### Invocation Metrics")
            t_col1, t_col2, t_col3 = st.columns(3)
            total_invokes = len(tool_ends)
            failed_invokes = sum(1 for e in tool_ends if e.get("event_type") == "error")
            success_invokes = total_invokes - failed_invokes
            avg_tool_dur = sum(e.get("duration", 0.0) for e in tool_ends) / total_invokes if total_invokes > 0 else 0.0
            
            t_col1.metric("Total Tool Invocations", total_invokes)
            t_col2.metric("Success Rate", f"{(success_invokes/total_invokes)*100:.1f}%" if total_invokes > 0 else "N/A")
            t_col3.metric("Avg Execution Time", f"{avg_tool_dur:.3f}s")
        else:
            st.info("No tool calls recorded in this session's run yet. Execute the pipeline from the dashboard first.")
    else:
        st.info("No run logs found in the active session. Go to the Executive Dashboard tab and run the workflow to gather telemetry.")
        
    st.markdown("---")
    st.markdown("### 🗺️ Multi-Agent ↔ MCP Interoperability Architecture")
    
    # Render Mermaid diagram via HTML container with MermaidJS
    mermaid_code = """
    graph LR
        subgraph Agents
            LA[Lead Analysis Agent]
            IA[Business Insights Agent]
            TM[Task Management Agent]
            RG[Report Generation Agent]
            NA[Notification Agent]
        end
        
        subgraph MCP Servers
            LDS[Lead Data Server]
            BKS[Business Knowledge Server]
            RPS[Reporting Server]
            NTS[Notification Server]
        end
        
        LA -->|load_leads| LDS
        LA -->|get_scoring_rules| BKS
        RG -->|generate_plotly_charts| RPS
        RG -->|compile_html_report| RPS
        NA -->|send_notification| NTS
        
        style LA fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
        style IA fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
        style TM fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
        style RG fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
        style NA fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
        
        style LDS fill:#faf5ff,stroke:#7e22ce,stroke-width:2px;
        style BKS fill:#faf5ff,stroke:#7e22ce,stroke-width:2px;
        style RPS fill:#faf5ff,stroke:#7e22ce,stroke-width:2px;
        style NTS fill:#faf5ff,stroke:#7e22ce,stroke-width:2px;
    """
    
    st.markdown("""
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({startOnLoad:true});</script>
    """, unsafe_allow_html=True)
    
    # Render using HTML
    html_content = f"""
    <div class="mermaid" style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #cbd5e1; display: flex; justify-content: center;">
    {mermaid_code}
    </div>
    """
    components.html(html_content, height=350)
    st.stop()

# Route to Pipeline History page if selected
if app_mode == "📜 Pipeline History":
    st.markdown("<div class='main-title'>📜 Pipeline Execution History</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Browse and reload prior BusinessPilot AI agent executions</div>", unsafe_allow_html=True)
    
    history_dir = os.path.join("data", "history")
    os.makedirs(history_dir, exist_ok=True)
    history_files = sorted([f for f in os.listdir(history_dir) if f.endswith(".json")], reverse=True)
    
    if not history_files:
        st.info("No historical runs found in storage yet. Go to the Executive Dashboard tab and run the workflow to save a run.")
    else:
        # Load summaries
        runs_list = []
        for file in history_files:
            try:
                with open(os.path.join(history_dir, file), "r", encoding="utf-8") as f:
                    rdata = json.load(f)
                runs_list.append({
                    "file_name": file,
                    "run_id": rdata.get("run_id"),
                    "timestamp": rdata.get("timestamp"),
                    "dataset": rdata.get("dataset_name"),
                    "leads_count": rdata.get("metrics", {}).get("total_leads", 0),
                    "pipeline_value": rdata.get("metrics", {}).get("total_revenue", 0.0),
                    "status": rdata.get("status", "Success")
                })
            except Exception as e:
                logger.error(f"Failed to read history run {file}: {str(e)}")
                
        # Render table or list of runs
        for i, run in enumerate(runs_list):
            with st.container(border=True):
                col_info, col_actions = st.columns([3, 1])
                with col_info:
                    st.markdown(f"#### 🏷️ Run: `{run['run_id']}`")
                    st.write(f"**Timestamp:** {run['timestamp']} | **Dataset:** `{run['dataset']}`")
                    st.write(f"**Ingested Leads:** {run['leads_count']} | **Pipeline Revenue:** ${run['pipeline_value']:,.2f}")
                    
                    # check report paths
                    reports = []
                    hist_run_id = run['run_id']
                    if os.path.exists(os.path.join("data", "reports", f"{hist_run_id}_report.html")):
                        reports.append("HTML 📄")
                    if os.path.exists(os.path.join("data", "reports", f"{hist_run_id}_report.md")):
                        reports.append("MD 📝")
                    if os.path.exists(os.path.join("data", "reports", f"{hist_run_id}_report.pdf")):
                        reports.append("PDF 📕")
                    st.write(f"**Saved Reports:** {', '.join(reports) if reports else 'None'}")
                    
                with col_actions:
                    st.write("")
                    st.write("")
                    if st.button("🔄 Load Run", key=f"load_{run['run_id']}", use_container_width=True):
                        try:
                            with open(os.path.join(history_dir, run['file_name']), "r", encoding="utf-8") as f:
                                loaded_data = json.load(f)
                                
                            # Restore session state
                            st.session_state["results"] = {
                                "success": loaded_data.get("status") == "Success",
                                "context": {
                                    "leads": loaded_data.get("leads"),
                                    "metrics": loaded_data.get("metrics"),
                                    "executive_summary": loaded_data.get("executive_summary"),
                                    "tasks": loaded_data.get("tasks"),
                                    "report_results": {
                                        "html_content": loaded_data.get("html_content") or "",
                                        "md_content": loaded_data.get("md_content") or "",
                                        "html_report_path": loaded_data.get("html_report_path") or "",
                                        "md_report_path": loaded_data.get("md_report_path") or "",
                                        "pdf_report_path": loaded_data.get("pdf_report_path") or ""
                                    },
                                    "notification_results": {
                                        "channel": "history",
                                        "dispatch_message": "Loaded from history record."
                                    }
                                }
                            }
                            st.session_state["tasks"] = loaded_data.get("tasks")
                            st.session_state["timeline"] = loaded_data.get("timeline")
                            st.session_state["current_run_id"] = loaded_data.get("run_id")
                            st.session_state["run_timestamp"] = loaded_data.get("timestamp")
                            
                            st.success(f"Successfully loaded run {loaded_data.get('run_id')} into dashboard!")
                            st.session_state["app_mode"] = "📊 Executive Dashboard"
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to load run: {str(e)}")
                            
                    if st.button("🗑️ Delete Run", key=f"delete_{run['run_id']}", use_container_width=True):
                        try:
                            os.remove(os.path.join(history_dir, run['file_name']))
                            
                            # delete associated reports
                            r_html = os.path.join("data", "reports", f"{run['run_id']}_report.html")
                            r_md = os.path.join("data", "reports", f"{run['run_id']}_report.md")
                            r_pdf = os.path.join("data", "reports", f"{run['run_id']}_report.pdf")
                            
                            if os.path.exists(r_html): os.remove(r_html)
                            if os.path.exists(r_md): os.remove(r_md)
                            if os.path.exists(r_pdf): os.remove(r_pdf)
                            
                            # Clean up active run state if the active run is deleted
                            if st.session_state.get("current_run_id") == run["run_id"]:
                                st.session_state["results"] = None
                                st.session_state["tasks"] = []
                                st.session_state["timeline"] = []
                                st.session_state["current_run_id"] = None
                                st.session_state["run_timestamp"] = None
                                
                            st.success(f"Run {run['run_id']} deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete run: {str(e)}")
                            
    st.stop()

# Route to System Architecture page if selected
if app_mode == "🏛️ System Architecture":
    st.markdown("<div class='main-title'>🏛️ System Architecture</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Decoupled Agent Orchestration & Model Context Protocol boundaries</div>", unsafe_allow_html=True)
    
    st.markdown("### 🗺️ End-to-End Orchestration Workflow")
    # Show Mermaid Flow
    flow_code = """
    graph TD
        User([User Dashboard]) -->|Ingest Leads CSV| Orch[Orchestrator]
        Orch -->|1. Scoring Rules & Filter| LA[Lead Analysis Agent]
        LA -->|stdio RPC| LDS[Lead Data Server]
        LA -->|stdio RPC| BKS[Business Knowledge Server]
        
        Orch -->|2. Generate Advisory Summary| IA[Insights Agent]
        IA -->|Analyze Scored Leads| Gemini[Gemini API]
        
        Orch -->|3. Compile Follow-up Actions| TM[Task Agent]
        TM -->|Convert Summary to Actions| Gemini
        
        Orch -->|4. Generate Visual Analytics| RG[Report Agent]
        RG -->|stdio RPC| RPS[Reporting Server]
        RG -->|Compile PDF| PDF[FPDF2 Generator]
        
        Orch -->|5. Stakeholder Communication| NA[Notification Agent]
        NA -->|stdio RPC| NTS[Notification Server]
        
        Orch -->|Sync Run Details| Hist[(data/history/)]
    """
    
    st.markdown("""
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({startOnLoad:true});</script>
    """, unsafe_allow_html=True)
    
    html_content = f"""
    <div class="mermaid" style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #cbd5e1; display: flex; justify-content: center;">
    {flow_code}
    </div>
    """
    components.html(html_content, height=420)
    
    st.markdown("### 📁 Project Component Breakdown")
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("#### 🤖 Autonomous AI Agents (`agents/`)")
            st.write("**Lead Analysis Agent**: Priority ranking engine calculating Explainable AI metrics.")
            st.write("**Business Insights Agent**: Translates scored lead patterns into advisory summaries via Gemini API.")
            st.write("**Task Management Agent**: Maps summaries to follow-up action items with role assignments.")
            st.write("**Report Generation Agent**: Coordinates reporting servers to generate HTML/MD and PDF layouts.")
            st.write("**Notification Agent**: Sends operation receipts and emails via notification servers.")
            
        with st.container(border=True):
            st.markdown("#### ⚙️ FastMCP Local Servers (`mcp_servers/`)")
            st.write("**Lead Data Server**: Manages CSV list parsing and lead filters.")
            st.write("**Business Knowledge Server**: Exposes lead scoring rules and thresholds.")
            st.write("**Reporting Server**: Compiles Plotly figure components and HTML sheets.")
            st.write("**Notification Server**: Runs mock console logger or SMTP mailer.")
            
    with col2:
        with st.container(border=True):
            st.markdown("#### ✈️ Core Orchestration (`orchestrator/`)")
            st.write("**MCP Manager (`mcp_manager.py`)**: Spawns FastMCP servers as local subprocesses, binds stdin/stdout pipelines, and handles client JSON-RPC tool runs.")
            st.write("**Orchestrator (`orchestrator.py`)**: Runs agent execution pipelines, manages contexts, logs telemetry events, and catches exceptions.")
            
        with st.container(border=True):
            st.markdown("#### 💾 Local Persistence (`data/`)")
            st.write("`data/uploads/` — Sanitized dataset uploads.")
            st.write("`data/reports/` — Stored HTML, MD, and PDF reports.")
            st.write("`data/history/` — JSON execution run histories.")
            
    st.stop()

# Route to About page if selected
if app_mode == "ℹ️ About BusinessPilot AI":
    st.markdown("<div class='main-title'>ℹ️ About BusinessPilot AI</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Core vision, problem statements, and technical design decisions</div>", unsafe_allow_html=True)
    
    col_v, col_t = st.columns([2, 1])
    with col_v:
        st.markdown("### 🎯 Project Vision")
        st.write("""
        BusinessPilot AI was built to solve a major issue in AI business tools—**transparency**. 
        Most agent platforms are black boxes. Operations managers trigger runs and receive outputs, but have no insight into *why* the AI prioritized a particular lead or what tools were called.
        
        Our vision is to build an **autonomous AI employee** that runs the operations workflow with full explainability, real-time telemetry, and modular tool boundaries.
        """)
        
        st.markdown("### ⚠️ The Problem Statement")
        st.write("""
        B2B sales teams lose hundreds of hours to operational overhead:
        1. **Inefficient Data Ingestion**: Customer datasets are loaded manually from flat files.
        2. **Gut-Feeling scoring**: Priority lists are ranked based on arbitrary rules or intuition.
        3. **Disconnected Systems**: Sales analysts must compile scoring, write reports, and assign follow-ups in separate applications.
        """)
        
        st.markdown("### 💼 Business Value Generated")
        st.write("""
        - **Immediate Time Savings**: Automates ingestion, scoring, insights, task assignment, and stakeholder alerting in a single click.
        - **Trustworthy Scoring**: Point-by-point XAI scorecards audit the score calculation, building user trust.
        - **Zero Maintenance Tool Boundaries**: Isolates DB and utility tools into local servers, allowing database migrations without changing agent prompts.
        """)
        
    with col_t:
        st.markdown("### 🛠️ Technology Stack")
        st.markdown("""
        * **Orchestrator**: Python, Asynchronous Asyncio
        * **LLM Engine**: Google Gemini API (`google-genai` SDK)
        * **Tool Boundary**: Model Context Protocol (FastMCP)
        * **Dashboard**: Streamlit (Native UI components)
        * **Analytics**: Plotly (Funnel, Bar, Scatter)
        * **Persistence**: Flat File JSON
        * **PDF Compiler**: FPDF2
        * **Deployment**: Docker / Docker Compose
        """)
        
        st.markdown("### 🛡️ Design Decisions")
        st.markdown("""
        1. **FastMCP local standard input/output (stdio)**: Avoided network port overhead by launching servers as standard OS subprocess pipes.
        2. **Explainable AI (XAI) scorecard math**: Lead scores are broken down into transparent point increments to provide audit trails.
        3. **Top-Down State Synchronization**: Maintains consistent session state on interactive click actions (like dragging Kanban tasks) using flat-file writes.
        """)
        
    st.stop()

# Route to Capabilities & Demo Guide if selected
if app_mode == "🚀 Capabilities & Demo Guide":
    st.markdown("<div class='main-title'>🚀 Capabilities & Demo Guide</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>User guide, sample prompts, and recruiter interview talking points</div>", unsafe_allow_html=True)
    
    tab_guide, tab_talking = st.tabs(["📖 Demo & User Guide", "💼 Career & Recruiter Talking Points"])
    
    with tab_guide:
        st.markdown("### 📄 Step-by-Step Demo Guide")
        st.write("""
        1. **Ingest Data**: Upload a custom CSV list in the sidebar (enforces 5MB max, CSV extensions only) or let it fall back to the default `sample_leads.csv`.
        2. **Execute Workflow**: Go to Tab 1 (**Workspace & Execution**) and click **Run BusinessPilot AI**. Watch the tracer logs update in real-time.
        3. **Audit Scoring**: Go to Tab 2 (**Lead Funnel Analytics**). Scroll down to the Score Explainability section, select a company, and review the points breakdown.
        4. **Move Kanban Tasks**: Go to Tab 4 (**Follow-up Task Board**). Click **Start** or **Complete** on tasks to see them transition between columns.
        5. **Download Reports**: Go to Tab 3 (**Executive Report View**). Download the compiled HTML, Markdown, or PDF report.
        6. **Manage History**: Navigate to `📜 Pipeline History` in the sidebar. You can reload previous pipeline sessions or delete runs.
        """)
        
        st.markdown("### 💡 Sample Prompts for System Agents")
        st.write("""
        The platform prompts agents dynamically using templates. Here are the core instructions:
        - **Lead Analysis Agent**: *\"Calculate scoring point contributions for each lead based on annual revenue, employee count, conversion probability, and interactions.\"*
        - **Business Insights Agent**: *\"Summarize B2B sales trends and industry qualification guidelines. Expose market insights and average benchmarks.\"*
        - **Task Management Agent**: *\"Generate 4-7 follow-up tasks targeting Hot and Warm leads. Assign roles from Lead AE, Technical Sales Engineer, and BizDev Specialist.\"*
        """)
        
    with tab_talking:
        st.markdown("### 🗣️ Recruiter Screen Pitch (30 seconds)")
        st.info("""
        "I recently built BusinessPilot AI, an autonomous sales operations platform. It deploys a team of specialized AI agents that ingest datasets, score leads, write reports, and alert stakeholders. 
        What makes it unique is the **Model Context Protocol (MCP)** architecture. I isolated our database and reporting tools into FastMCP servers running as stdio subprocesses. This decouples the AI from our data sources. 
        I also built a transparent Explainable AI auditing scorecard so sales reps know exactly *why* a lead was prioritized."
        """)
        
        st.markdown("### 🧠 Hiring Manager Talking Points (Technical)")
        st.markdown("""
        * **Subprocess Communication**: *"I chose FastMCP stdio transport to avoid port allocation issues on shared cloud hosting. The client communicates with the server subprocesses over standard RPC pipes."*
        * **FPDF2 Unicode Mapping**: *"Generating PDF reports containing rich text and emojis caused Unicode encoding crashes. I built a mapping layer (`clean_pdf_text`) to replace or strip unsupported symbols, making it stable."*
        * **State Synchronization**: *"To make sure interactive Kanban task moves persist across Streamlit reloads, I write changes back to `data/history/{run_id}.json` dynamically."*
        """)
        
    st.stop()

# Route to Project Statistics page if selected
if app_mode == "📈 Project Statistics":
    st.markdown("<div class='main-title'>📈 Project Statistics</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Live project analytics, lines of code, and tool execution telemetry</div>", unsafe_allow_html=True)
    
    # 1. Calculate files and lines of code dynamically
    py_files_count = 0
    py_lines_count = 0
    md_files_count = 0
    md_lines_count = 0
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for root, dirs, files in os.walk(project_root):
        # ignore python caches, virtual envs, git, and data files
        if any(part in root for part in [".venv", "venv", ".git", ".pytest_cache", "__pycache__", "data", ".gemini", "brain"]):
            continue
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(".py"):
                py_files_count += 1
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        py_lines_count += len(f.readlines())
                except:
                    pass
            elif file.endswith(".md"):
                md_files_count += 1
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        md_lines_count += len(f.readlines())
                except:
                    pass
                    
    # 2. Count reports and runs
    reports_dir = os.path.join("data", "reports")
    history_dir = os.path.join("data", "history")
    
    html_count = 0
    md_count = 0
    pdf_count = 0
    if os.path.exists(reports_dir):
        html_count = len([f for f in os.listdir(reports_dir) if f.endswith(".html")])
        md_count = len([f for f in os.listdir(reports_dir) if f.endswith(".md")])
        pdf_count = len([f for f in os.listdir(reports_dir) if f.endswith(".pdf")])
        
    num_runs = 0
    if os.path.exists(history_dir):
        num_runs = len([f for f in os.listdir(history_dir) if f.endswith(".json")])
        
    # 3. Telemetry metrics from history or current session
    avg_tool_latency = 0.0
    tool_calls_count = 0
    timeline = st.session_state.get("timeline", [])
    if timeline:
        tool_ends = [e for e in timeline if e.get("event_type") == "tool_end"]
        tool_calls_count = len(tool_ends)
        if tool_calls_count > 0:
            avg_tool_latency = sum(e.get("duration", 0.0) for e in tool_ends) / tool_calls_count
            
    # Layout cards
    st.markdown("### 📊 Repository Architecture Statistics")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric("System Agents", "5 Agents")
    col_s2.metric("FastMCP Servers", "4 Servers")
    col_s3.metric("Exposed Tools", "9 RPC Tools")
    col_s4.metric("Saved Pipeline Runs", num_runs)
    
    st.markdown("### 💻 Lines of Code (LOC) Telemetry")
    col_l1, col_l2, col_l3, col_l4 = st.columns(4)
    col_l1.metric("Python Files", py_files_count)
    col_l2.metric("Python Code LOC", f"{py_lines_count:,}")
    col_l3.metric("Markdown Files", md_files_count)
    col_l4.metric("Documentation LOC", f"{md_lines_count:,}")
    
    st.markdown("### 📄 Compiled Executive Artifacts")
    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric("HTML Reports Generated", html_count)
    col_r2.metric("Markdown Summaries", md_count)
    col_r3.metric("FPDF2 PDF Reports", pdf_count)
    
    st.markdown("### ⚡ Current Session Performance Telemetry")
    col_t1, col_t2 = st.columns(2)
    col_t1.metric("Active Run Tool Calls", tool_calls_count)
    col_t2.metric("Avg Tool Latency", f"{avg_tool_latency:.3f}s" if tool_calls_count > 0 else "N/A")
    
    st.markdown("### 🛠️ Technology Stack Breakdown")
    with st.container(border=True):
        st.write("**Core Framework**: Python 3.10+ (asyncio, multiprocessing stdio transport)")
        st.write("**Client-Server Protocol**: Model Context Protocol (FastMCP Python SDK)")
        st.write("**LLM Inference Engine**: Google Gemini API via native `google-genai` Client")
        st.write("**Visual Dashboard & GUI**: Streamlit + Plotly Express components")
        st.write("**Report Compilers**: Jinja2 HTML structures + FPDF2 binary report compilers")
        st.write("**Testing & Validation**: Pytest automation suite")
        
    st.stop()

# App Layout Header
st.markdown("<div class='main-title'>BusinessPilot AI</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Autonomous Multi-Agent Business Automation Platform</div>", unsafe_allow_html=True)

# Initialize session states
if "logs" not in st.session_state:
    st.session_state["logs"] = []
if "results" not in st.session_state:
    st.session_state["results"] = None
if "running" not in st.session_state:
    st.session_state["running"] = False
if "tasks" not in st.session_state:
    st.session_state["tasks"] = []
if "timeline" not in st.session_state:
    st.session_state["timeline"] = []
if "current_run_id" not in st.session_state:
    st.session_state["current_run_id"] = None
if "run_timestamp" not in st.session_state:
    st.session_state["run_timestamp"] = None

# Workspace Tab Structure
tab1, tab2, tab3, tab4 = st.tabs([
    "🚀 Workspace & Execution", 
    "📈 Lead Funnel Analytics", 
    "📄 Executive Report View", 
    "📋 Follow-up Task Board"
])

with tab1:
    col_run, col_logs = st.columns([1, 2])
    
    with col_logs:
        st.markdown("### ⚡ Live Agent Execution Timeline")
        timeline_placeholder = st.empty()
        
        # If there are past timeline events, render them
        timeline = st.session_state.get("timeline", [])
        if timeline:
            html = compile_timeline_to_html(timeline)
            timeline_placeholder.markdown(html, unsafe_allow_html=True)
        else:
            timeline_placeholder.info("The live multi-agent execution timeline will appear here in real-time once you run BusinessPilot AI.")
            
        results = st.session_state.get("results", {})
        if results and results.get("success", False):
            notif_res = results.get("context", {}).get("notification_results", {})
            st.markdown("### 🔔 Stakeholder Notification Dispatch Details")
            
            channel = notif_res.get("channel", "simulation")
            msg = notif_res.get("message") or notif_res.get("dispatch_message", "")
            
            if channel == "email":
                st.success(f"**Channel**: Real Email 📧\n\n**Status**: {msg}")
            else:
                if "failed" in msg.lower() or "error" in msg.lower():
                    st.warning(f"**Channel**: Simulated Logs 📋\n\n**Status**: {msg}")
                else:
                    st.info(f"**Channel**: Simulated Logs 📋\n\n**Status**: {msg}")
            
    with col_run:
        st.markdown("### Operations Dashboard")
        
        # Display active run details if present
        curr_run = st.session_state.get("current_run_id")
        if curr_run:
            st.markdown(f"""
            <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 10px 15px; margin-bottom: 15px;">
                <span style="color:#15803d; font-weight:bold; font-size:13px;">🛡️ Active Run Session: {curr_run}</span>
                <div style="font-size:11px; color:#166534; margin-top:3px;">
                    Reports compiled and saved to <code style="background-color:#dcfce7; color:#1565c0; font-size:10px;">data/reports/</code> successfully.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("Ready to run BusinessPilot AI workflow? This will ingest the data, prioritize leads, compile charts, generate summaries, create tasks, and alert stakeholders in a single autonomous execution.")
        
        # Run Button
        run_disabled = st.session_state.get("running", False) or df.empty
        
        if st.button("✈️ Run BusinessPilot AI", disabled=run_disabled, use_container_width=True):
            st.session_state["running"] = True
            st.session_state["results"] = None
            st.session_state["timeline"] = []
            
            with st.spinner("Executing autonomous multi-agent pipeline..."):
                res = asyncio.run(run_pipeline_streamed(
                    target_csv_path,
                    recipient_input,
                    GEMINI_API_KEY,
                    timeline_placeholder
                ))
                st.session_state["results"] = res
                st.session_state["running"] = False
                
            if res.get("success", False):
                st.success("BusinessPilot AI run completed successfully!")
                st.rerun()
            else:
                st.error(f"Pipeline failed: {res.get('error')}")

        # Metrics display (after execution)
        if st.session_state.get("results", {}).get("success", False):
            st.markdown("---")
            st.markdown("### Run Metrics Summary")
            
            # Calculate metrics dynamically on the filtered DataFrame
            total_leads_val = len(filtered_df)
            hot_leads_val = sum(filtered_df["priority_tier"] == "Hot")
            total_revenue_val = filtered_df["annual_revenue"].sum() if "annual_revenue" in filtered_df else 0.0
            avg_score_val = filtered_df["score"].mean() if total_leads_val > 0 else 0.0
            avg_conv_prob_val = filtered_df["estimated_conversion_rate"].mean() if total_leads_val > 0 else 0.0
            
            # 5 metrics cards in columns
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
            with m_col1:
                st.markdown(f"""
                <div class='metric-card' style='height: 140px;'>
                    <div class='metric-val'>{total_leads_val}</div>
                    <div class='metric-lbl'>Total Leads</div>
                </div>
                """, unsafe_allow_html=True)
            with m_col2:
                st.markdown(f"""
                <div class='metric-card' style='height: 140px; border-top: 4px solid #ef4444;'>
                    <div class='metric-val' style='color:#ef4444;'>{hot_leads_val}</div>
                    <div class='metric-lbl'>Hot Leads</div>
                </div>
                """, unsafe_allow_html=True)
            with m_col3:
                st.markdown(f"""
                <div class='metric-card' style='height: 140px;'>
                    <div class='metric-val'>${total_revenue_val:,.0f}</div>
                    <div class='metric-lbl'>Pipeline Value</div>
                </div>
                """, unsafe_allow_html=True)
            with m_col4:
                st.markdown(f"""
                <div class='metric-card' style='height: 140px;'>
                    <div class='metric-val'>{avg_score_val:.1f}</div>
                    <div class='metric-lbl'>Avg Score</div>
                </div>
                """, unsafe_allow_html=True)
            with m_col5:
                st.markdown(f"""
                <div class='metric-card' style='height: 140px; border-top: 4px solid #10b981;'>
                    <div class='metric-val' style='color:#10b981;'>{avg_conv_prob_val:.1%}</div>
                    <div class='metric-lbl'>Avg Conv. Prob</div>
                </div>
                """, unsafe_allow_html=True)

with tab2:
    st.markdown("### Scored Leads Ingestion & prioritisation")
    
    if st.session_state.get("results", {}).get("success", False):
        if filtered_df.empty:
            st.warning("No leads match the selected filter criteria.")
        else:
            # Display Plotly figures
            st.markdown("#### Interactive Analytics")
            
            # Row 1: Funnel & Industry Pie Chart
            fig_col1, fig_col2 = st.columns(2)
            with fig_col1:
                # Funnel Chart Ingested -> Cold -> Warm -> Hot
                total_count = len(filtered_df)
                cold_or_better = len(filtered_df)
                warm_or_better = sum(filtered_df["score"] >= 40)
                hot_count = sum(filtered_df["score"] >= 70)
                
                funnel_data = pd.DataFrame({
                    "Stage": ["1. Ingested", "2. Qualified (Cold+)", "3. Engaged (Warm+)", "4. Priority Target (Hot)"],
                    "Count": [total_count, cold_or_better, warm_or_better, hot_count]
                })
                fig_funnel = px.funnel(
                    funnel_data,
                    x="Count",
                    y="Stage",
                    color="Stage",
                    color_discrete_sequence=["#6366f1", "#3b82f6", "#f59e0b", "#ef4444"],
                    title="Lead Prioritisation Funnel Stages"
                )
                fig_funnel.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_family='Outfit')
                st.plotly_chart(fig_funnel, use_container_width=True)
                
            with fig_col2:
                # Industry pie chart
                ind_dist = filtered_df["industry"].value_counts().reset_index()
                ind_dist.columns = ["industry", "count"]
                fig_ind_dist = px.pie(
                    ind_dist,
                    names="industry",
                    values="count",
                    hole=0.4,
                    title="Industry Lead Count Distribution",
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_ind_dist.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_family='Outfit')
                st.plotly_chart(fig_ind_dist, use_container_width=True)
                
            # Row 2: Revenue Bar Chart & Scatter Plot
            fig_col3, fig_col4 = st.columns(2)
            with fig_col3:
                # Revenue by Industry
                revenue_by_ind = filtered_df.groupby("industry")["annual_revenue"].sum().reset_index()
                revenue_by_ind = revenue_by_ind.sort_values(by="annual_revenue", ascending=True)
                fig_revenue = px.bar(
                    revenue_by_ind,
                    y="industry",
                    x="annual_revenue",
                    orientation="h",
                    title="Total Pipeline Revenue by Industry ($)",
                    labels={"annual_revenue": "Revenue ($)", "industry": "Industry"},
                    color="industry",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_revenue.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_family='Outfit')
                st.plotly_chart(fig_revenue, use_container_width=True)
                
            with fig_col4:
                # Conversion Probability vs Score scatter
                fig_conv_vs_score = px.scatter(
                    filtered_df,
                    x="score",
                    y="estimated_conversion_rate",
                    color="priority_tier",
                    size="employee_count",
                    hover_name="company_name",
                    title="Conversion Probability vs. Lead Score",
                    labels={"estimated_conversion_rate": "Conversion Rate", "score": "Lead Score"},
                    color_discrete_map={"Hot": "#ef4444", "Warm": "#f59e0b", "Cold": "#3b82f6"}
                )
                fig_conv_vs_score.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_family='Outfit')
                st.plotly_chart(fig_conv_vs_score, use_container_width=True)
                
            # Row 3: Score Distribution Histogram
            fig_dist = px.histogram(
                filtered_df,
                x="score",
                color="priority_tier",
                color_discrete_map={"Hot": "#ef4444", "Warm": "#f59e0b", "Cold": "#3b82f6"},
                title="Lead Score Distribution by Priority Tier",
                labels={"score": "Lead Score", "count": "Number of Leads", "priority_tier": "Priority Tier"},
                category_orders={"priority_tier": ["Hot", "Warm", "Cold"]},
                nbins=15
            )
            fig_dist.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_family='Outfit')
            st.plotly_chart(fig_dist, use_container_width=True)
            
            # Row 4: Scored Leads Data Table
            st.markdown("#### Scored Leads Data Table")
            # Style tiers
            def style_priority(val):
                if val == 'Hot':
                    return 'background-color: #fee2e2; color: #ef4444; font-weight: bold;'
                elif val == 'Warm':
                    return 'background-color: #fef3c7; color: #d97706; font-weight: bold;'
                else:
                    return 'background-color: #dbeafe; color: #2563eb;'
                    
            styled_df = filtered_df.style.map(style_priority, subset=["priority_tier"])
            st.dataframe(styled_df, use_container_width=True)
            
            # Row 5: Score Explainability deep-dive
            st.markdown("---")
            st.markdown("### 🔍 Lead Score Explainability Deep-Dive")
            st.write("Select a lead from the dropdown below to view a detailed audit trail of its prioritisation score, factor contributions, and the contributing AI agents/MCP tools.")
            
            selected_company = st.selectbox(
                "Choose Company to Deep-Dive Score",
                options=filtered_df["company_name"].tolist(),
                key="deep_dive_select"
            )
            
            if selected_company:
                lead_row = filtered_df[filtered_df["company_name"] == selected_company].iloc[0]
                exp = lead_row.get("score_explanation")
                
                if isinstance(exp, dict):
                    # Outer Card Container
                    st.markdown(f"""
                    <div style="background: rgba(255, 255, 255, 0.05); border: 1px solid #e2e8f0; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                        <h4 style="margin: 0 0 10px 0; color: #1e293b;">🏢 {lead_row['company_name']} ({lead_row['industry']})</h4>
                        <div style="display: flex; gap: 15px; align-items: center; margin-bottom: 10px;">
                            <span style="font-size: 18px; font-weight: 800; color: #1e293b; background: #e2e8f0; padding: 5px 15px; border-radius: 8px;">Final Score: {lead_row['score']}/100</span>
                            <span style="font-size: 13px; font-weight: 700; background: {'#fee2e2; color: #ef4444;' if lead_row['priority_tier'] == 'Hot' else '#fef3c7; color: #d97706;' if lead_row['priority_tier'] == 'Warm' else '#dbeafe; color: #2563eb;'}; padding: 6px 12px; border-radius: 20px; text-transform: uppercase;">{lead_row['priority_tier']} Tier</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Columns for scoring factors
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        # Revenue Factor
                        st.markdown(f"""
                        <div style="background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6; margin-bottom: 15px; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
                            <div style="font-weight: bold; color: #64748b; font-size: 12px; text-transform: uppercase;">💰 Annual Revenue Factor</div>
                            <div style="font-size: 18px; font-weight: 700; color: #1e293b; margin: 5px 0;">+{exp['revenue']['points']} Points <span style="font-size: 12px; font-weight: 400; color: #64748b;">(Value: {exp['revenue']['value']})</span></div>
                            <div style="font-size: 12px; color: #475569;">{exp['revenue']['description']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Company Size Factor
                        st.markdown(f"""
                        <div style="background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #10b981; margin-bottom: 15px; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
                            <div style="font-weight: bold; color: #64748b; font-size: 12px; text-transform: uppercase;">👥 Company Size (Employees)</div>
                            <div style="font-size: 18px; font-weight: 700; color: #1e293b; margin: 5px 0;">+{exp['employees']['points']} Points <span style="font-size: 12px; font-weight: 400; color: #64748b;">(Size: {exp['employees']['value']})</span></div>
                            <div style="font-size: 12px; color: #475569;">{exp['employees']['description']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with col_f2:
                        # Interaction Factor
                        st.markdown(f"""
                        <div style="background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #a855f7; margin-bottom: 15px; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
                            <div style="font-weight: bold; color: #64748b; font-size: 12px; text-transform: uppercase;">⚡ Engagement Index (Interactions)</div>
                            <div style="font-size: 18px; font-weight: 700; color: #1e293b; margin: 5px 0;">+{exp['interactions']['points']} Points <span style="font-size: 12px; font-weight: 400; color: #64748b;">(Count: {exp['interactions']['value']})</span></div>
                            <div style="font-size: 12px; color: #475569;">{exp['interactions']['description']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Conversion Rate Factor
                        st.markdown(f"""
                        <div style="background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b; margin-bottom: 15px; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
                            <div style="font-weight: bold; color: #64748b; font-size: 12px; text-transform: uppercase;">📈 Conversion Probability Factor</div>
                            <div style="font-size: 18px; font-weight: 700; color: #1e293b; margin: 5px 0;">+{exp['conversion_rate']['points']} Points <span style="font-size: 12px; font-weight: 400; color: #64748b;">(Rate: {exp['conversion_rate']['value']})</span></div>
                            <div style="font-size: 12px; color: #475569;">{exp['conversion_rate']['description']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Capping Note & Total
                    capped_text = " (Score capped at maximum limit of 100)" if exp['capped'] else ""
                    st.info(f"**Score Math Audit:** {exp['revenue']['points']} (Rev) + {exp['employees']['points']} (Size) + {exp['interactions']['points']} (Engage) + {exp['conversion_rate']['points']} (Conv) = **{exp['total_unfiltered']} Raw Points**{capped_text} -> **Final Score: {lead_row['score']}/100**")
                    
                    # Audited Contributors
                    st.markdown("##### 🕵️ Contributing Architecture Telemetry")
                    st.write(f"**Contributing Agents:** `{'`, `'.join(exp['contributors']['agents'])}`")
                    mcp_tools_str = ", ".join([f"`{t['tool']}` on `{t['server']}`" for t in exp['contributors']['mcp_tools']])
                    st.write(f"**Contributing MCP Tools:** {mcp_tools_str}")
                else:
                    st.warning("Explainability audit log is not available for this run.")
    else:
        st.info("Execute a pipeline run to load funnel charts and prioritized datasets.")

with tab3:
    st.markdown("### Executive Report Compiler")
    
    if st.session_state.get("results", {}).get("success", False):
        context = st.session_state.get("results", {}).get("context", {})
        report_res = context["report_results"]
        
        # Display Run Info and Timestamp
        run_id = st.session_state.get("current_run_id", "N/A")
        timestamp = st.session_state.get("run_timestamp", "N/A")
        
        st.markdown(f"""
        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 18px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
            <div><strong>Active Run ID:</strong> <code>{run_id}</code></div>
            <div><strong>Generated At:</strong> <span style="color: #6366f1; font-weight: 600;">{timestamp}</span></div>
            <div><span style="background-color: #d1fae5; color: #065f46; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">Saved to Storage ✅</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Download buttons
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            st.download_button(
                label="📄 Download HTML Executive Report",
                data=report_res.get("html_content", ""),
                file_name=f"{run_id}_report.html",
                mime="text/html",
                use_container_width=True
            )
        with btn_col2:
            st.download_button(
                label="📝 Download Markdown Insights Summary",
                data=report_res.get("md_content", ""),
                file_name=f"{run_id}_report.md",
                mime="text/markdown",
                use_container_width=True
            )
        with btn_col3:
            pdf_data = None
            if run_id:
                pdf_path = os.path.join("data", "reports", f"{run_id}_report.pdf")
                if os.path.exists(pdf_path):
                    try:
                        with open(pdf_path, "rb") as pdf_file:
                            pdf_data = pdf_file.read()
                    except Exception as e:
                        logger.error(f"Failed to read PDF report file: {str(e)}")
            
            if pdf_data:
                st.download_button(
                    label="📕 Download PDF Executive Report",
                    data=pdf_data,
                    file_name=f"{run_id}_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.button("📕 PDF Report Unavailable", disabled=True, use_container_width=True)
                
        st.markdown("---")
        # Render HTML Report directly in Streamlit using component
        components.html(report_res.get("html_content", ""), height=900, scrolling=True)
    else:
        st.info("Execute a pipeline run to generate the styled HTML report.")

with tab4:
    st.markdown("### Interactive Kanban Task Board")
    
    if st.session_state.get("results", {}).get("success", False):
        tasks = st.session_state.get("tasks", [])
        if not tasks:
            st.warning("No tasks available for this run.")
        else:
            # Filter tasks based on filtered leads
            filtered_companies = filtered_df["company_name"].tolist() if not filtered_df.empty else []
            
            # Map index to tasks to allow status updates using index
            indexed_tasks = [(i, t) for i, t in enumerate(tasks) if t.get("lead_company") in filtered_companies]
            
            todo_tasks = []
            in_progress_tasks = []
            completed_tasks = []
            
            for idx, task in indexed_tasks:
                status = task.get("status", "To Do")
                if status == "To Do":
                    todo_tasks.append((idx, task))
                elif status == "In Progress":
                    in_progress_tasks.append((idx, task))
                elif status == "Completed":
                    completed_tasks.append((idx, task))
                else:
                    todo_tasks.append((idx, task))
                    
            # Render structured Kanban task columns
            col_todo, col_in_progress, col_completed = st.columns(3)
            
            with col_todo:
                st.markdown("<h4 style='color:#6366f1; border-bottom: 2px solid #6366f1; padding-bottom:5px;'>📋 To Do</h4>", unsafe_allow_html=True)
                st.write("")
                if not todo_tasks:
                    st.info("No tasks in To Do.")
                for idx, task in todo_tasks:
                    with st.container(border=True):
                        prio = task.get("priority", "Medium").upper()
                        prio_color = "#ef4444" if prio == "HIGH" else "#f59e0b" if prio == "MEDIUM" else "#3b82f6"
                        
                        st.markdown(f"**🏢 {task.get('lead_company')}**")
                        st.markdown(f"<span style='color:{prio_color}; font-size:11px; font-weight:700;'>{prio} PRIORITY</span>", unsafe_allow_html=True)
                        st.write(task.get("task_description"))
                        
                        st.markdown(f"""
                        <div style='display:flex; justify-content:space-between; margin-top:8px; margin-bottom:12px; font-size:11px; color:#64748b;'>
                            <span>👤 {task.get('assignee')}</span>
                            <span>📅 {task.get('created_at', 'N/A')}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        b_col1, b_col2 = st.columns(2)
                        with b_col1:
                            if st.button("▶️ Start", key=f"start_{idx}", use_container_width=True):
                                move_task(idx, "In Progress")
                                st.rerun()
                        with b_col2:
                            if st.button("✔️ Complete", key=f"comp_todo_{idx}", use_container_width=True):
                                move_task(idx, "Completed")
                                st.rerun()
                                
            with col_in_progress:
                st.markdown("<h4 style='color:#f59e0b; border-bottom: 2px solid #f59e0b; padding-bottom:5px;'>⚡ In Progress</h4>", unsafe_allow_html=True)
                st.write("")
                if not in_progress_tasks:
                    st.info("No tasks in progress.")
                for idx, task in in_progress_tasks:
                    with st.container(border=True):
                        prio = task.get("priority", "Medium").upper()
                        prio_color = "#ef4444" if prio == "HIGH" else "#f59e0b" if prio == "MEDIUM" else "#3b82f6"
                        
                        st.markdown(f"**🏢 {task.get('lead_company')}**")
                        st.markdown(f"<span style='color:{prio_color}; font-size:11px; font-weight:700;'>{prio} PRIORITY</span>", unsafe_allow_html=True)
                        st.write(task.get("task_description"))
                        
                        st.markdown(f"""
                        <div style='display:flex; justify-content:space-between; margin-top:8px; margin-bottom:12px; font-size:11px; color:#64748b;'>
                            <span>👤 {task.get('assignee')}</span>
                            <span>📅 {task.get('created_at', 'N/A')}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        b_col1, b_col2 = st.columns(2)
                        with b_col1:
                            if st.button("⬅️ Move Back", key=f"back_inprog_{idx}", use_container_width=True):
                                move_task(idx, "To Do")
                                st.rerun()
                        with b_col2:
                            if st.button("✔️ Complete", key=f"comp_inprog_{idx}", use_container_width=True):
                                move_task(idx, "Completed")
                                st.rerun()
                                
            with col_completed:
                st.markdown("<h4 style='color:#10b981; border-bottom: 2px solid #10b981; padding-bottom:5px;'>✔️ Completed</h4>", unsafe_allow_html=True)
                st.write("")
                if not completed_tasks:
                    st.info("No completed tasks.")
                for idx, task in completed_tasks:
                    with st.container(border=True):
                        prio = task.get("priority", "Medium").upper()
                        prio_color = "#ef4444" if prio == "HIGH" else "#f59e0b" if prio == "MEDIUM" else "#3b82f6"
                        
                        st.markdown(f"**🏢 {task.get('lead_company')}**")
                        st.markdown(f"<span style='color:{prio_color}; font-size:11px; font-weight:700;'>{prio} PRIORITY</span>", unsafe_allow_html=True)
                        st.write(task.get("task_description"))
                        
                        st.markdown(f"""
                        <div style='display:flex; justify-content:space-between; margin-top:8px; margin-bottom:12px; font-size:11px; color:#64748b;'>
                            <span>👤 {task.get('assignee')}</span>
                            <span>📅 {task.get('created_at', 'N/A')}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("⬅️ Move Back", key=f"back_comp_{idx}", use_container_width=True):
                            move_task(idx, "In Progress")
                            st.rerun()
    else:
        st.info("Execute a pipeline run to auto-generate assignable follow-up Kanban tasks.")
