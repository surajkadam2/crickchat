# agent_types.py
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class AgentContext:
    """
    The baton passed between all agents.
    Every agent receives this and returns an updated version.

    Args:
        question:       Original user question
        history:        Conversation history for Gemini
        schema:         DB schema string
        question_type:  Classified by Router — "sql" | "rag" | "both"
        sql:            Generated SQL query
        rows:           DB query results
        web_results:    Retrieved web content from RAG Agent
        explanation:    Final answer from Synthesizer
        sources:        Which sources were used — ["db"] | ["web"] | ["db", "web"]
        error:          Any error that occurred
    """
    question: str
    history: list = field(default_factory=list)
    schema: str = ""
    question_type: Optional[str] = None
    sql: Optional[str] = None
    rows: list = field(default_factory=list)
    web_results: Optional[str] = None
    explanation: Optional[str] = None
    sources: list = field(default_factory=list)
    error: Optional[str] = None