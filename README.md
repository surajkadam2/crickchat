# 🏏 CrickChat

> Ask cricket statistics in plain English. Get real answers from real data.

```
You ask:   "Who scored the most centuries in Test cricket?"
CrickChat: "Sachin Tendulkar scored 51 centuries in Test cricket,
            the most by any batsman in history."
```

Built with **Google Gemini AI** + **SQL Server** + **Python**.  
300,000+ rows of real ODI, T20, and Test match data.

---

## What It Does

CrickChat converts natural language questions into SQL queries against a real cricket statistics database — then explains the answer in plain English.

No SQL knowledge required. Just ask.

```
> Which team has the best win rate in ODIs?
  South Africa — 63.66% win rate across all ODI matches.

> Who took the most wickets in ODIs?
  Muttiah Muralitharan with 534 wickets across his ODI career.

> Compare Virat Kohli and Rohit Sharma in T20s
  ┌─────────────────────┬──────────────┬──────────────┐
  │ Stat                │ Virat Kohli  │ Rohit Sharma │
  ├─────────────────────┼──────────────┼──────────────┤
  │ Matches             │ 125          │ 159          │
  │ Runs                │ 4,008        │ 4,231        │
  │ Average             │ 52.73        │ 32.05        │
  │ Strike Rate         │ 137.96       │ 139.11       │
  └─────────────────────┴──────────────┴──────────────┘
```

---

## Features

- **Natural language → SQL** in under 2 seconds
- **Multi-format support** — ODI, T20, and Test cricket
- **Multi-table JOINs** — handles complex cross-table queries automatically
- **Player comparison cards** — side-by-side stat comparisons
- **Conversation memory** — follow-up questions work naturally
- **Plain English answers** — grounded in real data, no hallucination
- **Two-layer safety** — validates input before AI, validates SQL before execution
- **16 tables, 300,000+ rows** of real historical cricket data

---

## Database Schema

```
CricketStats Database — 16 Tables

Batting:     ODI_Batting | T20_Batting | TEST_Batting
Bowling:     ODI_Bowling | T20_Bowling | TEST_Bowling
Matches:     ODI_Matches | T20_Matches | TEST_Matches
Partnerships: ODI_Partnerships | T20_Partnerships | TEST_Partnerships
Fall of Wkts: ODI_FallOfWickets | T20_FallOfWickets | TEST_FallOfWickets
Players:     Players (shared across all formats)
```

---

## Architecture

```
User Question
     │
     ▼
┌─────────────┐
│  Safety     │  Layer 1 — validate input before AI sees it
│  (safety.py)│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Prompt     │  Cricket-aware system prompt + schema + JOIN rules
│  (prompt.py)│  Schema cached after first load
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Gemini AI  │  Temperature 0.0 for SQL, 0.1 for explanation
│  (claude.py)│  Signal protocol: NOT_A_DB_QUESTION | EXTRACTED
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Safety     │  Layer 2 — validate SQL before execution
│  (safety.py)│  Blocks DROP, DELETE, INSERT, UPDATE, etc.
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Database   │  SQL Server execution + FK schema extraction
│  (db.py)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Explainer  │  Grounds answer in real data, 2–3 sentence limit
│ (explainer) │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Cards      │  Player comparison cards for head-to-head queries
│  (cards.py) │
└─────────────┘
```

**Key design decisions:**
- `Temperature 0.0` for SQL generation — deterministic, reproducible
- `Temperature 0.1` for explanations — slight flexibility for natural language
- Schema is cached after first query — no repeated DB roundtrips
- System prompt contains rules + schema only — no runtime data injected

---

## Example Queries

**Batting**
```
Who scored the most runs in ODIs?
Which batsman has the best average in Tests (min 50 innings)?
Who hit the most sixes in T20 internationals?
List the top 5 century scorers in Test cricket.
```

**Bowling**
```
Who took the most wickets in ODIs?
Best bowling average in Tests with minimum 50 wickets?
Which bowler has the most five-wicket hauls in T20s?
```

**Teams**
```
Which country won the most T20 matches?
Which team has the best win rate in ODIs?
How many Test matches has Australia won at home?
```

**Comparisons**
```
Compare Virat Kohli and Rohit Sharma in T20s
Compare India and Australia in ODI win rates
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

# 5. Run CrickChat
python main.py
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
├── main.py           → CLI entry point, conversation memory, Rich UI
├── config.py         → All configuration, domain context, business rules
├── claude.py         → Gemini AI interface, temperature control
├── db.py             → SQL Server connection, FK schema extraction
├── safety.py         → Two-layer input + SQL validation
├── prompt.py         → Cricket-aware system prompt, schema caching
├── explainer.py      → Grounded plain English answer generation
├── cards.py          → Player comparison card renderer
├── logger.py         → Dual logging — console + file
├── load_cricket.py   → One-time CSV → SQL Server data loader
├── .env.example      → Safe onboarding template
├── requirements.txt  → 5 clean dependencies
└── README.md         → You are here
```

---

## Safety

CrickChat uses a **two-layer safety system**:

| Layer | What it checks | When |
|-------|---------------|------|
| Input validation | Blocks injection attempts, off-topic abuse | Before AI call |
| SQL validation | Blocks DROP, DELETE, INSERT, UPDATE, EXEC | Before DB execution |

The AI also uses a **signal protocol** — responses are treated as signals first, SQL second:
- `NOT_A_DB_QUESTION` → politely redirects non-cricket questions
- `EXTRACTED:` → strips prefix before executing SQL

---

## Dependencies

```
google-generativeai   → Gemini AI SDK
pyodbc                → SQL Server connection
python-dotenv         → Environment variable management
rich                  → Terminal UI and formatting
pandas                → Result processing
```

---

## Related Project

**DataChat** — the generic version of this tool. Query *any* SQL Server database in plain English.  
→ [github.com/surajkadam2/datachat](https://github.com/surajkadam2/datachat)

CrickChat is built on the same core architecture as DataChat, extended with cricket-specific domain context, JOIN rules, and comparison cards.

---

## What I Learned Building This

This project went from zero Python and zero AI knowledge to a working product in 5 days of 2-hour evening sessions.

Key insights:
- **Schema quality = output quality.** The AI is only as good as what you tell it about the data.
- **Grounding beats creativity.** Temperature 0.0 + exact numbers = no hallucination.
- **Semantic mismatches are silent killers.** A column named `batsman` that contains `player_id` — and the AI joins wrong silently.
- **Prompts control behavior. Code enforces safety.** Never rely on the AI to self-police dangerous queries.

Full learning journal: [LEARNINGS.md](./LEARNINGS.md)

---

## Roadmap

- [ ] Streamlit web UI with Plotly charts
- [ ] Multi-agent architecture (Router → SQL Agent → Stats Agent → Synthesizer)
- [ ] RAG integration — combine stats with news articles
- [ ] Azure SQL + Streamlit Cloud deployment
- [ ] IPL live match data integration

---

## Author

**Suraj Kadam** — Java/SQL developer, 10 years experience, now building AI products.  
→ [github.com/surajkadam2](https://github.com/surajkadam2)

---

*Built in 5 days. Powered by curiosity.*