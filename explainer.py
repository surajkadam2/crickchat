import time
from claude import ask_claude
from logger import log_execution_time
from config import MAX_ROWS_TO_EXPLAINER, TEMPERATURE_EXPLAIN


def explain_results(question: str, rows: list, sql: str) -> str:
    """
    Generates a concise natural language explanation of query results.
    
    Takes raw query results and the original question, then uses Claude to generate
    a short, human-friendly summary. Always uses lower temperature to ensure factual
    consistency with the provided data. Limits rows to prevent token waste on large
    result sets beyond what needs explanation.
    
    Args:
        question (str): The original user question that prompted the query.
        rows (list): List of result dictionaries from the database query.
        sql (str): The SQL query that was executed (for context).
        
    Returns:
        str: A 2-3 sentence plain English explanation of the query results.
        
    Raises:
        Exception: If Claude API call fails.
    """
    start_time = time.time()

    # Limit rows to prevent excessive token usage; sample of data is sufficient for explanation
    limited_rows = rows[:MAX_ROWS_TO_EXPLAINER] if rows else []

    # Format rows as simple list for Claude to parse easily
    rows_text = ""
    if not limited_rows:
        rows_text = "[]"
    else:
        rows_text = "\n".join([str(row) for row in limited_rows])

    # Build prompt with clear instructions for brevity and factuality
    prompt = f"""
You are a data analyst.

System rules:
- Answer in 2-3 sentences maximum
- Use ONLY the provided data
- Always include exact numbers
- Never invent facts
- If data is empty say: "No results found"
- Express uncertainty with: "Based on available data"

Original Question:
{question}

SQL Query:
{sql}

Data:
{rows_text}

Provide a clear answer:
"""

    response = ask_claude(prompt, temperature=TEMPERATURE_EXPLAIN)

    execution_time = time.time() - start_time
    log_execution_time("Explanation generation", execution_time)

    return response.strip()


if __name__ == "__main__":
    sample_rows = [
        {"CompanyName": "Alfreds Futterkiste", "Country": "Germany"},
        {"CompanyName": "Blauer See Delikatessen", "Country": "Germany"},
        {"CompanyName": "Drachenblut Delikatessen", "Country": "Germany"},
    ]
    
    result = explain_results(
        question="Show me customers from Germany",
        rows=sample_rows,
        sql="SELECT CompanyName, Country FROM Customers WHERE Country = 'Germany'"
    )
    print("Explanation:\n", result)