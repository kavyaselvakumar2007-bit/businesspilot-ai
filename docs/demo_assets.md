# BusinessPilot AI Demo Scripts & Assets

This document provides structured guides for demonstrating BusinessPilot AI to recruiters, hiring managers, and technical interview panels.

---

## 1. Suggested Screenshot Capture Guide
Save your screenshots in the `docs/screenshots/` directory with these filenames:
1. `01_dashboard.png`: Captures the metrics cards, funnel charts, and lead table.
2. `02_timeline.png`: Captures the live Agent Execution Timeline.
3. `03_explainability.png`: Captures the expanded Lead Score Audit Card showing points contribution.
4. `04_kanban.png`: Captures the To Do, In Progress, and Completed columns on the Task Board.
5. `05_telemetry.png`: Captures the MCP Observability tool registry and latency grids.
6. `06_history.png`: Captures the historical runs list and restoration buttons.
7. `07_architecture.png`: Captures the system diagram page.

---

## 2. 2-Minute Demo Script (Elevator Pitch)
*Goal: Briefly hook the recruiter by highlighting core features and value.*

- **[0:00 - 0:30] Hook & Problem**: "Hi, I want to show you BusinessPilot AI. In B2B sales, teams waste hours parsing lead lists and trying to prioritize who to contact. BusinessPilot AI solves this by deploying a team of autonomous AI agents."
- **[0:30 - 1:15] The Demo**: "I will click 'Run BusinessPilot AI'. As you see in this live timeline, multiple agents are spinning up. A Lead Analysis Agent filters the leads; a Business Insights Agent summarizes sales trends using Gemini; and a Task Agent assigns follow-ups. Everything is tracked live."
- **[1:15 - 2:00] Value Proposition**: "Here is the interactive Kanban board where tasks are created and can be dragged across columns. All runs are saved to persistent storage so I can load previous pipeline states instantly. It is built using the new Model Context Protocol (MCP) standard, which separates the AI logic from the data tools, making it modular, secure, and ready for production."

---

## 3. 5-Minute Technical Demo Script
*Goal: Showcase technical details, MCP, and Explainability to hiring managers.*

- **[0:00 - 1:00] Architecture & MCP**: "BusinessPilot AI uses a client-server architecture based on Anthropic's Model Context Protocol. We launch four FastMCP servers as subprocesses communicating over stdio. This abstracts our database, reporting engine, and email service into standard tools, separating code boundaries."
- **[1:00 - 2:30] Agent Orchestration**: "When we trigger the pipeline, the Orchestrator sequences five agents. Let's look at the live tracer. We intercept base agent methods to log tool starts, tool latency, and agent states. Notice that the Lead Agent calls the `get_scoring_rules` tool on our Knowledge Server."
- **[2:30 - 3:30] Explainable AI (XAI)**: "AI scoring is often a black box. In the Funnel Analytics tab, we have built an explainability card. If we select a company, we see exactly how the score was calculated—e.g. +30 points for revenue bracket, +20 for conversion rate—and list which agents and tools contributed to this decision."
- **[3:30 - 5:00] Kanban & History Page**: "Once tasks are created, sales reps can move tasks through 'To Do', 'In Progress', and 'Completed'. This state is stored in Streamlit's session state and saved back to our history JSON records, making it persistent across page reloads. We can also reload historical runs offline without invoking the LLM."

---

## 4. Recruiter Screening Conversation Script
*Recruiter: 'Tell me about a project you are proud of.'*

> "I recently built **BusinessPilot AI**, an autonomous multi-agent platform for B2B sales automation. I built it because B2B sales pipelines suffer from slow ingestion and non-transparent scoring. 
> 
> What makes this project stand out is that I implemented the new **Model Context Protocol (MCP)** standard. Instead of writing custom API wrappers for the AI agents, I decoupled the data tools into independent servers. 
> 
> I also addressed a major issue in AI business tools—**transparency**. I built an Explainable AI scorecard that audits why a lead was prioritized, showing the exact points distribution. The project is fully dockerized and ready for production deployment."

---

## 5. Technical Presentation Script (System Design Interview)
*Goal: Walk through the codebase during a technical interview.*

1. **Decoupling Data Tools (MCP)**: "In `mcp_servers/`, I created four service boundaries. If we ever swap our CSV database for PostgreSQL, we only update the Lead Data Server; our agents remain untouched."
2. **Explainable Audits**: "In `agents/lead_analysis_agent.py`, I designed `score_lead_explainable` which calculates factors point contributions and adds auditing telemetry tracking the executing tools. The standard `score_lead` delegates to it, keeping our test suite fully backward-compatible."
3. **Robust State Syncing**: "In `dashboard/app.py`, the `move_task` function synchronizes Streamlit UI updates to disk. Since Streamlit runs top-to-bottom on every action, we write state changes to `data/history/{run_id}.json` to make sure task movements are saved."
