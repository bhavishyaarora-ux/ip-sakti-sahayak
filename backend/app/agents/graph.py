import sys
import os
import re
from pathlib import Path
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from app.rag.verifier import DPDPGuard

# Path resolution
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from app.agents.classifier import (
    FormulationClassifier,
    ClassificationResult,
    ClarifyingQuestion,
)
from app.agents.router import JurisdictionRouter, RoutingDecision
from app.rag.retriever import StatutoryRetriever
dpdp_guard = DPDPGuard()
vector_retriever = StatutoryRetriever()

STATUTORY_WATERMARK = (
    "> **Statutory Notice:** Information provided for educational and diagnostic "
    "routing purposes only. Does not constitute legal advice under the Advocates Act, 1961.\n\n"
)

# -------------------------------------------------------------
# 1. State Definition
# -------------------------------------------------------------
class AgentState(TypedDict):
    user_query: str
    user_answers: Optional[Dict[str, str]]
    forced_jurisdiction: Optional[str]
    classification: Optional[Dict[str, Any]]
    routing: Optional[Dict[str, Any]]
    retrieved_chunks: List[Dict[str, Any]]
    final_response: str
    citations: List[str]
    confidence_score: float
    escalate_to_human: bool
    needs_clarification: bool
    clarifying_questions: List[Dict[str, Any]]


# -------------------------------------------------------------
# 2. Graph Nodes
# -------------------------------------------------------------
classifier_engine = FormulationClassifier()
router_engine = JurisdictionRouter()


def classification_node(state: AgentState) -> Dict[str, Any]:
    """Sanitizes sensitive data and triages product classification."""
    raw_query = state["user_query"]
    sanitized_query, _ = dpdp_guard.sanitize(raw_query)

    answers = state.get("user_answers") or {}
    result: ClassificationResult = classifier_engine.classify(sanitized_query, answers)

    return {
        "user_query": sanitized_query,
        "classification": result.model_dump(),
        "needs_clarification": not result.is_definitive,
        "clarifying_questions": [q.model_dump() for q in result.clarifying_questions],
    }


def routing_node(state: AgentState) -> Dict[str, Any]:
    """Determines regulatory track based on user query and toggle override."""
    forced = state.get("forced_jurisdiction")

    # Normalize frontend values to canonical corpus filters ('IN', 'INT', 'DUAL')
    if forced in ["CROSS_BORDER", "INT", "INTERNATIONAL"]:
        selected_track = "International"
        target_filter = "INT"
    elif forced in ["INDIA", "IN", "DOMESTIC"]:
        selected_track = "India Domestic"
        target_filter = "IN"
    else:
        selected_track = "Dual Split View"
        target_filter = "DUAL"

    return {
        "routing": {"selected_track": selected_track, "target_filter": target_filter}
    }


def retrieval_node(state: AgentState) -> Dict[str, Any]:
    """Retrieves relevant statutory provisions with jurisdiction-aware enrichment."""
    user_query = state["user_query"]
    classification = state.get("classification", {})
    category = classification.get("category", "")
    routing = state.get("routing", {}) or {}
    target_filter = routing.get("target_filter", "IN")

    enriched_query = f"{user_query} {category}"

    # Enrich conditionally based on active jurisdiction filter
    if target_filter == "INT":
        enriched_query += " WIPO GRATK Treaty US FDA Botanical Guidance Nagoya Protocol ABS country of origin"
    elif target_filter == "IN":
        if "Phytopharmaceutical" in category:
            enriched_query += " CDSCO Rule 122E NBA Form III Section 3(d)"
        elif "Classical" in category:
            enriched_query += " Section 3(p) TKDL Section 40 BDA"
    else:  # DUAL
        enriched_query += (
            " Section 3(p) CDSCO NBA Form III WIPO GRATK Treaty US FDA Botanical"
        )

    # Query Qdrant
    chunks = vector_retriever.retrieve(
        query=enriched_query,
        jurisdiction=target_filter if target_filter != "DUAL" else None,
        top_k=4,
    )
    return {"retrieved_chunks": chunks}


def response_synthesis_node(state: AgentState) -> Dict[str, Any]:
    """Synthesizes legal findings prepended with the mandatory statutory watermark."""
    classification = state.get("classification", {})
    routing = state.get("routing", {}) or {}
    chunks = state.get("retrieved_chunks", [])

    category = classification.get("category", "General")
    ip_posture = classification.get("ip_posture", "")
    abs_mandate = classification.get("abs_mandate", "")
    target_filter = routing.get("target_filter", "IN")

    citations = [c["citation_anchor"] for c in chunks if "citation_anchor" in c]
    unique_citations = list(dict.fromkeys(citations))

    base_conf = classification.get("confidence", 0.70)
    retrieval_bonus = 0.15 if chunks else -0.20
    confidence_score = round(min(0.99, max(0.20, base_conf + retrieval_bonus)), 2)
    escalate_to_human = (confidence_score < 0.80) or (
        "Phytopharmaceutical" in str(category)
    )

    category_str = (
        str(category).replace("FormulationCategory.", "").replace("_", " ").title()
    )
    track_str = "Cross-Border / Export" if target_filter == "INT" else "India Domestic"

    # Prepend statutory watermark and core posture
    response_lines = [
        STATUTORY_WATERMARK,
        f"**Product Classification:** {category_str}",
        f"**Jurisdiction Track:** {track_str}\n",
        "**Core Legal & Regulatory Posture:**",
        f"* **IP & Patentability:** {ip_posture}",
        f"* **Access & Benefit-Sharing (ABS):** {abs_mandate}\n",
        "**Statutory References & Grounded Rules (India):**",
    ]

    # 1. Domestic (IN) Chunks Only: prevents international chunks from bleeding into the national track
    domestic_chunks = [c for c in chunks if c.get("jurisdiction") == "IN"]
    if domestic_chunks:
        for chunk in domestic_chunks:
            anchor = chunk.get("citation_anchor", "Statutory Provision")
            snippet = (
                chunk.get("content", "").split("Statutory Text & Rules:")[-1].strip()
            )
            first_sentence = (
                snippet.split("\n")[0] if snippet else chunk.get("content", "").strip()
            )
            response_lines.append(f"* `[{anchor}]`: {first_sentence}")
    else:
        response_lines.append(
            "* *No direct domestic statutory exclusion or precedent chunk passed retrieval threshold.*"
        )

    # 2. International Track: inserted only when Cross-Border is active
    if target_filter in ["INT", "DUAL"]:
        response_lines.append("\n**Target Export Regime Identified:**")

        int_chunks = [c for c in chunks if c.get("jurisdiction") == "INT"]
        for chunk in int_chunks:
            anchor = chunk.get("citation_anchor", "Treaty Provision")
            snippet = (
                chunk.get("content", "").split("Statutory Text & Rules:")[-1].strip()
            )
            first_sentence = (
                snippet.split("\n")[0] if snippet else chunk.get("content", "").strip()
            )
            response_lines.append(f"* `[{anchor}]`: {first_sentence}")

        response_lines.append(
            "* **WIPO GRATK Treaty (2024):** Mandatory disclosure of Indian genetic resources and traditional knowledge origins in patent applications."
        )
        response_lines.append(
            "* **US FDA Botanical Drug Guidance:** Early clinical safety reliance permitted for codified traditional use; Phase 1/2 clinical trial exemptions may apply."
        )
        response_lines.append(
            "* **Nagoya Protocol & ABS:** Prior Informed Consent (PIC) and Mutually Agreed Terms (MAT) required for foreign commercial exploitation."
        )

        if routing.get("target_export_markets"):
            markets_str = ", ".join(routing["target_export_markets"])
            response_lines.append(f"\n*Export Destinations:* {markets_str}")
            if "United States (US FDA)" in markets_str:
                response_lines.append(
                    "* *US FDA Pathway Note:* Botanical Drug Development guidance permits historical clinical use in India to support early IND phases; dietary supplements cannot carry medical claims."
                )

    # 3. Empaneled AYUSH IP Facilitator escalation notice
    if escalate_to_human:
        response_lines.append(
            "\n> **Recommendation:** Escalation to an empaneled AYUSH IP Facilitator (TISC / Patent Agent) recommended for formal claim drafting and NBA Form III filing."
        )

    final_text = "\n".join(response_lines)

    return {
        "final_response": final_text,
        "citations": unique_citations,
        "confidence_score": confidence_score,
        "escalate_to_human": escalate_to_human,
    }


# -------------------------------------------------------------
# 3. Conditional Routing Logic
# -------------------------------------------------------------
def clarification_router(state: AgentState) -> str:
    """If classification is uncertain and no answers were provided, branch to clarify."""
    if state["needs_clarification"]:
        return "clarification_needed"
    return "proceed_to_routing"


def clarification_stop_node(state: AgentState) -> Dict[str, Any]:
    """Generates user-facing diagnostic questions when the query is ambiguous."""
    questions = state.get("clarifying_questions", [])
    output = [
        "**Formulation Diagnostic Gate:** Your query requires regulatory classification before proceeding to legal retrieval.\n",
        "Please answer the following clarifying questions:\n",
    ]
    for idx, q in enumerate(questions, 1):
        output.append(f"**{idx}. {q['question']}**")
        for opt in q["options"]:
            output.append(f"   - [ ] {opt}")
        output.append(f"   *Legal Rationale: {q['legal_rationale']}*\n")

    output.append("---")
    output.append(
        "*Provide these details to map your formulation to the correct IP regime (Classical, P&P, Phytopharmaceutical, or Ayurveda-Aahar).*"
    )

    return {
        "final_response": "\n".join(output),
        "citations": [],
        "confidence_score": 0.40,
        "escalate_to_human": False,
    }


# -------------------------------------------------------------
# 4. StateGraph Assembly
# -------------------------------------------------------------
builder = StateGraph(AgentState)

builder.add_node("classifier", classification_node)
builder.add_node("clarification_stop", clarification_stop_node)
builder.add_node("router", routing_node)
builder.add_node("retriever", retrieval_node)
builder.add_node("synthesizer", response_synthesis_node)

builder.set_entry_point("classifier")

builder.add_conditional_edges(
    "classifier",
    clarification_router,
    {"clarification_needed": "clarification_stop", "proceed_to_routing": "router"},
)

builder.add_edge("clarification_stop", END)
builder.add_edge("router", "retriever")
builder.add_edge("retriever", "synthesizer")
builder.add_edge("synthesizer", END)

orchestration_graph = builder.compile()

# -------------------------------------------------------------
# Module Self-Test
# -------------------------------------------------------------
if __name__ == "__main__":
    print("Executing LangGraph Orchestration Engine Verification...\n")

    # Test Run 1: Ambiguous Query (Hits Clarification Branch)
    input_state_1: AgentState = {
        "user_query": "I made an herbal oil for headache",
        "user_answers": None,
        "forced_jurisdiction": None,
        "classification": None,
        "routing": None,
        "retrieved_chunks": [],
        "final_response": "",
        "citations": [],
        "confidence_score": 0.0,
        "escalate_to_human": False,
        "needs_clarification": False,
        "clarifying_questions": [],
    }

    print("=== TEST 1: Ambiguous Query -> Diagnostic Gate ===")
    res_1 = orchestration_graph.invoke(input_state_1)
    print(res_1["final_response"])
    print("\n" + "=" * 60 + "\n")

    # Test Run 2: Complete Query (Proceeds through Router, Vector Retrieval & Synthesis)
    input_state_2: AgentState = {
        "user_query": "Can I patent a classical Churna from Charaka Samhita and export to USA?",
        "user_answers": {"Q1_CLASSICAL_SOURCE": "Yes, identical classical recipe"},
        "forced_jurisdiction": None,
        "classification": None,
        "routing": None,
        "retrieved_chunks": [],
        "final_response": "",
        "citations": [],
        "confidence_score": 0.0,
        "escalate_to_human": False,
        "needs_clarification": False,
        "clarifying_questions": [],
    }

    print("=== TEST 2: Dual Cross-Border Query -> End-to-End Execution ===")
    res_2 = orchestration_graph.invoke(input_state_2)
    print(res_2["final_response"])
    print(f"\nExtracted Citations: {res_2['citations']}")
    print(
        f"Confidence: {res_2['confidence_score']} | Escalate: {res_2['escalate_to_human']}"
    )
