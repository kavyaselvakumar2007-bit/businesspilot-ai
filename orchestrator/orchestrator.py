import os
import sys
import time
import asyncio
from datetime import datetime
from google import genai

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import logger, GEMINI_API_KEY
from orchestrator.mcp_manager import MCPManager
from agents.lead_analysis_agent import LeadAnalysisAgent
from agents.business_insights_agent import BusinessInsightsAgent
from agents.task_management_agent import TaskManagementAgent
from agents.report_generation_agent import ReportGenerationAgent
from agents.notification_agent import NotificationAgent

class BusinessPilotOrchestrator:
    """
    Main Orchestrator coordinates the multi-agent pipeline,
    maintains the shared execution context, and tracks runtime performance.
    """
    def __init__(self):
        self.mcp_manager = None
        self.gemini_client = None
        self.timeline = []

    def log_event(self, stage: str, message: str):
        """Helper to append structured event log with accurate timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        event = {
            "timestamp": timestamp,
            "stage": stage,
            "message": message
        }
        self.timeline.append(event)
        logger.info(f"[{stage}] {message}")

    async def execute_pipeline(self, csv_path: str = None, recipient: str = None) -> dict:
        """
        Runs the full end-to-end multi-agent workflow.
        
        Args:
            csv_path (str): Optional path to custom leads CSV file.
            recipient (str): Optional stakeholder notification email.
            
        Returns:
            dict: Unified results package containing scored data, reports, tasks, and logs.
        """
        start_time = time.time()
        self.timeline.clear()
        
        self.log_event("Initialization", "Starting BusinessPilot AI Orchestrator...")
        
        # Initialize Gemini SDK Client
        if GEMINI_API_KEY:
            try:
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
                self.log_event("Initialization", "Gemini GenAI SDK client initialized successfully.")
            except Exception as e:
                self.log_event("Initialization", f"Failed to initialize Gemini Client: {str(e)}. Proceeding with mock fallback.")
        else:
            self.log_event("Initialization", "Warning: GEMINI_API_KEY not found in env. Running in offline fallback mode.")

        # Initialize MCP Manager
        self.mcp_manager = MCPManager()
        
        # Shared context dictionary passed between agents
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
            # 1. Boot MCP Servers
            self.log_event("MCP Boot", "Spawning local FastMCP servers...")
            await self.mcp_manager.start_all()
            self.log_event("MCP Boot", "All MCP servers online and tools registered.")
            
            # Pass managers to agents
            lead_agent = LeadAnalysisAgent(self.mcp_manager, self.gemini_client)
            insights_agent = BusinessInsightsAgent(self.mcp_manager, self.gemini_client)
            task_agent = TaskManagementAgent(self.mcp_manager, self.gemini_client)
            report_agent = ReportGenerationAgent(self.mcp_manager, self.gemini_client)
            notify_agent = NotificationAgent(self.mcp_manager, self.gemini_client)

            # 2. RUN: Lead Analysis Agent
            self.log_event("Lead Analysis", "Executing Lead scoring and prioritisation rules...")
            lead_results = await lead_agent.execute(context)
            if not lead_results.get("success", False):
                raise RuntimeError("Lead Analysis Agent execution failed.")
            context["leads"] = lead_results["leads"]
            context["metrics"] = lead_results["metrics"]
            self.log_event("Lead Analysis", f"Completed. prioritised {context['metrics']['hot_leads']} Hot leads.")

            # 3. RUN: Business Insights Agent
            self.log_event("Business Insights", "Generating executive trends with Gemini API...")
            insights_results = await insights_agent.execute(context)
            if not insights_results.get("success", False):
                raise RuntimeError("Business Insights Agent execution failed.")
            context["executive_summary"] = insights_results["executive_summary"]
            self.log_event("Business Insights", "Completed. Summary analysis derived.")

            # 4. RUN: Task Management Agent
            self.log_event("Task Management", "Generating structured follow-up action items...")
            task_results = await task_agent.execute(context)
            if not task_results.get("success", False):
                raise RuntimeError("Task Management Agent execution failed.")
            context["tasks"] = task_results["tasks"]
            self.log_event("Task Management", f"Completed. Generated {len(context['tasks'])} tasks.")

            # 5. RUN: Report Generation Agent
            self.log_event("Report Generation", "Compiling HTML assets and rendering charts...")
            report_results = await report_agent.execute(context)
            if not report_results.get("success", False):
                raise RuntimeError("Report Generation Agent execution failed.")
            context["report_results"] = report_results
            self.log_event("Report Generation", f"Completed. Report saved: {report_results['html_report_path']}")

            # 6. RUN: Notification Agent
            self.log_event("Notification Dispatch", "Sending alert summary to stakeholder...")
            notify_results = await notify_agent.execute(context)
            context["notification_results"] = notify_results
            self.log_event("Notification Dispatch", f"Completed. Channel: {notify_results.get('channel')}.")

            # End Pipeline
            duration = time.time() - start_time
            self.log_event("Complete", f"BusinessPilot AI workflow finished successfully in {duration:.2f} seconds.")
            
            return {
                "success": True,
                "context": context,
                "timeline": self.timeline,
                "duration_seconds": duration
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            duration = time.time() - start_time
            self.log_event("Pipeline Failed", f"Execution aborted due to exception: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timeline": self.timeline,
                "duration_seconds": duration
            }
            
        finally:
            # Crucial: clean up and shut down MCP servers
            self.log_event("Cleanup", "Shutting down MCP servers...")
            await self.mcp_manager.stop_all()
            self.log_event("Cleanup", "Orchestrator cleanup finished.")

def run_synchronous_pipeline(csv_path: str = None, recipient: str = None) -> dict:
    """Helper to run the async orchestrator pipeline inside a standard blocking context."""
    orchestrator = BusinessPilotOrchestrator()
    return asyncio.run(orchestrator.execute_pipeline(csv_path, recipient))

if __name__ == "__main__":
    # Test execution using the sample data CSV
    print("Starting sample orchestrator run...")
    results = run_synchronous_pipeline()
    if results["success"]:
        print(f"\nPipeline succeeded in {results['duration_seconds']:.2f}s!")
        print(f"Total leads: {results['context']['metrics']['total_leads']}")
        print(f"Report path: {results['context']['report_results']['html_report_path']}")
        print(f"Notification status: {results['context']['notification_results'].get('dispatch_message')}")
    else:
        print(f"\nPipeline failed! Error: {results.get('error')}")
