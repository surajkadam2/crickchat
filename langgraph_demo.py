# langgraph_demo.py
# A minimal LangGraph demo — 3 nodes, conditional edges, typed state
# No DB, no RAG — just pure LangGraph concepts

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.5-flash"  # from config.py, but hardcoded here for simplicity

# ── State — shared object passed between all nodes ─────────────────────────────
# This is your AgentContext — but as a TypedDict
class CricketState(TypedDict):
    question: str
    category: Optional[str]    # set by classifier node
    answer: Optional[str]      # set by specialist node
    formatted: Optional[str]   # set by formatter node

# ── Node 1 — Classifier ────────────────────────────────────────────────────────
def classifier_node(state: CricketState) -> CricketState:
    """
    Reads the question.
    Returns category: "batting" | "bowling" | "general"
    """
    print(f"\n[Classifier] Question: {state['question']}")

    response = client.models.generate_content(
        model=MODEL,
        contents=state["question"],
        config=types.GenerateContentConfig(
            system_instruction="""
            Classify this cricket question into exactly one word:
            batting  — if about runs, centuries, averages, batting records
            bowling  — if about wickets, economy, bowling averages
            general  — if about teams, matches, or anything else
            Reply with ONE word only: batting or bowling or general
            """,
            temperature=0.0
        )
    )

    category = response.text.strip().lower()
    if category not in ["batting", "bowling", "general"]:
        category = "general"

    print(f"[Classifier] Category → {category}")
    return {"category": category}

# ── Node 2a — Batting Specialist ───────────────────────────────────────────────
def batting_node(state: CricketState) -> CricketState:
    """Answers batting questions."""
    print(f"[Batting Node] Answering: {state['question']}")

    response = client.models.generate_content(
        model=MODEL,
        contents=state["question"],
        config=types.GenerateContentConfig(
            system_instruction="""
            You are a cricket batting expert.
            Answer in exactly 2 sentences.
            Focus only on batting statistics and records.
            Be specific with numbers.
            """,
            temperature=0.1
        )
    )

    print(f"[Batting Node] Done")
    return {"answer": response.text.strip()}

# ── Node 2b — Bowling Specialist ───────────────────────────────────────────────
def bowling_node(state: CricketState) -> CricketState:
    """Answers bowling questions."""
    print(f"[Bowling Node] Answering: {state['question']}")

    response = client.models.generate_content(
        model=MODEL,
        contents=state["question"],
        config=types.GenerateContentConfig(
            system_instruction="""
            You are a cricket bowling expert.
            Answer in exactly 2 sentences.
            Focus only on bowling statistics and records.
            Be specific with numbers.
            """,
            temperature=0.1
        )
    )

    print(f"[Bowling Node] Done")
    return {"answer": response.text.strip()}

# ── Node 2c — General Specialist ───────────────────────────────────────────────
def general_node(state: CricketState) -> CricketState:
    """Answers general cricket questions."""
    print(f"[General Node] Answering: {state['question']}")

    response = client.models.generate_content(
        model=MODEL,
        contents=state["question"],
        config=types.GenerateContentConfig(
            system_instruction="""
            You are a cricket expert.
            Answer in exactly 2 sentences.
            Be specific and factual.
            """,
            temperature=0.1
        )
    )

    print(f"[General Node] Done")
    return {"answer": response.text.strip()}

# ── Node 3 — Formatter ─────────────────────────────────────────────────────────
def formatter_node(state: CricketState) -> CricketState:
    """
    Formats the final answer with category label.
    Every node in LangGraph must return state updates.
    """
    print(f"[Formatter] Formatting answer")

    category_emoji = {
        "batting": "🏏",
        "bowling": "🎳",
        "general": "🏆"
    }

    emoji = category_emoji.get(state["category"], "🏏")
    formatted = (
        f"{emoji} [{state['category'].upper()}]\n"
        f"{state['answer']}"
    )

    print(f"[Formatter] Done")
    return {"formatted": formatted}

# ── Conditional Edge — reads category, returns next node name ──────────────────
def route_to_specialist(state: CricketState) -> str:
    """
    This is the conditional edge function.
    Reads state, returns the name of the next node.
    LangGraph uses this return value to pick the edge.
    """
    return state["category"]   # "batting" | "bowling" | "general"

# ── Build the Graph ────────────────────────────────────────────────────────────
def build_graph():
    graph = StateGraph(CricketState)

    # Add all nodes
    graph.add_node("classifier", classifier_node)
    graph.add_node("batting",    batting_node)
    graph.add_node("bowling",    bowling_node)
    graph.add_node("general",    general_node)
    graph.add_node("formatter",  formatter_node)

    # Entry point — first node to run
    graph.set_entry_point("classifier")

    # Conditional edge — classifier → specialist based on category
    graph.add_conditional_edges(
        "classifier",           # from this node
        route_to_specialist,    # call this function to decide
        {
            "batting": "batting",   # if "batting" → go to batting node
            "bowling": "bowling",   # if "bowling" → go to bowling node
            "general": "general",   # if "general" → go to general node
        }
    )

    # Regular edges — specialist → formatter → END
    graph.add_edge("batting",  "formatter")
    graph.add_edge("bowling",  "formatter")
    graph.add_edge("general",  "formatter")
    graph.add_edge("formatter", END)

    # Compile — validates the graph, returns a runnable
    return graph.compile()


# ── Run the Demo ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = build_graph()

    print(app.get_graph().draw_mermaid())

    app.get_graph().draw_mermaid_png(output_file_path="graph.png")

    #test_questions = [
    #    "Who scored the most centuries in Test cricket?",
    #    "Who took the most wickets in ODIs?",
    #    "Which team won the most T20 World Cups?",
    #]

    #for question in test_questions:
    #    print("\n" + "=" * 60)
    #    initial_state = {
    #        "question": question,
    #        "category": None,
    #        "answer": None,
    #        "formatted": None
    #    }

    #    result = app.invoke(initial_state)
    #    print(f"\nFinal Answer:\n{result['formatted']}")
    #    print("=" * 60)