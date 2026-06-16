# Resume Description & Career Assets

This document contains ready-to-copy resume bullets and talking points for technical interviews.

---

## 1. Resume Project Entry

### **BusinessPilot AI — Autonomous Multi-Agent Operations Platform** | Python, Streamlit, Gemini API, FastMCP, Docker
*Autonomous business lead scoring and process automation engine built on Anthropic's Model Context Protocol (MCP) standard.*

- **Decoupled System Architecture**: Designed and built 4 FastMCP microservice servers running as local subprocesses communicating via stdio JSON-RPC, separating the AI orchestrator from reporting, notification, and database tools.
- **Multi-Agent Orchestration**: Implemented a dynamic sequence orchestrator running 5 specialized AI agents with automatic exception handling and retries. Developed a live HTML/CSS tracer to display agent states and tool latency.
- **Explainable Scoring (XAI)**: Created an XAI scoring audit scorecard that tracks point-by-point contributions for lead scores, logging contributing agents and tools to resolve transparency issues in AI decision-making.
- **Data Persistence & State Management**: Developed persistent file storage for execution history, dataset uploads, and compiled reports. Implemented an interactive Kanban board syncing UI moves to history JSON records.

---

## 2. Technology Stack Keywords
`Python` `Streamlit` `Plotly` `Google Gemini API` `Model Context Protocol (MCP)` `FastMCP` `JSON-RPC` `Docker` `FPDF2` `Pytest` `Asynchronous Programming (asyncio)`

---

## 3. Interview Talking Points

### The "Why" behind MCP
> "I chose Anthropic's Model Context Protocol (MCP) because it decouples agent planning from tool execution. In typical architectures, agents are tightly coupled to custom database wrappers or API clients. 
> 
> With MCP, all data interfaces are isolated into stand-alone microservices that expose tools over JSON-RPC. If our database structure changes from CSV to PostgreSQL, I only update the Lead Data Server; the orchestrator and agents remain completely untouched."

### Overcoming the PDF Unicode Challenge
> "One challenge I solved was generating PDF reports. Our insights agent uses rich formatting and emojis (like checkmarks or trend icons) to display reports in the Streamlit UI. However, the standard Helvetica font in `fpdf2` throws `UnicodeEncodeError` when compiling these characters. 
> 
> I designed a text sanitization pipeline (`clean_pdf_text`) that filters non-Latin1 symbols and maps common operational emojis to text badges (like mapping ✅ to `[SUCCESS]` and 📈 to `[Conversion]`), preventing runtime crashes."

### Asynchronous State Synchronization
> "In Streamlit, the entire script runs top-to-bottom on every user click. This makes maintaining state in interactive components (like moving tasks on a Kanban board) difficult. 
> 
> I resolved this by utilizing Streamlit's `st.session_state` to track active tasks, and then writing a module-level state synchronizer that updates `data/history/{run_id}.json` after every state transition. This ensures task updates survive page reloads and can be reloaded offline."
