from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from agent_types import AgentContext
from router import classify_question
import sql_agent
import rag_agent
import synthesizer
import asyncio

from prompt import ask_data_question, get_cached_schema
from db import run_query, get_schema
from safety import is_input_safe
from logger import log_question, log_error
from explainer import explain_results
from config import APP_NAME, APP_VERSION, CLI_PROMPT, MAX_HISTORY_ITEMS

from cards import display_comparison_card, display_player_card, is_comparison_query


console = Console()


# =========================
# UI FUNCTIONS
# =========================
def print_welcome():
    welcome_text = f"""
🏏 [bold green]{APP_NAME} v{APP_VERSION}[/bold green]

[bold]Chat with Cricket Stats[/bold]

Formats: Test | ODI | T20

[bold]Example questions:[/bold]
- Who has scored the most centuries in Test cricket?
- Compare Virat Kohli and Rohit Sharma in T20s
- Which team has the best win rate in ODIs?
- Who took the most wickets in Test cricket?
- Show me top 10 batsmen by average in ODIs

[yellow]Type 'help' to see all commands[/yellow]
"""
    console.print(Panel(welcome_text, border_style="green"))


def print_help():
    console.print("\n[bold cyan]Commands:[/bold cyan]")
    console.print("• [green]exit[/green]    → Quit")
    console.print("• [green]help[/green]    → Show help")
    console.print("• [green]explain[/green] → Show conversation history")
    console.print("• [green]retry[/green]   → Retry with feedback")
    console.print("• [green]edit[/green]    → Edit last question")
    console.print("• [green]cls[/green]     → Clear screen\n")

def _fmt(val):
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    return str(val) if val is not None else ""

def display_results(rows, sql, gemini_time, execution_time):
    if not rows:
        console.print("[yellow]No results found.[/yellow]")
        return

    table = Table(box=box.MINIMAL_DOUBLE_HEAD)

    columns = rows[0].keys()
    for col in columns:
        table.add_column(str(col), style="cyan", overflow="fold")

    for row in rows:
        #table.add_row(*[str(row[col]) for col in columns])
        table.add_row(*[_fmt(row[col]) for col in columns])

    console.print(table)

    console.print(
        f"\n[dim]Rows: {len(rows)} | AI Time: {gemini_time:.2f}s | DB Time: {execution_time:.2f}s[/dim]"
    )

async def process_question(user_input, schema, history):
    """
    Orchestrator — routes question to the right agents
    and returns a completed AgentContext.
    """
    # Step 1 — Build context
    ctx = AgentContext(
        question=user_input,
        schema=schema,
        history=history
    )

    # Step 2 — Route
    ctx.question_type = classify_question(user_input)
    print(f"[Orchestrator] Route → {ctx.question_type}")

    # Step 3 — Run agents based on route
    if ctx.question_type == "sql":
        ctx = sql_agent.run(ctx)

    elif ctx.question_type == "rag":
        ctx = rag_agent.run(ctx)

    elif ctx.question_type == "both":
        # Run SQL and RAG in parallel
        loop = asyncio.get_event_loop()
        sql_ctx, rag_ctx = await asyncio.gather(
            loop.run_in_executor(None, sql_agent.run, ctx),
            loop.run_in_executor(None, rag_agent.run, ctx)
        )
        # Merge results from both
        ctx.rows = sql_ctx.rows
        ctx.sql = sql_ctx.sql
        ctx.web_results = rag_ctx.web_results
        #ctx.sources = sql_ctx.sources + rag_ctx.sources
        ctx.sources = list(dict.fromkeys(sql_ctx.sources + rag_ctx.sources))

    # Step 4 — Synthesize
    ctx = synthesizer.run(ctx)

    return ctx

# =========================
# MAIN CLI
# =========================
def main():
    print_welcome()

    schema = get_cached_schema(get_schema)

    last_question = None
    last_sql = None
    last_gemini_time = None
    last_execution_time = None

    history = []

    while True:
        try:
            user_input = console.input(f"[bold blue]{CLI_PROMPT}[/bold blue]").strip()

            if not user_input:
                continue

            cmd = user_input.lower()

            # ================= COMMANDS =================
            if cmd == "exit":
                console.print("[bold red]Goodbye 👋[/bold red]")
                break

            if cmd == "help":
                print_help()
                continue

            if cmd == "cls":
                console.clear()
                continue

            if cmd == "explain":
                if history:
                    console.print("\n[bold cyan]Conversation History:[/bold cyan]\n")
                    for item in history:
                        console.print(f"[green]Q:[/green] {item['question']}")
                        console.print(f"[cyan]SQL:[/cyan] {item['sql']}\n")
                else:
                    console.print("[yellow]No history available.[/yellow]")
                continue

            if cmd == "edit":
                if not last_question:
                    console.print("[yellow]No previous question.[/yellow]")
                    continue
                user_input = console.input(
                    f"[bold blue]Edit ({last_question}):[/bold blue] "
                ).strip()
                if not user_input:
                    continue

            if cmd == "retry":
                if not last_question:
                    console.print("[yellow]No previous question.[/yellow]")
                    continue
                feedback = console.input("[bold blue]What was wrong?[/bold blue] ")
                user_input = f"{last_question}\nFix this: {feedback}"

            # ================= SAFETY =================
            if not is_input_safe(user_input):
                console.print("[bold red]⚠ Unsafe input detected[/bold red]")
                continue

            log_question(user_input)

            # ================= AI =================
             # ── Replace the old AI + DB block with this ───────────────
            # Run orchestrator
            ctx = asyncio.run(process_question(
                user_input,
                schema,
                history
            ))

            if ctx.error:
                console.print(f"[bold red]Error:[/bold red] {ctx.error}")
                continue
            
            # Display results
            if ctx.rows:
                if is_comparison_query(ctx.rows):
                    display_comparison_card(ctx.rows, user_input)
                else:
                    display_results(
                        ctx.rows,
                        ctx.sql,
                        0,   # gemini_time now inside agent
                        0    # execution_time now inside agent
                    )

            # Show source badges
            if ctx.sources:
                source_str = " + ".join(
                    ["[green]DB[/green]" if s == "db" else "[blue]Web[/blue]"
                     for s in ctx.sources]
                )
                console.print(f"\n[dim]Sources: {source_str}[/dim]")

            # Show explanation
            if ctx.explanation:
                console.print(f"\n[bold green]Answer:[/bold green] {ctx.explanation}")

            # Update history
            history.append({
                "question": user_input,
                "sql": ctx.sql or ""
            })
            if len(history) > MAX_HISTORY_ITEMS:
                history.pop(0)

            # ================= DISPLAY =================
            #display_results(rows, sql, gemini_time, execution_time)

            #if is_comparison_query(rows):
            #    display_comparison_card(rows, user_input)
            #else:
            #    display_results(rows, sql, gemini_time, execution_time)

            ## ================= EXPLAIN =================
            #explanation = explain_results(user_input, rows, sql)

            #console.print(f"\n[bold green]Explanation:[/bold green] {explanation}")

        except Exception as e:
            log_error(str(e))
            console.print(f"[bold red]Error:[/bold red] {str(e)}")


if __name__ == "__main__":
    main()