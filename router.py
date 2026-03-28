# router.py
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import time
from config import GEMINI_MODEL

# Load environment variables from .env
load_dotenv()

client =genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

ROUTER_SYSTEM_PROMPT = """
You are a routing agent for a cricket statistics assistant.

Your ONLY job is to classify a cricket question into exactly one of these three categories:

SQL   - Question is about historical cricket stats, records, career totals,
        all-time rankings, comparisons between players using past data.
        Examples:
        - "Who scored the most centuries in Test cricket?"
        - "Compare Kohli and Rohit in T20s"
        - "Best bowling average in ODIs?"
        - "Which team has the best win rate?"

RAG   - Question needs current, recent, or live information not in a database.
        Examples:
        - "How is Kohli performing in IPL 2025?"
        - "Latest cricket news"
        - "Who won yesterday's match?"
        - "Current IPL standings"

BOTH  - Question needs historical DB stats AND current web information together.
        Examples:
        - "Kohli's career average vs his current IPL 2025 form"
        - "How does Rohit's IPL 2025 performance compare to his career?"

Rules:
- Respond with ONLY one word: SQL or RAG or BOTH
- No explanation, no punctuation, no extra words
- When in doubt between SQL and BOTH, choose SQL
- When in doubt between RAG and BOTH, choose RAG
"""

def classify_question(question: str) -> str:
    """
    Classifies a cricket question into sql, rag, or both.

    Args:
        question: The user's cricket question

    Returns:
        str: "sql" | "rag" | "both"
    """
    try:
        start = time.time()

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=ROUTER_SYSTEM_PROMPT,
                temperature=0.0
            )
        )

        elapsed = time.time() - start
        result = response.text.strip().upper()

        # Validate — if unexpected response, default to SQL
        if result not in ["SQL", "RAG", "BOTH"]:
            return "sql"

        print(f"[Router] '{question[:50]}' → {result} ({elapsed:.2f}s)")
        return result.lower()

    except Exception as e:
        print(f"[Router] Error: {e} — defaulting to SQL")
        return "sql"


if __name__ == "__main__":
    test_questions = [
        "Who scored the most centuries in Test cricket?",
        "Compare Kohli and Rohit in T20s",
        "How is Kohli performing in IPL 2025?",
        "Latest cricket news today",
        "Kohli career average vs his IPL 2025 form",
        "Which team won the most T20 matches?",
        "Who won yesterday's IPL match?",
    ]

    for q in test_questions:
        result = classify_question(q)
        print(f"  → {result}\n")