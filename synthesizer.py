# synthesizer.py
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
import time
from config import GEMINI_MODEL
from agent_types import AgentContext

# Load environment variables from .env
load_dotenv()

client =genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYNTHESIZER_PROMPT = """
You are a cricket analyst who combines historical statistics with current news.

You will receive:
- HISTORICAL DATA: Facts from a cricket statistics database (always reliable)
- CURRENT NEWS: Recent information from web search (reliable but may be incomplete)

Your job:
1. Combine both sources into one clear, flowing answer
2. Always mention where each fact comes from using [DB] or [Web] tags
3. Lead with the most interesting insight
4. Keep it to 3-4 sentences maximum
5. If only one source is available, use that source only
6. Never contradict the database facts with web speculation

Example output:
"[DB] Virat Kohli has a career T20 average of 51.76 across 125 matches.
[Web] In IPL 2025, he scored 657 runs at an average of 54.75, helping
RCB win their first IPL title. His current form is actually above his
career average — a remarkable consistency at the highest level."
"""

def run(context: AgentContext) -> AgentContext:
    """
    Synthesizer — combines SQL Agent and RAG Agent results
    into one coherent answer with source labels.

    Args:
        context: AgentContext with rows and/or web_results

    Returns:
        AgentContext: updated with explanation and sources
    """
    try:
        # Build the content based on what's available
        parts = []

        if context.rows:
            parts.append(f"HISTORICAL DATA (from database):\n{context.rows}")

        if context.web_results:
            parts.append(f"CURRENT NEWS (from web search):\n{context.web_results}")

        if not parts:
            context.explanation = "No data found from any source."
            return context

        combined = "\n\n".join(parts)
        prompt = f"Question: {context.question}\n\n{combined}"

        start = time.time()

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYNTHESIZER_PROMPT,
                temperature=0.1
            )
        )

        elapsed = time.time() - start
        context.explanation = response.text.strip()

        print(f"[Synthesizer] Answer generated ({elapsed:.2f}s) "
              f"sources={context.sources}")

    except Exception as e:
        print(f"[Synthesizer] Error: {e}")
        context.error = str(e)

    return context


if __name__ == "__main__":
    # Test 1 — SQL only
    print("=" * 60)
    print("TEST 1 — SQL only (historical question)")
    print("=" * 60)
    ctx = AgentContext(
        question="Who scored the most runs in ODIs?",
        rows=[{"PlayerName": "Sachin Tendulkar", "TotalRunsScored": 18426}],
        sources=["db"]
    )
    ctx = run(ctx)
    print(f"\n{ctx.explanation}\n")

    # Test 2 — RAG only
    print("=" * 60)
    print("TEST 2 — RAG only (current question)")
    print("=" * 60)
    ctx = AgentContext(
        question="How is Kohli performing in IPL 2025?",
        web_results="Kohli scored 657 runs in IPL 2025 at average 54.75. "
                    "RCB won their first IPL title. "
                    "Kohli was RCB's leading run getter.",
        sources=["web"]
    )
    ctx = run(ctx)
    print(f"\n{ctx.explanation}\n")

    # Test 3 — BOTH sources
    print("=" * 60)
    print("TEST 3 — BOTH sources (career + current)")
    print("=" * 60)
    ctx = AgentContext(
        question="Kohli career T20 average vs IPL 2025 form?",
        rows=[{"PlayerName": "Virat Kohli", "BattingAverage": 51.76,
               "TotalRuns": 4037, "TotalMatches": 50}],
        web_results="Kohli scored 657 runs in IPL 2025 at average 54.75. "
                    "RCB won their first IPL title.",
        sources=["db", "web"]
    )
    ctx = run(ctx)
    print(f"\n{ctx.explanation}\n")