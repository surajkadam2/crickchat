# =========================
# AI CONFIGURATION
# Controls model behavior for SQL generation and explanations
# =========================
GEMINI_MODEL = "gemini-2.5-flash"
TEMPERATURE_SQL = 0.0
TEMPERATURE_EXPLAIN = 0.1


# =========================
# DATABASE CONFIGURATION
# Controls query execution limits
# =========================
QUERY_TIMEOUT_SECONDS = 15  # cricket queries can be complex
MAX_ROWS_RETURNED = 50      # cricket needs more rows than generic


# =========================
# CRICKET DOMAIN CONTEXT
# Provides schema understanding and domain-specific rules
# =========================
CRICKET_TABLE_MAPPING = """
Table mapping by format and category:
- ODI batting stats → ODI_Batting
- ODI bowling stats → ODI_Bowling  
- ODI match results → ODI_Matches
- ODI partnerships → ODI_Partnerships
- T20 batting stats → T20_Batting
- T20 bowling stats → T20_Bowling
- T20 match results → T20_Matches
- Test batting stats → TEST_Batting
- Test bowling stats → TEST_Bowling
- Test match results → TEST_Matches
- Player information → Players (shared across formats)
"""

CRICKET_BUSINESS_RULES = """
Cricket calculations:
- Century = innings where runs >= 100
- Half century = innings where runs >= 50 AND runs < 100
- Duck = innings where runs = 0 AND isOut = 1
- Strike rate = (runs / balls) * 100
- Economy rate = runs conceded per over (conceded/overs)
- Batting average = total runs / total dismissals (isOut = 1)
- 5-wicket haul = innings where wickets >= 5
- Maiden over = overs bowled without conceding a run
- Win rate = (matches won / matches played) * 100
- Always exclude NULL, Tied, and No Result from win calculations
- Always use NULLIF(count, 0) to prevent divide by zero
- Batting average = total runs / NULLIF(total dismissals, 0)
"""


# =========================
# APP CONFIGURATION
# Controls CLI behavior and memory
# =========================
APP_NAME = "CrickChat"
APP_VERSION = "1.0"
CLI_PROMPT = "You: "
MAX_HISTORY_ITEMS = 5
MAX_ROWS_TO_EXPLAINER = 20


# =========================
# SAFETY CONFIGURATION
# Controls blocked keywords for user input and SQL queries
# =========================
DANGEROUS_INPUT_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER", "EXEC"
]

DANGEROUS_SQL_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER", "EXEC"
]