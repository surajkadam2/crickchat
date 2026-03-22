from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

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


def display_results(rows, sql, gemini_time, execution_time):
    if not rows:
        console.print("[yellow]No results found.[/yellow]")
        return

    table = Table(box=box.MINIMAL_DOUBLE_HEAD)

    columns = rows[0].keys()
    for col in columns:
        table.add_column(str(col), style="cyan", overflow="fold")

    for row in rows:
        table.add_row(*[str(row[col]) for col in columns])

    console.print(table)

    console.print(
        f"\n[dim]Rows: {len(rows)} | AI Time: {gemini_time:.2f}s | DB Time: {execution_time:.2f}s[/dim]"
    )


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
            result = ask_data_question(user_input, schema, history)

            if not result["success"]:
                console.print(f"[bold red]Error:[/bold red] {result['error']}")
                continue

            sql = result["sql"]
            gemini_time = result["gemini_time"]

            # ================= DB =================
            db_result = run_query(sql)

            rows = db_result["rows"]
            execution_time = db_result["execution_time"]

            # Save state
            last_question = user_input
            last_sql = sql
            last_gemini_time = gemini_time
            last_execution_time = execution_time

            # Update history
            history.append({
                "question": user_input,
                "sql": sql
            })
            if len(history) > MAX_HISTORY_ITEMS:
                history.pop(0)

            # ================= DISPLAY =================
            display_results(rows, sql, gemini_time, execution_time)

            if is_comparison_query(rows):
                display_comparison_card(rows, user_input)
            else:
                display_results(rows, result['sql'], 
                   result['gemini_time'], 
                   result['execution_time'])

            # ================= EXPLAIN =================
            explanation = explain_results(user_input, rows, sql)
            console.print(f"\n[bold green]Explanation:[/bold green] {explanation}")

        except Exception as e:
            log_error(str(e))
            console.print(f"[bold red]Error:[/bold red] {str(e)}")


if __name__ == "__main__":
    main()