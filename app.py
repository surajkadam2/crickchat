import asyncio
import streamlit as st
import pandas as pd

from safety import is_input_safe
from cards import is_comparison_query
from prompt import get_cached_schema
from db import get_schema
from agent_types import AgentContext
from router import classify_question
import sql_agent
import rag_agent
import synthesizer

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="CrickChat", page_icon="🏏", layout="wide")

st.markdown("""
<style>
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    flex-direction: row !important;
    justify-content: flex-start !important;
}
</style>
""", unsafe_allow_html=True)

st.info(
    "📊 Data covers international cricket up to 2024. "
    "Current IPL 2025 and recent match data is fetched live from the web.",
    icon="ℹ️",
)

# ── Session State ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

if "messages" not in st.session_state:
    st.session_state.messages = []

if "schema" not in st.session_state:
    st.session_state.schema = get_cached_schema(get_schema)

# ── Orchestrator ──────────────────────────────────────────────────────────────
async def process_question(user_input, schema, history):
    ctx = AgentContext(
        question=user_input,
        schema=schema,
        history=history
    )

    ctx.question_type = classify_question(user_input)

    if ctx.question_type == "sql":
        ctx = sql_agent.run(ctx)

    elif ctx.question_type == "rag":
        ctx = rag_agent.run(ctx)

    elif ctx.question_type == "both":
        loop = asyncio.get_event_loop()
        sql_ctx, rag_ctx = await asyncio.gather(
            loop.run_in_executor(None, sql_agent.run, ctx),
            loop.run_in_executor(None, rag_agent.run, ctx)
        )
        ctx.rows = sql_ctx.rows
        ctx.sql = sql_ctx.sql
        ctx.web_results = rag_ctx.web_results
        ctx.sources = list(dict.fromkeys(sql_ctx.sources + rag_ctx.sources))

    ctx = synthesizer.run(ctx)
    return ctx

# ── Sidebar ───────────────────────────────────────────────────────────────────
NAME_KEYS = ["PlayerName", "player_name", "player", "name", "batsman", "bowler"]

def get_player_name(row, fallback):
    for key in NAME_KEYS:
        if key in row and row[key]:
            return str(row[key])
    return fallback

def source_badges(sources):
    badges = []
    for s in sources:
        if s == "db":
            badges.append("🟢 DB")
        elif s == "web":
            badges.append("🔵 Web")
    return " + ".join(badges)

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
        "How is Kohli performing in IPL 2025?",
        "Kohli career T20 average vs IPL 2025 form?",
    ]
    for q in example_questions:
        if st.button(q, use_container_width=True):
            st.session_state.pending_question = q
    st.divider()
    st.caption("CricketStats DB · 16 tables · 300K+ rows")

# ── Chat History Display ──────────────────────────────────────────────────────
for msg in st.session_state.messages:
    avatar = "🧑" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg["type"] == "text":
            st.write(msg["content"])
        elif msg["type"] == "table":
            st.table(msg["content"])
            if msg.get("explanation"):
                st.write(msg["explanation"])
            if msg.get("sources"):
                st.caption(f"Sources: {source_badges(msg['sources'])}")
        elif msg["type"] == "comparison":
            names = msg.get("names", ["Player 1", "Player 2"])
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(names[0])
                st.table(msg["content"][0])
            with col2:
                st.subheader(names[1])
                st.table(msg["content"][1])
            if msg.get("explanation"):
                st.write(msg["explanation"])
            if msg.get("sources"):
                st.caption(f"Sources: {source_badges(msg['sources'])}")
        elif msg["type"] == "web":
            st.write(msg["content"])
            if msg.get("sources"):
                st.caption(f"Sources: {source_badges(msg['sources'])}")

# ── Input Handling ────────────────────────────────────────────────────────────
user_input = None
if "pending_question" in st.session_state:
    user_input = st.session_state.pending_question
    del st.session_state.pending_question

prompt = st.chat_input("Ask a cricket question...")
if prompt:
    user_input = prompt

# ── Process Question ──────────────────────────────────────────────────────────
if user_input:
    with st.chat_message("user", avatar="🧑"):
        st.write(user_input)
    st.session_state.messages.append(
        {"role": "user", "type": "text", "content": user_input}
    )

    if not is_input_safe(user_input):
        with st.chat_message("assistant", avatar="🤖"):
            st.warning("That question doesn't look safe to process.")
        st.session_state.messages.append(
            {"role": "assistant", "type": "text",
             "content": "That question doesn't look safe to process."}
        )
    else:
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                ctx = asyncio.run(process_question(
                    user_input,
                    st.session_state.schema,
                    st.session_state.history
                ))

            if ctx.error:
                st.error("Error processing your question. Please try again.")
                st.session_state.messages.append(
                    {"role": "assistant", "type": "text",
                     "content": "Error processing your question."}
                )

            elif ctx.question_type == "rag" and not ctx.rows:
                # Web only answer
                st.write(ctx.explanation)
                st.caption(f"Sources: {source_badges(ctx.sources)}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "type": "web",
                    "content": ctx.explanation,
                    "sources": ctx.sources
                })

            elif not ctx.rows and not ctx.web_results:
                st.info("No results found.")
                st.session_state.messages.append(
                    {"role": "assistant", "type": "text",
                     "content": "No results found."}
                )

            elif ctx.rows and is_comparison_query(ctx.rows):
                df = pd.DataFrame(ctx.rows)
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

                st.write(ctx.explanation)
                st.caption(f"Sources: {source_badges(ctx.sources)}")

                st.session_state.messages.append({
                    "role": "assistant",
                    "type": "comparison",
                    "content": [disp1, disp2],
                    "names": [p1_name, p2_name],
                    "explanation": ctx.explanation,
                    "sources": ctx.sources
                })

            else:
                df = pd.DataFrame(ctx.rows)
                if len(df) > 100:
                    df = df.head(100)
                    st.caption("Showing first 100 rows.")
                st.table(df)
                st.write(ctx.explanation)
                st.caption(f"Sources: {source_badges(ctx.sources)}")

                st.session_state.messages.append({
                    "role": "assistant",
                    "type": "table",
                    "content": df,
                    "explanation": ctx.explanation,
                    "sources": ctx.sources
                })

            # Update history
            st.session_state.history.append({
                "question": user_input,
                "sql": ctx.sql or ""
            })
            if len(st.session_state.history) > 5:
                st.session_state.history.pop(0)