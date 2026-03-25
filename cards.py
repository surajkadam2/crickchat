from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Metrics where LOWER is better
LOWER_IS_BETTER = {"economy", "economy_rate", "avg_conceded"}


def is_comparison_query(rows):
    """
    Returns True if exactly 2 rows (comparison case).
    """
    return len(rows) == 2


def _is_number(value):
    try:
        float(value)
        return True
    except:
        return False


def _better_value(metric, val1, val2):
    """
    Determines which value is better.
    """
    metric_lower = metric.lower()

    if not (_is_number(val1) and _is_number(val2)):
        return None, None  # can't compare

    v1, v2 = float(val1), float(val2)

    # Decide rule
    if any(k in metric_lower for k in LOWER_IS_BETTER):
        # Lower is better
        if v1 < v2:
            return "p1", "lower"
        elif v2 < v1:
            return "p2", "lower"
    else:
        # Higher is better
        if v1 > v2:
            return "p1", "higher"
        elif v2 > v1:
            return "p2", "higher"

    return None, None

def _fmt(val):
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    return str(val) if val is not None else ""

def display_comparison_card(rows, question):
    """
    Displays side-by-side comparison for 2 players.
    """
    if len(rows) != 2:
        console.print("[red]Comparison requires exactly 2 rows[/red]")
        return

    row1, row2 = rows[0], rows[1]

    # Try to detect player names
    p1_name = str(row1.get("player") or row1.get("name") or "Player 1")
    p2_name = str(row2.get("player") or row2.get("name") or "Player 2")

    table = Table(title="🏏 Player Comparison", show_lines=True)

    table.add_column("Metric", style="bold cyan")
    table.add_column(p1_name, style="green")
    table.add_column(p2_name, style="magenta")

    for key in row1.keys():
        if key.lower() in ["player", "name"]:
            continue

        val1 = row1.get(key)
        val2 = row2.get(key)

        better, _ = _better_value(key, val1, val2)

        #val1_str = str(val1)
        #val2_str = str(val2)

        # AFTER
        val1_str = _fmt(val1)
        val2_str = _fmt(val2)

        if better == "p1":
            val1_str = f"[bold green]{val1_str}[/bold green]"
        elif better == "p2":
            val2_str = f"[bold green]{val2_str}[/bold green]"

        table.add_row(key, val1_str, val2_str)

    console.print(table)


def display_player_card(rows, question):
    """
    Displays a single player card.
    """
    if not rows:
        console.print("[yellow]No data available[/yellow]")
        return

    row = rows[0]

    player_name = str(row.get("player") or row.get("name") or "Player")

    table = Table(show_header=False, box=None)

    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    for key, value in row.items():
        if key.lower() in ["player", "name"]:
            continue
        table.add_row(key, _fmt(value))

    panel = Panel(table, title=f"🏏 {player_name}", border_style="green")

    console.print(panel)