# rag_agent.py
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

RAG_SYSTEM_PROMPT = """
You are a cricket news analyst with access to Google Search.

Your job:
1. Search for current, recent cricket information relevant to the question
2. Summarise what you find in clear, factual bullet points
3. Always include specific numbers, dates, and player names where available
4. If you cannot find relevant current information, say exactly: NO_CURRENT_DATA

Rules:
- Stick to cricket topics only
- Do not mix historical career stats with current news
- Cite the source of each fact (e.g. "According to ESPNCricinfo...")
- Maximum 5 bullet points
- No opinions, only facts from search results
"""

def run(context: AgentContext) -> AgentContext:
    """
    RAG Agent — searches web for current cricket information.
    Uses Gemini's built-in Google Search grounding tool.

    Args:
        context: AgentContext with question

    Returns:
        AgentContext: updated with web_results and sources
    """
    try:
        start = time.time()

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"Find current cricket information for: {context.question}",
            config=types.GenerateContentConfig(
                system_instruction=RAG_SYSTEM_PROMPT,
                temperature=0.0,
                tools=[types.Tool(
                    google_search=types.GoogleSearch()
                )]
            )
        )

        elapsed = time.time() - start
        result = response.text.strip()

        if "NO_CURRENT_DATA" in result:
            print(f"[RAG Agent] No current data found ({elapsed:.2f}s)")
            context.web_results = None
        else:
            print(f"[RAG Agent] Web results retrieved ({elapsed:.2f}s)")
            context.web_results = result
            context.sources.append("web")

    except Exception as e:
        print(f"[RAG Agent] Error: {e}")
        context.error = str(e)

    return context


if __name__ == "__main__":
    test_questions = [
        "How is Virat Kohli performing in IPL 2025?",
        "Who won the latest IPL match?",
        "Current IPL 2025 points table",
    ]

    for q in test_questions:
        print(f"\nQuestion: {q}")
        ctx = AgentContext(question=q)
        ctx = run(ctx)
        print(f"Sources:  {ctx.sources}")
        print(f"Results:\n{ctx.web_results}")
        print("-" * 60)