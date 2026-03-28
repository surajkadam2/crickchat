# 🏏 CrickChat

> Ask cricket statistics in plain English. Get real answers from real data — historical and live.

```
You ask:   "Kohli career T20 average vs IPL 2025 form?"
CrickChat: "[DB] Virat Kohli has a career T20 average of 51.76 across 50 matches.
            [Web] In IPL 2025, he scored 657 runs at an average of 54.75,
            helping RCB win their first IPL title."
```

Built with **Google Gemini AI** + **SQL Server** + **Python** + **Multi-Agent Architecture**.
300,000+ rows of real ODI, T20, and Test match data. Live web search for current cricket news.

---

## What It Does

CrickChat routes your question to the right agent — historical database, live web search, or both — then synthesizes a grounded answer with source labels.

No SQL knowledge required. Just ask.

```
> Which team has the best win rate in ODIs?
  [DB] South Africa — 63.66% win rate across all ODI matches.

> How is Kohli performing in IPL 2025?
  [Web] Virat Kohli scored 657 runs in 15 matches at an average of 54.75.
        RCB won their maiden IPL title. He was the tournament's third-highest scorer.

> Kohli career T20 average vs IPL 2025 form?
  [DB] Career T20 average: 51.76 across 50 matches.
  [Web] IPL 2025: 657 runs at 54.75 — above his career average.
        A remarkable consistency at the highest level.
```

---

## Features

- **Multi-agent architecture** — Router → SQL Agent + RAG Agent (parallel) → Synthesizer
- **Live web search** — current IPL data, recent match results via Gemini grounding
- **Source labels** — every fact tagged 🟢 DB or 🔵 Web
- **Natural language → SQL** in under 2 seconds
- **Multi-format support** — ODI, T20, and Test cricket
- **Multi-table JOINs** — handles complex cross-table queries automatically
- **Player comparison cards** — side-by-side stat comparisons
- **Conversation memory** — follow-up questions work naturally
- **Plain English answers** — grounded in real data, no hallucination
- **Two-layer safety** — validates input before AI, validates SQL before execution
- **Streamlit web UI** — full browser chat interface
- **CLI interface** — Rich terminal UI with conversation memory
- **16 tables, 300,000+ rows** of real historical cricket data

---

## Architecture

```
User Question
      │
      ▼
┌─────────────┐
│   Safety    │  Layer 1 — validate input before any agent sees it
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Router    │  Classifies question → "sql" | "rag" | "both"
│   Agent     │  Temperature 0.0 — deterministic routing
└──────┬──────┘
       │
   ┌───┴────────────┐
   │                │
   ▼                ▼
┌──────────┐  ┌──────────────┐
│   SQL    │  │  RAG Agent   │  ← run in parallel for "both"
│  Agent   │  │              │
│          │  │ Gemini web   │
│ prompt   │  │ search +     │
│  .py +   │  │ grounding    │
│  db.py   │  │              │
└────┬─────┘  └──────┬───────┘
     │                │
     └───────┬─────────┘
             │
             ▼
    ┌─────────────────┐
    │   Synthesizer   │  Merges DB + Web results
    │                 │  Labels sources [DB] / [Web]
    │                 │  Temperature 0.1
    └────────┬────────┘
             │
             ▼
      Final Answer
   🟢 DB facts + 🔵 Web facts
```

**Key design decisions:**
- `Temperature 0.0` for Router and SQL — deterministic, reproducible
- `Temperature 0.1` for Synthesizer — slight flexibility for natural language
- SQL Agent and RAG Agent run in **parallel** for "both" questions — saves time
- Schema cached after first query — no repeated DB roundtrips
- Each agent accepts and returns `AgentContext` — clean handoff pattern
- Gemini built-in Google Search grounding — zero extra infrastructure

---

## Agent Types

| Agent | File | Job |
|-------|------|-----|
| Router Agent | `router.py` | Classifies question as sql / rag / both |
| SQL Agent | `sql_agent.py` | Generates + executes SQL against DB |
| RAG Agent | `rag_agent.py` | Web search via Gemini grounding |
| Synthesizer | `synthesizer.py` | Merges results, labels sources |

---

## Example Queries

**Historical stats (SQL Agent)**
```
Who scored the most runs in ODIs?
Which batsman has the best average in Tests (min 50 innings)?
Who took the most wickets in ODIs?
Which team has the best win rate in ODIs?
Compare Virat Kohli and Rohit Sharma in T20s
```

**Current / live data (RAG Agent)**
```
How is Kohli performing in IPL 2025?
Who won the latest IPL match?
Current IPL 2025 points table
Latest cricket news
```

**Combined — DB + Web (both agents in parallel)**
```
Kohli career T20 average vs IPL 2025 form?
How does Rohit's IPL 2025 performance compare to his career stats?
```

**Follow-ups (conversation memory)**
```
> Who scored the most centuries in ODIs?
  Sachin Tendulkar, 49 centuries.

> What about in Tests?         ← follow-up, no repetition needed
  Also Sachin Tendulkar, with 51 centuries.
```

---

## Installation

### Prerequisites

- Python 3.9+
- SQL Server (local or Azure)
- Google Gemini API key — [get one free](https://aistudio.google.com/)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/surajkadam2/crickchat.git
cd crickchat

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your credentials (see below)

# 4. Load cricket data
python load_cricket.py

# 5a. Run CLI
python main.py

# 5b. Run web UI
streamlit run app.py
```

### Environment Variables

```env
# .env
GEMINI_API_KEY=your_gemini_api_key_here
DB_SERVER=your_sql_server_host
DB_NAME=CricketStats
DB_USERNAME=your_db_username
DB_PASSWORD=your_db_password
```

---

## Project Structure

```
crickchat/
├── app.py            → Streamlit web UI — chat interface with source badges
├── main.py           → CLI entry point — Rich UI + conversation memory
├── agent_types.py    → AgentContext dataclass — shared contract between agents
├── router.py         → Router Agent — classifies question type
├── sql_agent.py      → SQL Agent — wraps prompt.py + db.py
├── rag_agent.py      → RAG Agent — Gemini web search grounding
├── synthesizer.py    → Synthesizer — merges + labels multi-source results
├── config.py         → All configuration, domain context, business rules
├── prompt.py         → Cricket-aware system prompt, schema caching
├── db.py             → SQL Server connection, FK schema extraction
├── safety.py         → Two-layer input + SQL validation
├── explainer.py      → Grounded plain English answer generation
├── cards.py          → Player comparison card renderer
├── logger.py         → Dual logging — console + file
├── load_cricket.py   → One-time CSV → SQL Server data loader
├── .env.example      → Safe onboarding template
├── requirements.txt  → Dependencies
└── README.md         → You are here
```

---

## Database Schema

```
CricketStats Database — 16 Tables

Batting:      ODI_Batting | T20_Batting | TEST_Batting
Bowling:      ODI_Bowling | T20_Bowling | TEST_Bowling
Matches:      ODI_Matches | T20_Matches | TEST_Matches
Partnerships: ODI_Partnerships | T20_Partnerships | TEST_Partnerships
Fall of Wkts: ODI_FallOfWickets | T20_FallOfWickets | TEST_FallOfWickets
Players:      Players (shared across all formats)
```

---

## Safety

CrickChat uses a **two-layer safety system**:

| Layer | What it checks | When |
|-------|---------------|------|
| Input validation | Blocks injection attempts, off-topic abuse | Before any agent |
| SQL validation | Blocks DROP, DELETE, INSERT, UPDATE, EXEC | Before DB execution |

The AI uses a **signal protocol** — responses are treated as signals first:
- `NOT_A_DB_QUESTION` → politely redirects non-cricket questions
- `EXTRACTED:` → strips prefix before executing SQL

---

## Dependencies

```
google-genai          → Gemini AI SDK (new)
sqlalchemy            → SQL Server connection
pyodbc                → ODBC driver
python-dotenv         → Environment variable management
rich                  → Terminal UI and formatting
pandas                → Result processing
streamlit             → Web UI
```

---

## Related Project

**DataChat** — the generic version of this tool. Query *any* SQL Server database in plain English.
→ [github.com/surajkadam2/datachat](https://github.com/surajkadam2/datachat)

CrickChat is built on the same core architecture as DataChat, extended with cricket-specific domain context, multi-agent routing, RAG integration, and a Streamlit UI.

---

## What I Learned Building This

From zero Python and zero AI knowledge to a multi-agent AI product in 2 weeks of evening sessions.

Key insights:
- **Schema quality = output quality.** The AI is only as good as what you tell it about the data.
- **Grounding beats creativity.** Temperature 0.0 + exact numbers = no hallucination.
- **Build agents manually before using frameworks.** Understanding what LangChain does under the hood makes you a better engineer.
- **Prompts control behavior. Code enforces safety.** Never rely on the AI to self-police dangerous queries.
- **Don't add architecture for architecture's sake.** Multi-agent earned its place when RAG added a genuinely different data source.

Full learning journal: [LEARNINGS.md](./LEARNINGS.md)

---

## Roadmap

- [x] CLI with Rich UI
- [x] Streamlit web UI
- [x] Multi-agent architecture
- [x] RAG — live web search via Gemini grounding
- [x] Source labels — [DB] and [Web] per fact
- [ ] Deploy to Streamlit Cloud + Azure SQL
- [ ] LangGraph refactor — rebuild agents using proper framework
- [ ] Plotly charts for visual stat comparisons

---

## Author

**Suraj Kadam** — Java/SQL developer, 10 years experience, now building AI products.
→ [github.com/surajkadam2](https://github.com/surajkadam2)

---

*Built in 2 weeks. Powered by curiosity.*