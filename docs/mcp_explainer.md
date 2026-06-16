# Model Context Protocol (MCP) Explainer

This document explains the Model Context Protocol (MCP) concepts and how they are implemented within **BusinessPilot AI** to satisfy tool-interoperability requirements for academic and course reviews.

---

## 1. What is Model Context Protocol?

The **Model Context Protocol (MCP)** is an open standard developed to allow Large Language Models (LLMs) to interact securely and dynamically with local or remote data sources, tools, and systems.

Historically, AI applications relied on **hardcoded tool bindings**. Every time a developer wanted to expose a new database or API to an LLM, they had to write custom API clients, schemas, and routing logic.

MCP replaces this with a **client-server architecture**:
* **MCP Server**: A standalone process or service that exposes resources (data files), tools (executable code), and prompts (preconfigured template queries).
* **MCP Client**: The agent orchestrator or execution environment. It initiates communication with the servers, queries their capabilities, and routes agent requests to them.

---

## 2. Core Concepts in BusinessPilot AI

Our architecture implements a **real local MCP system** using the official Python MCP SDK and `FastMCP`.

### A. Transport layer (Stdio)
In BusinessPilot AI, the `MCPManager` launches each server script as a Python subprocess:
* Transport occurs over standard input and output streams (`stdin` and `stdout`).
* The orchestrator uses the Python MCP SDK client's `stdio_client` context manager to establish these channels securely.
* Messages are serialized as standard JSON-RPC 2.0 frames.

### B. Dynamic Tool Discovery
Instead of hardcoding what tools are available, the client queries the servers.
1. When the orchestrator boots, the `MCPManager` calls `session.list_tools()` for each server session.
2. The server responds with its schema:
   - **Name**: e.g., `load_leads`
   - **Description**: Exposes tool utility to LLMs (derived from docstrings).
   - **Input Schema**: A JSON Schema describing required parameter names and types (derived from python type hints).
3. These schemas can then be bound directly to Gemini or executed dynamically by agents.

### C. Dynamic Tool Invocation
When an agent needs to execute a tool (e.g. loading data):
1. The agent dispatches `call_mcp_tool("Lead Data Server", "load_leads", {"csv_path": "path"})`.
2. The `MCPManager` routes this to the `Lead Data Server`'s active JSON-RPC session.
3. The server validates the inputs against the Pydantic schema, executes the internal Python code, and returns the serialized output.

---

## 3. Server Implementations

We implemented four distinct MCP servers inside the `mcp_servers/` directory:

1. **Lead Data Server (`lead_data_server.py`)**
   - *Tools*: `load_leads`, `filter_leads`, `get_lead_stats`.
   - *Utility*: Abstracts pandas data ingestion. The LLM or orchestrator reads and aggregates leads without touching raw CSV files.
2. **Business Knowledge Server (`business_knowledge_server.py`)**
   - *Tools*: `get_scoring_rules`, `get_industry_benchmarks`, `get_qualification_guidelines`.
   - *Utility*: Serves core domain parameters. If scoring thresholds shift, they are updated centrally in the knowledge base.
3. **Reporting Server (`reporting_server.py`)**
   - *Tools*: `generate_plotly_charts`, `compile_html_report`.
   - *Utility*: Serves presentation logic. Compiles analytical layouts and generates visual widgets.
4. **Notification Server (`notification_server.py`)**
   - *Tools*: `send_notification`.
   - *Utility*: Serves side-effect dispatches. Handles SMTP email delivery or falls back to simulated logging outputs.

---

## 4. Why This Architecture is Production-Quality

* **Decoupled Business Logic**: The agents are entirely generic. If we switch the backend database from CSV to a Postgres SQL database, we only modify the *Lead Data Server*. The agent code remains untouched.
* **Security & Sandboxing**: MCP servers run as isolated subprocesses. They execute tools locally, only exposing structured text/image outputs to the client, preventing unauthorized system calls.
* **Dynamic Interoperability**: Any MCP-compliant client (such as Claude Desktop or other developer tools) can connect to our `mcp_servers/` out-of-the-box and immediately inspect and call the same tools.
