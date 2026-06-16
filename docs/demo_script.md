# BusinessPilot AI Demo Scripts

This document contains demo scripts for demonstrating the BusinessPilot AI platform in recruiters screenings, technical case presentations, or team reviews.

---

## 1. 2-Minute Demo Script (Elevator Pitch)
*Goal: Showcase the core capabilities and value quickly to recruiters.*

- **[0:00 - 0:30] Hook & Problem**: "Hi, I'd like to show you BusinessPilot AI. Sales operations teams lose hours loading spreadsheets, scoring contacts based on intuition, and manually creating follow-up lists. BusinessPilot AI solves this by deploying a team of autonomous AI agents."
- **[0:30 - 1:15] In-Action Demo**: "If I click 'Run BusinessPilot AI', five specialized agents launch in sequence. You can see this live timeline tracer: the Lead Analysis Agent loads leads from an MCP tool and ranks them; the Insights Agent parses trends using Gemini; the Task Agent assigns follow-ups; the Reporting Agent compiles Plotly charts; and the Notification Agent alerts stakeholders."
- **[1:15 - 2:00] Value & Tech Stack**: "Our dashboard features an interactive Kanban board where reps can drag tasks. We also support HTML, Markdown, and PDF downloads. The platform leverages the new Model Context Protocol (MCP) standard, isolating our database and tools into subprocesses. It is fully containerized with Docker and ready for production."

---

## 2. 5-Minute Technical Demo Script
*Goal: Deep-dive into technical system design and code boundaries for hiring managers.*

- **[0:00 - 1:00] Protocol Boundary (MCP)**: "BusinessPilot AI uses a client-server architecture based on Anthropic's Model Context Protocol. We launch four FastMCP servers as subprocesses communicating over standard input/output pipelines. This abstracts tools into JSON-RPC interfaces, keeping database logic separate from AI code."
- **[1:00 - 2:30] Live Tracer & Telemetry**: "When a workflow runs, we log agent states and tool durations. Notice the tracer console: it intercepts base agent executions to log tool latencies. Our Observability page displays server statuses and tool latency tables in real-time."
- **[2:30 - 3:30] Scoring Explainability**: "To solve the black-box AI problem, I built an Explainable AI scorecard. In the Funnel tab, selecting any lead displays a detailed point audit—e.g. +30 for revenue, +20 for engagement—and lists which agents and tools contributed to the result."
- **[3:30 - 5:00] Persistence & State Synchronization**: "Sales reps can move tasks between 'To Do', 'In Progress', and 'Completed'. I built a synchronizer that writes task movements back to `data/history/{run_id}.json` to make sure changes persist. Users can also reload historical runs offline without invoking the LLM."

---

## 3. Recruiter Screening Pitch Script
*Recruiter: 'Can you tell me about your favorite project?'*

> "I recently built **BusinessPilot AI**, an autonomous multi-agent platform for B2B sales operations. It deploys a team of specialized AI agents that ingest lead datasets, prioritize contacts, compile Plotly charts, write PDF reports, and alert stakeholders. 
> 
> What makes this project unique is its **Model Context Protocol (MCP)** architecture. I decoupled the data tools into four isolated FastMCP servers running over stdio RPC. This means we can swap out our database without changing the core AI code. 
> 
> I also addressed a key trust issue in AI by building an **Explainable AI** scorecard showing why the agent prioritized each lead. It's fully dockerized and verified with a robust pytest suite."
