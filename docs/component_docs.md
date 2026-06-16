# BusinessPilot AI Component Documentation

This document provides a breakdown of each module and file within the BusinessPilot AI codebase to help beginners and developers navigate the project structure.

---

## 1. Directory Overview

```text
├── config/
│   └── settings.py              # System parameters & logging setup
├── data/
│   └── sample_leads.csv         # Realistic mockup leads dataset
├── mcp_servers/
│   ├── lead_data_server.py      # MCP Data ingestion server
│   ├── business_knowledge_server.py # MCP Scoring parameters server
│   ├── reporting_server.py      # MCP HTML layout compiler & charts generator
│   └── notification_server.py   # MCP Messaging & SMTP email dispatch server
├── agents/
│   ├── base_agent.py            # Generic agent skeleton with mock fallbacks
│   ├── lead_analysis_agent.py   # prioritises leads using multi-factor scoring
│   ├── business_insights_agent.py # Gemini-powered executive trend generator
│   ├── report_generation_agent.py # Report and asset writer agent
│   ├── task_management_agent.py # Gemini-powered follow-up task creator
│   └── notification_agent.py    # Notification layout compiler agent
├── orchestrator/
│   ├── mcp_manager.py           # Subprocess runner & JSON-RPC dispatcher
│   └── orchestrator.py          # Pipeline sequence coordinator
├── dashboard/
│   └── app.py                   # Streamlit dashboard interface
├── tests/
│   └── test_lead_scoring.py     # pytest lead scoring rules test suite
```

---

## 2. Core Components

### Configuration (`config/settings.py`)
Defines default logging rules, output directories, lead scoring weights, priority score brackets, and industry benchmarks. Both the agents and MCP servers use this file as their source of truth.

### MCP Manager (`orchestrator/mcp_manager.py`)
Utilizes Python's `asyncio` and `mcp` libraries to start the FastMCP servers. It connects to them via standard I/O streams and exposes a single method `call_tool(server, tool, args)` that translates and routes requests.

### Sequence Orchestrator (`orchestrator/orchestrator.py`)
Manages the shared pipeline context and executes the agents sequentially. It measures performance times, updates the timeline, catches exceptions, and shuts down the MCP servers cleanly inside a `finally` block to prevent background zombie processes.

---

## 3. Autonomous Agents (`agents/`)

### `BaseAgent` (`base_agent.py`)
The base class that all agents inherit from. It sets up logging and provides an asynchronous `call_mcp_tool` wrapper. If the `mcp_manager` is not initialized, it redirects calls to `_mock_mcp_call` which serves predefined, static payloads.

### `LeadAnalysisAgent` (`lead_analysis_agent.py`)
Loads lead details, scores them using mathematical rules (Revenue bracket points + Employee bracket points + Interactions * 3 + Conversion rate * 20), assigns them to priority tiers (Hot, Warm, Cold), and ranks them descending by score.

### `BusinessInsightsAgent` (`business_insights_agent.py`)
Injects scored leads and summary stats into a detailed prompt template and calls Gemini (`gemini-2.5-flash`) via the `google-genai` SDK. It returns a professional executive report. Falls back to a rule-based generator if offline.

### `TaskManagementAgent` (`task_management_agent.py`)
Uses Gemini to translate recommendations into a JSON list of structured follow-up items. It allocates roles (e.g. *Technical Sales Engineer* or *Lead Account Executive*) based on industry profiles and assigns priority levels.

### `ReportGenerationAgent` (`report_generation_agent.py`)
Calls the Reporting MCP Server to generate Plotly histogram and scatter plots as HTML divs and compile a complete styled HTML report, saving files to `logs/executive_report.html` and `logs/executive_report.md`.

### `NotificationAgent` (`notification_agent.py`)
Aggregates summary statistics, compiles a text-based operational digest highlighting high-value leads and immediate actions, and calls the Notification MCP Server to dispatch the message.
