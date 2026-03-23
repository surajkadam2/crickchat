import time
from claude import ask_claude
from safety import extract_sql, is_sql_safe
from logger import log_question, log_execution_time

from config import (
    CRICKET_TABLE_MAPPING,
    CRICKET_BUSINESS_RULES,
    TEMPERATURE_SQL,
    MAX_HISTORY_ITEMS,
    CRICKET_JOIN_RULES
)

# Schema cache
_schema_cache = None


def get_cached_schema(get_schema_fn):
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = get_schema_fn()
    return _schema_cache


def build_system_prompt(schema: str) -> str:
    """
    Builds cricket-aware system prompt.
    """
    return f"""
    You are a cricket statistics expert and SQL Server specialist.

    Here is the database schema:
    {schema}

    {CRICKET_TABLE_MAPPING}

    {CRICKET_BUSINESS_RULES}

    {CRICKET_JOIN_RULES}

    Rules:
    - Return ONLY a valid SQL query
    - Do NOT include explanations or markdown
    - NEVER use SELECT *
    - ALWAYS select specific columns
    - ALWAYS use TOP N (limit results)
    - Use SQL Server syntax only
    - NEVER use DELETE, DROP, UPDATE, INSERT, TRUNCATE, ALTER, EXEC

    Cricket-specific rules:
    - Use the correct table based on format (ODI, T20, TEST)
    - If format is mentioned → use only that format table
    - If format is NOT mentioned → query all relevant format tables and UNION results
    - Use business rules for calculations (centuries, averages, strike rate, etc.)
    - When calculating win rates or percentages, always use 
      NULLIF to prevent divide by zero:
      CAST(SUM(wins) AS FLOAT) / NULLIF(COUNT(*), 0) * 100
    - When filtering match winners, always exclude NULL and 
      'No Result' and 'Tied' values:
      WHERE Match_Winner IS NOT NULL 
      AND Match_Winner NOT IN ('No Result', 'Tied', 'Match Tied')
    - When calculating team win rates, exclude combined/exhibition 
      teams: 'Asia XI', 'Africa XI', 'ICC World XI', 
      'World XI', 'Americas XI'
    - Only include actual cricket nations
    - Always round percentages to 2 decimal places using ROUND()
    - Always add % label to percentage columns using:
      CAST(ROUND(value, 2) AS VARCHAR) + '%' AS WinRate
    - Always ROUND overs to 1 decimal place
    - Always show meaningful column names aliases using AS, donnt show - characters in column names, use descriptive aliases instead
    - Never use modulo operator (%) on float columns in SQL Server
    - To convert balls to overs use: 
      CAST(balls/6 AS INT) + (balls % 6) * 0.1
      But only when balls column is INTEGER type
    - For overs already stored as decimal, use them directly
    - Always CAST float columns to INT before using modulo
    - When calculating overs from balls bowled:
      FLOOR(balls / 6.0) + (balls % 6) / 10.0
      First CAST balls to INT: CAST(balls AS INT)
    - For comparison queries, use a single query with 
      GROUP BY player name rather than two separate queries
    - Avoid subqueries where possible — use CTEs instead
    - Always CAST wickets, runs, matches to INT when displaying: CAST(SUM(wickets) AS INT) AS TotalWickets
    - Always ROUND averages and rates to 2 decimal places
    - ROUND(AVG(value), 2) or ROUND(SUM(runs)/NULLIF(SUM(wickets),0), 2)
    """


def build_full_prompt(question: str, schema: str, history: list) -> str:
    """
    Builds full prompt including conversation history.
    """
    system_prompt = build_system_prompt(schema)

    # Sliding window
    history = history[-MAX_HISTORY_ITEMS:] if history else []

    history_block = ""
    if history:
        history_block = "Previous conversation:\n"
        for item in history:
            history_block += f"Q: {item['question']}\nSQL: {item['sql']}\n\n"

    return f"""
{system_prompt}

{history_block}

User question:
{question}
"""


def ask_data_question(question: str, schema: str, history=None) -> dict:
    """
    Sends cricket question to Gemini with memory + validation.
    """
    start_time = time.time()
    history = history or []

    try:
        log_question(question)

        full_prompt = build_full_prompt(question, schema, history)

        raw_response = ask_claude(full_prompt)

        gemini_time = time.time() - start_time
        log_execution_time("Gemini response", gemini_time)

        sql = extract_sql(raw_response)

        if not sql:
            return {
                "success": False,
                "sql": None,
                "error": "No SQL generated",
                "gemini_time": gemini_time
            }

        if not is_sql_safe(sql):
            return {
                "success": False,
                "sql": sql,
                "error": "Unsafe SQL detected",
                "gemini_time": gemini_time
            }

        return {
            "success": True,
            "sql": sql,
            "error": None,
            "gemini_time": gemini_time
        }

    except Exception as e:
        gemini_time = time.time() - start_time
        return {
            "success": False,
            "sql": None,
            "error": str(e),
            "gemini_time": gemini_time
        }


if __name__ == "__main__":
    from db import get_schema

    schema = get_cached_schema(get_schema)

    history = []

    result = ask_data_question(
        "Top 5 batsmen with most centuries",
        schema,
        history
    )

    print(result)