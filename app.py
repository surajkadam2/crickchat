import streamlit as st
import pandas as pd
from prompt import ask_data_question, get_cached_schema
from db import run_query, get_schema
from safety import is_input_safe
from explainer import explain_results
from cards import is_comparison_query

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="CrickChat", page_icon="🏏", layout="wide")

# ── Light‑weight styling (only essential) ─────────────────────────────────────
st.markdown(
    """
    <style>
    /* Keep chat bubbles left‑aligned for the user and right‑aligned for the bot */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        flex-direction: row !important;
        justify-content: flex-start !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Brief data notice (kept minimal) ────────────────────────────────────────
st.info(
    "📊 Data covers international cricket up to 2024. Recent cricket data not included.",
    icon="ℹ️",
)

# ── Session State ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

if "messages" not in st.session_state:
    st.session_state.messages = []

if "schema" not in st.session_state:
    st.session_state.schema = get_cached_schema(get_schema)

# ── Sidebar – example questions only ────────────────────────────────────────
with st.sidebar:
    st.title("🏏 CrickChat")
    st.caption("Cricket statistics in plain English")
    st.divider()
    st.markdown("**Try asking**")
    example_questions = [
        "Who scored the most centuries in Test cricket?",
        "Compare Virat Kohli and Rohit Sharma in T20s",
        "Which team has the best win rate in ODIs?",
        "Who took the most wickets in ODIs?",
        "Best bowling average in Tests (min 50 wickets)?",
        "Which country won the most T20 matches?",
    ]
    for q in example_questions:
        if st.button(q, use_container_width=True):
            st.session_state.pending_question = q
    st.divider()
    st.caption("CricketStats DB · 16 tables · 300K+ rows")

# ── Chat History Display (no system UI inside chat bubbles) ─────────────────
for msg in st.session_state.messages:
    avatar = "🧑" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg["type"] == "text":
            st.write(msg["content"])
        elif msg["type"] == "table":
            st.table(msg["content"])
        elif msg["type"] == "comparison":
            names = msg.get("names", ["Player 1", "Player 2"])
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(names[0])
                st.table(msg["content"][0])
            with col2:
                st.subheader(names[1])
                st.table(msg["content"][1])

# ── Input Handling ───────────────────────────────────────────────────────────
NAME_KEYS = ["PlayerName", "player_name", "player", "name", "batsman", "bowler"]


def get_player_name(row, fallback):
    for key in NAME_KEYS:
        if key in row and row[key]:
            return str(row[key])
    return fallback


user_input = None
if "pending_question" in st.session_state:
    user_input = st.session_state.pending_question
    del st.session_state.pending_question

prompt = st.chat_input("Ask a cricket question...")
if prompt:
    user_input = prompt

# ── Process Question ────────────────────────────────────────────────────────
if user_input:
    # Show user message
    with st.chat_message("user", avatar="🧑"):
        st.write(user_input)
    st.session_state.messages.append(
        {"role": "user", "type": "text", "content": user_input}
    )

    # Safety check
    if not is_input_safe(user_input):
        error_msg = "That question doesn't look safe to process."
        with st.chat_message("assistant", avatar="🤖"):
            st.warning(error_msg)
        st.session_state.messages.append(
            {"role": "assistant", "type": "text", "content": error_msg}
        )
    else:
        # Main processing
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                result = ask_data_question(
                    user_input,
                    st.session_state.schema,
                    st.session_state.history,
                )

            # ── 1️⃣  LLM‑generation errors ─────────────────────────────────────
            if not result.get("success", False):
                friendly_error = "Error processing, try again."
                st.error(friendly_error)
                st.session_state.messages.append(
                    {"role": "assistant", "type": "text", "content": friendly_error}
                )
                # keep history entry (even if SQL is empty) so the conversation flow stays
                st.session_state.history.append(
                    {"question": user_input, "sql": result.get("sql", "")}
                )
                if len(st.session_state.history) > 5:
                    st.session_state.history.pop(0)
                st.stop()

            # ── 2️⃣  Run the generated SQL – catch any DB‑side errors ─────────────
            try:
                db_result = run_query(result["sql"])
                rows = db_result["rows"]
            except Exception as e:  # noqa: BLE001 – we deliberately swallow the stack
                # Show a clean, user‑friendly message instead of the traceback
                friendly_msg = "Data is not available."
                st.info(friendly_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "type": "text", "content": friendly_msg}
                )
                # Record the attempt in history (helps LLM stay on track)
                st.session_state.history.append(
                    {"question": user_input, "sql": result["sql"]}
                )
                if len(st.session_state.history) > 5:
                    st.session_state.history.pop(0)
                st.stop()

            # ── 3️⃣  Normal result handling ───────────────────────────────────────
            if not rows:
                no_res = "No results found."
                st.info(no_res)
                st.session_state.messages.append(
                    {"role": "assistant", "type": "text", "content": no_res}
                )
            elif is_comparison_query(rows):
                df = pd.DataFrame(rows)
                row1, row2 = df.iloc[0], df.iloc[1]

                p1_name = get_player_name(row1, "Player 1")
                p2_name = get_player_name(row2, "Player 2")

                drop_keys = [k for k in NAME_KEYS if k in df.columns]
                disp1 = row1.drop(labels=drop_keys).rename(p1_name).to_frame()
                disp2 = row2.drop(labels=drop_keys).rename(p2_name).to_frame()

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader(p1_name)
                    st.table(disp1)
                with col2:
                    st.subheader(p2_name)
                    st.table(disp2)

                explanation = explain_results(user_input, rows, result["sql"])
                st.write(explanation)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "type": "comparison",
                        "content": [disp1, disp2],
                        "names": [p1_name, p2_name],
                        "explanation": explanation,
                    }
                )
            else:
                df = pd.DataFrame(rows)
                # Limit rows for speed
                if len(df) > 100:
                    df = df.head(100)
                    st.caption("Showing first 100 rows.")
                st.table(df)

                explanation = explain_results(user_input, rows, result["sql"])
                st.write(explanation)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "type": "table",
                        "content": df,
                        "explanation": explanation,
                    }
                )

            # ── 4️⃣  Update conversation history (keep last 5) ─────────────────────
            st.session_state.history.append(
                {"question": user_input, "sql": result["sql"]}
            )
            if len(st.session_state.history) > 5:
                st.session_state.history.pop(0)