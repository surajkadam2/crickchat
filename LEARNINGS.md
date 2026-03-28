# 🧠 LEARNINGS.md — CrickChat

> A personal knowledge base built while going from **zero Python, zero AI**
> to a multi-agent RAG system in 2 weeks of evening sessions.
>
> These are lessons learned through building, breaking, swearing quietly,
> and fixing — not from tutorials.
>
> If you're reading this thinking *"I could never do this"* —
> that's exactly what I thought 2 weeks ago. Keep reading.

---

## 📖 Table of Contents

1. [How LLMs Work](#how-large-language-models-work)
2. [Prompt Engineering](#prompt-engineering)
3. [RAG — Retrieval Augmented Generation](#rag--retrieval-augmented-generation)
4. [Multi-Agent Architecture](#multi-agent-architecture)
5. [Architecture Principles](#architecture-principles)
6. [Testing & Quality](#testing--quality)
7. [Python Lessons](#python-lessons)
8. [AI System Design](#ai-system-design)
9. [Config Tuning](#config-tuning)
10. [Personal Lessons](#personal-lessons)

---

## How Large Language Models Work

**Tokenization**
Words are converted to numbers before the model processes them.
Every token costs money and consumes context window space.
*"Show me Sachin's centuries"* is not a sentence to the model — it is a list of numbers.

**Attention Mechanism**
The model maps relationships between all tokens simultaneously.
*"Show me customers from Germany"* — the model understands
*"Germany"* modifies *"customers"* through attention, not keyword matching.
This is why the schema you provide matters so much — the model is paying attention to it.

**Pattern Completion**
LLMs are trained on billions of examples. They predict the most
probable next token based on patterns seen in training data.
They do not "think." They complete patterns. Very, very well.

**Hallucination**
The model confidently generating wrong answers.
It does not know it is wrong. It is completing a pattern.
This is why grounding exists — you hand it the answer sheet.

> 💡 **Key Insight:** Schema quality = output quality.
> Better context = better SQL. Garbage in, garbage out
> applies to AI just as much as it applies to your old Java ETL jobs.

---

## Prompt Engineering

**System prompt is for rules and schema only.**
Never inject runtime or user-specific data into the system prompt.
Runtime data belongs in conversation history or the user message.
*(Yes, I learned this the hard way.)*

**Prompt instructions compete with training data.**
Strong training patterns can override weak prompt rules.
If your instruction fights the model's training — the training usually wins.
Write stronger instructions. Or accept the loss gracefully.

**Temperature controls randomness.**

| Value | Behaviour | Use for |
|-------|-----------|---------|
| `0.0` | Deterministic — same output every time | SQL generation, routing |
| `0.1` | Slight variation — feels natural | Explanations, synthesis |
| `1.0` | Maximum creativity — different every time | Never. Not here. |

Never set `TEMPERATURE_SQL` above `0.2` — causes silent wrong answers.
Silent wrong answers are worse than crashes. At least a crash tells you something broke.

**Security must never rely on prompt instructions alone.**
The model can be talked out of its instructions by a sufficiently clever user.
Hard-coded safety checks cannot be talked out of anything.

> *"Prompts control behavior. Code enforces safety."*
> — Learned this at week 1. Still true at week 2.

---

## RAG — Retrieval Augmented Generation

*The lesson that made current IPL data possible.*

**The Problem RAG Solves**
Your model was trained on data up to a certain date.
It does not know what happened yesterday.
If you ask *"How is Kohli performing in IPL 2025?"* without RAG —
the model either hallucinates or says *"I don't know."*
Neither is acceptable.

**What RAG Actually Is**
Not magic. Not fine-tuning. Not retraining.
You fetch relevant documents. You paste them into the prompt.
The model reads them like you handed it a newspaper.
Then it answers based on what it just read.

```
Without RAG:  Question → LLM (training only) → Answer
With RAG:     Question → Fetch docs → Inject → LLM → Grounded Answer
```

> 📰 **Think of it as:** Open book exam vs closed book exam.
> RAG = open book. You hand the AI the relevant pages.

**The 3 Steps of RAG**

1. **Retrieve** — find relevant documents (web search, vector DB, files)
2. **Augment** — inject retrieved content into the prompt
3. **Generate** — model answers using the injected content

That word **Augmented** in RAG = you augmented the prompt with fresh data.
The model did not learn anything new. You just gave it better context.

**Vector Embeddings**
Converting text to numbers where *similar meanings produce similar numbers*.
*"Kohli scored a century"* and *"Virat hit 100 runs"* — different words, similar meaning.
Embeddings capture that similarity. This is how semantic search works.

> 🗺️ **Think of it as:** GPS coordinates for meaning.
> Similar meanings = close coordinates on a map.

**Chunking**
Splitting large documents into smaller pieces before searching.
A 10,000 word match report gets split into 200-word chunks.
You retrieve only the relevant chunks — not the whole document.

> ✂️ **Think of it as:** Cutting a newspaper into individual articles before filing them.
> You retrieve the cricket article — not the entire newspaper.

**Grounding**
Restricting the AI to only use the retrieved content.
*"Answer using ONLY the provided data. Never invent facts."*
Grounding = the difference between a useful answer and a confident lie.

**What We Used — Gemini Built-in Google Search**
Instead of building a full RAG pipeline (fetch → chunk → embed → store → retrieve),
Gemini has a built-in `google_search` tool that does all of it internally.
One line of code. Zero extra infrastructure.

```python
tools=[types.Tool(google_search=types.GoogleSearch())]
```

That single addition gave CrickChat live IPL 2025 data.
Sometimes the best engineering decision is knowing what NOT to build.

---

## Multi-Agent Architecture

*The lesson that made everything more interesting.*

**What is an Agent?**
An LLM with a specific job and tools to do that job.
Not one LLM doing everything — one LLM doing one thing, well.

```
Before:  User → One LLM → Answer   (does everything, mediocrely)
After:   User → Router → Specialists → Synthesizer → Answer
```

**The Agent Pattern**
Every agent in CrickChat follows the same contract:

```python
def run(context: AgentContext) -> AgentContext:
    # 1. Read from context
    # 2. Do one job
    # 3. Write results back to context
    # 4. Return context
```

Accept context. Do one thing. Return updated context.
This is the relay race baton pattern — each agent passes the baton forward.

**The 4 Agents We Built**

| Agent | Job | Temperature |
|-------|-----|-------------|
| Router Agent | Classify question → sql / rag / both | 0.0 |
| SQL Agent | Generate + execute SQL | 0.0 |
| RAG Agent | Web search + grounding | 0.0 |
| Synthesizer | Merge results + label sources | 0.1 |

**Constrained Generation**
The Router must return exactly one word: `SQL`, `RAG`, or `BOTH`.
You achieve this by being extremely specific in the system prompt.
Then you validate the output — if it returns anything else, default to `SQL`.
Trust but verify. Actually, just verify.

**Parallel Execution**
SQL Agent and RAG Agent run simultaneously using `asyncio.gather`.
Total time = `max(SQL time, RAG time)` instead of `SQL time + RAG time`.

```python
# Sequential — slow (SQL + RAG time)
sql_result = sql_agent.run(ctx)
rag_result = rag_agent.run(ctx)

# Parallel — fast (max of SQL, RAG time)
sql_ctx, rag_ctx = await asyncio.gather(
    loop.run_in_executor(None, sql_agent.run, ctx),
    loop.run_in_executor(None, rag_agent.run, ctx)
)
```

> 🍳 **Think of it as:** Cooking rice and curry simultaneously
> instead of finishing one before starting the other.

**Why No Framework (Yet)**
We did not use LangChain or LangGraph.
We built agents as plain Python functions with a shared dataclass.
This was intentional — understanding beats abstraction.

```python
# LangChain way — you learn the framework
agent = AgentExecutor(agent=..., tools=tools)

# Our way — you learn the concept
ctx = sql_agent.run(ctx)      # you know exactly what this does
ctx = rag_agent.run(ctx)      # you wrote this file yourself
```

LangGraph will make complete sense when we get there —
because we already know what it's doing under the hood.

> 🏗️ **Rule:** Build it manually first. Use the framework second.
> Engineers who skip step 1 become framework users, not engineers.

**When Multi-Agent is NOT needed**
The most important lesson about multi-agent architecture:

> *"Don't add architecture for architecture's sake. Add it when you feel the pain."*

CrickChat did not need multi-agent for historical stats alone.
It needed it when RAG added a genuinely different data source.
The pain appeared. The architecture earned its complexity.

---

## Architecture Principles

**Single Responsibility Principle**
One module = one responsibility.
`claude.py` talks to AI. `db.py` talks to database. `safety.py` validates.
When something breaks, you know exactly where to look.
*(This never stops being true. Not in Java, not in Python, not in AI.)*

**Lazy Loading**
Load only when needed. Fail only when needed.
Schema is fetched on the first question, not on app startup.
If the database is down at startup — the app still launches.

**Externalized Configuration**
All magic numbers and settings live in `config.py`.
Change model name, temperature, or timeout in one place.
Config values need comments explaining valid ranges.

**Signal Protocol**
AI responses are treated as signals first, SQL second.

- Clean SQL → valid question, execute it
- `NOT_A_DB_QUESTION` → invalid input, tell the user
- `EXTRACTED:` → partial input recovery, warn and proceed
- `SQL` / `RAG` / `BOTH` → Router signals, parsed not read

**AgentContext as the Single Source of Truth**
Every agent reads from `AgentContext`. Every agent writes to `AgentContext`.
No hidden state. No global variables. No surprises.
The context object IS the conversation between agents.

---

## Testing & Quality

**Evals over manual testing**
Evals are coded once and run after every change.
Manual testing is time-consuming, inconsistent, and forgettable.
Evals catch regressions automatically.
*(You will thank yourself at 11pm when a new feature breaks something old.)*

**Three types of evals**

- Safety evals — does it block dangerous input?
- Correctness evals — does it return the right data?
- Functional evals — does it return data at all?

**Robust assertions**
Never assert exact column names from AI-generated SQL.
Assert values not structure.
`list(rows[0].values())[0]` is more resilient than `rows[0]['count']`
Brittle evals break on improvements, not just regressions.

**Always verify your verification**
Wrong manual calculation = false bug report.
Before blaming AI — check your test data.
In production: use known test data with pre-calculated expected results.

**Test data strategy**
Never run evals against production database.
Use dedicated test DB with seed data covering:
happy path, edge cases, and false positive scenarios.
Northwind is perfect seed data — static, diverse, realistic.

---

## Python Lessons

**Mutable default arguments — the silent trap**
```python
# DANGEROUS — history is shared across ALL calls
def function(history=[]):
    ...

# CORRECT — new list created for each call
def function(history=None):
    if history is None:
        history = []
```
Mutable defaults are shared across all function calls.
One of the hardest bugs to find in production.
You will encounter this once. You will never forget it.

**Docstrings are contracts**
A docstring tells you: what goes in, what comes out, what can fail.
An inline comment tells you: why this decision was made.
Never use `"""` for inline comments — use `#`.

**Why comments over what comments**
```python
# BAD — describes what code does (redundant, the code does this)
# Loop through rows

# GOOD — explains why decision was made
# Cap at 20 rows to prevent token overflow in Gemini context
```

**Dataclasses are better than dicts for structured data**
```python
# Dict — no type hints, no defaults, easy to typo the key
ctx = {"question": q, "rows": [], "sql": None}

# Dataclass — typed, defaulted, autocompleted
@dataclass
class AgentContext:
    question: str
    rows: list = field(default_factory=list)
    sql: Optional[str] = None
```
Use dicts for flexible data. Use dataclasses for contracts between components.

**select_dtypes gotcha — Pandas 4**
```python
# Pandas 4 changed this — use include not dtype
df.select_dtypes(include=['object', 'str'])   # correct
df.select_dtypes(include='object')             # also correct
```

---

## AI System Design

**Grounding prevents hallucination**
Restrict AI to provided data only.
Tell the model: use ONLY this data, never invent facts.
The more freedom given to AI, the more hallucination risk introduced.

**Conversation memory is an illusion**
LLMs have no memory between API calls.
Your app sends the full conversation history on every request.
This creates the illusion of memory — it is engineering, not magic.
*(The magic IS the engineering.)*

**Sliding window memory**
Keep last N exchanges. Drop oldest when limit reached.
Every message added = more tokens = more cost.
Balance context quality against API cost.

**Silent wrong answers are the most dangerous failures**
A query that crashes is safe — you know it failed.
A query that returns wrong data confidently is dangerous.
The user makes decisions based on incorrect information.
Design for silent failures as hard as you design for loud ones.

**Source labelling builds trust**
When you have multiple data sources, always tell the user which fact came from where.
`[DB] Career average: 51.76` + `[Web] IPL 2025: 657 runs`
Users trust labelled answers more than unlabelled answers.
Transparency is a feature.

**Confidence levels matter**
DB results = structured, validated, deterministic = high confidence.
Web results = articles, opinions, possibly outdated = medium confidence.
Your Synthesizer should weight them differently — and tell the user.

---

## Config Tuning

**MAX_ROWS_RETURNED is domain-specific**

| Domain | Value | Why |
|--------|-------|-----|
| Generic DB | 100 | Unknown query patterns |
| Cricket | 50 | Known patterns, wider but bounded |

Too low = truncated results = wrong answers.
Too high = token waste + slow responses.
Right value = maximum a legitimate query needs.

**MEMORY_WINDOW is a cost dial**
Every conversation turn you keep = more tokens per request = more cost.
5 turns is usually enough for cricket questions.
For a general-purpose assistant — maybe 10.
For a one-shot lookup tool — maybe 1.

---

## Personal Lessons

**Building beats watching. Every single time.**
Every tutorial watched is time not building.
Real learning happens when something breaks at 11pm
and you have to figure out why.
That frustration is the learning. Embrace it.

**Your 10 years transferred instantly.**
Java instincts, systems thinking, debugging discipline, reading errors —
none of that was wasted. It all transferred.
You were not starting from zero. You were changing languages.

**Fear of visibility held me back.**
For years I did great work that nobody saw.
Building in public is uncomfortable.
It is also how opportunities find you.
Chose to be visible. Still uncomfortable. Worth it.

**Consistency compounds more than talent.**
2 hours every evening beats 12 hours on a weekend.
The engineers winning in AI are not the smartest.
They are the most consistent.
Show up. Build something. Repeat.

**The right question beats the right answer.**
*"Does CrickChat really need multi-agent architecture?"*
That question saved a week of unnecessary complexity.
Always ask: does this solve a real problem I'm feeling right now?
If not — skip it, add it when the pain appears.

**You are not behind.**
There is no race. There is no finish line.
There are only people who started and people who haven't.
You started. That's the whole game.

---

*Last updated after Week 2 — multi-agent + RAG session.*
*Started: zero Python, zero AI.*
*Now: multi-agent RAG system with Streamlit UI.*
*Next: LangGraph, deployment, and whatever breaks next.*

> *"The best time to start was a year ago.*
> *The second best time is right now."*