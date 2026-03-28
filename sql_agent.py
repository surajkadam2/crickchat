# sql_agent.py
from agent_types import AgentContext
from prompt import ask_data_question
from db import run_query

def run(context: AgentContext) -> AgentContext:
    """
    SQL Agent — fetches cricket stats from the database.
    Accepts AgentContext, returns updated AgentContext.

    Args:
        context: AgentContext with question, schema, history

    Returns:
        AgentContext: updated with sql, rows, and sources
    """
    try:
        result = ask_data_question(
            context.question,
            context.schema,
            context.history
        )

        if not result["success"]:
            context.error = result["error"]
            return context

        db_result = run_query(result["sql"])

        context.sql = result["sql"]
        context.rows = db_result["rows"]
        context.sources.append("db")

    except Exception as e:
        context.error = str(e)

    return context

if __name__ == "__main__":
    from db import get_schema
    from prompt import get_cached_schema

    ctx = AgentContext(
        question="Who scored the most runs in ODIs?",
        schema=get_cached_schema(get_schema)
    )

    ctx = run(ctx)

    print(f"SQL:     {ctx.sql}")
    print(f"Rows:    {ctx.rows}")
    print(f"Sources: {ctx.sources}")
    print(f"Error:   {ctx.error}")