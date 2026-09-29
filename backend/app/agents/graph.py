import sys
import os
import re
from pathlib import Path
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END

# Path resolution
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from app.rag.verifier import DPDPGuard
from app.rag.retriever import StatutoryRetriever
from app.agents.classifier import (
    FormulationClassifier,
    ClassificationResult,
    ClarifyingQuestion,
)
from app.agents.router import JurisdictionRouter, RoutingDecision

# Modular sub-agent imports with graceful fallback
try:
    from app.agents.ip_agent import evaluate_ip_regime
except ImportError:
    evaluate_ip_regime = None

try:
    from app.agents.abs_agent import evaluate_abs_compliance
except ImportError:
    evaluate_abs_compliance = None

try:
    from app.agents.export_agent import evaluate_export_regime
except ImportError:
    evaluate_export_regime = None

dpdp_guard = DPDPGuard()
vector_retriever = StatutoryRetriever()
classifier_engine = FormulationClassifier()
router_engine = JurisdictionRouter()

STATUTORY_WATERMARK = (
    "> **Statutory Notice:** Information provided for educational and diagnostic "
    "routing purposes only. Does not constitute formal legal advice under the Advocates Act, 1961.\n\n"
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
    target_agents: List[str]
    agent_outputs: Dict[str, Any]
    reasoning_trace: List[str]
    retrieved_chunks: List[Dict[str, Any]]
    final_response: str
    citations: List[str]
    confidence_score: float
    escalate_to_human: bool
    needs_clarification: bool
    clarifying_questions: List[Dict[str, Any]]


# -------------------------------------------------------------
# 2. Upstream Nodes: Classification & Routing
# -------------------------------------------------------------
def classification_node(state: AgentState) -> Dict[str, Any]:
    """Sanitizes sensitive data and triages product classification."""
    raw_query = state.get("user_query", "")
    sanitized_query, _ = dpdp_guard.sanitize(raw_query)

    answers = state.get("user_answers") or {}
    result: ClassificationResult = classifier_engine.classify(sanitized_query, answers)

    trace = state.get("reasoning_trace") or []
    cat_name = (
        str(result.category)
        .replace("FormulationCategory.", "")
        .replace("_", " ")
        .title()
    )
    trace.append(
        f"Classifier Agent: Identified category as '{cat_name}' (Definitive: {result.is_definitive})."
    )

    return {
        "user_query": sanitized_query,
        "classification": result.model_dump(),
        "needs_clarification": not result.is_definitive,
        "clarifying_questions": [q.model_dump() for q in result.clarifying_questions],
        "reasoning_trace": trace,
        "agent_outputs": state.get("agent_outputs") or {},
        "target_agents": state.get("target_agents") or [],
    }


def routing_node(state: AgentState) -> Dict[str, Any]:
    """Determines jurisdictional track and dispatches required sub-agents."""
    forced = state.get("forced_jurisdiction")
    user_query = state["user_query"]

    # Use the upgraded JurisdictionRouter for statutory awareness and sub-agent dispatching
    decision: RoutingDecision = router_engine.route(user_query, forced_override=forced)

    # Map active jurisdictions to vector DB filter tag ('IN', 'INT', 'DUAL')
    active_jur = decision.active_jurisdictions
    if len(active_jur) > 1 or "DUAL" in str(decision.selected_track.value).upper():
        target_filter = "DUAL"
    elif "INT" in active_jur:
        target_filter = "INT"
    else:
        target_filter = "IN"

    routing_data = decision.model_dump()
    routing_data["target_filter"] = target_filter

    trace = state.get("reasoning_trace") or []
    trace.append(
        f"Jurisdiction Router: Track set to '{decision.selected_track.value}'. "
        f"Dispatched worker agents: {decision.target_agents}."
    )

    return {
        "routing": routing_data,
        "target_agents": decision.target_agents,
        "reasoning_trace": trace,
    }


def retrieval_node(state: AgentState) -> Dict[str, Any]:
    """Retrieves relevant statutory provisions with jurisdiction-aware enrichment."""
    user_query = state["user_query"]
    classification = state.get("classification") or {}
    category = classification.get("category", "")
    routing = state.get("routing") or {}
    target_filter = routing.get("target_filter", "IN")

    enriched_query = f"{user_query} {category}"

    # Enrich conditionally based on active jurisdiction filter
    if target_filter == "INT":
        enriched_query += " WIPO GRATK Treaty US FDA Botanical Guidance Nagoya Protocol ABS country of origin"
    elif target_filter == "IN":
        if "Phytopharmaceutical" in str(category):
            enriched_query += (
                " CDSCO Rule 122E NBA Form III Section 3(d) bioactive markers"
            )
        elif "Classical" in str(category):
            enriched_query += " Section 3(p) TKDL Section 40 BDA First Schedule"
        else:
            enriched_query += " Patents Act Section 3(e) Section 2(1)(j) SBB intimation"
    else:  # DUAL
        enriched_query += (
            " Section 3(p) Section 3(e) NBA Form III WIPO GRATK Treaty US FDA Botanical"
        )

    # Query vector database
    chunks = vector_retriever.retrieve(
        query=enriched_query,
        jurisdiction=target_filter if target_filter != "DUAL" else None,
        top_k=4,
    )

    trace = state.get("reasoning_trace") or []
    trace.append(
        f"Statutory Retriever: Fetched {len(chunks)} verified clauses from corpus."
    )

    return {"retrieved_chunks": chunks, "reasoning_trace": trace}


# -------------------------------------------------------------
# 3. Specialized Worker Agent Nodes
# -------------------------------------------------------------
def ip_agent_node(state: AgentState) -> Dict[str, Any]:
    """Specialist sub-agent for Indian Patents Act, Trademarks, GI, and Design rights."""
    target_agents = state.get("target_agents", [])
    if "ip_agent" not in target_agents:
        return state

    trace = state.get("reasoning_trace") or []
    outputs = state.get("agent_outputs") or {}
    classification = state.get("classification") or {}
    category = str(classification.get("category", ""))

    # If external standalone module is implemented, delegate to it
    if evaluate_ip_regime:
        ip_findings = evaluate_ip_regime(state)
    else:
        # In-graph domain evaluation
        findings = []
        if "Classical" in category:
            findings.append(
                "* **Product Patent:** **BARRED under Section 3(p) of the Patents Act, 1970** "
                "(Traditional Knowledge exclusion). Classical formulations documented in First Schedule texts are protected in the TKDL."
            )
            findings.append(
                "* **Recommended Protection:** File for **Trademark (Form TM-A)** for your brand/name "
                "under Nice Class 5, and leverage **Geographical Indications (GI)** if rooted in a specific region."
            )
        elif "Phytopharmaceutical" in category:
            findings.append(
                "* **Product & Process Patent:** **POTENTIALLY ELIGIBLE**. High patent eligibility for novel, "
                "purified bioactive fractions under Section 2(1)(j). Must substantiate enhanced therapeutic efficacy under Section 3(d)."
            )
            findings.append(
                "* **Regulatory Requirement:** Requires minimum 4 validated bioactive markers and clinical safety clearance under New Drugs Rules, 2019."
            )
        elif "Ayurveda_Aahar" in category:
            findings.append(
                "* **Patent Eligibility:** **EXCLUDED for medical claims**. Cannot claim medicinal properties under FSSAI Ayurveda Aahara Regulations, 2022."
            )
            findings.append(
                "* **Recommended Protection:** Safeguard proprietary preparation recipes as **Trade Secrets**, "
                "register brand Trademarks under Nice Class 30, and protect packaging via **Industrial Designs**."
            )
        else:  # Patent & Proprietary / Cosmetics
            findings.append(
                "* **Formulation Patent:** Subject to strict **Section 3(e) scrutiny** (mere admixtures). "
                "You must establish non-obvious synergistic therapeutic efficacy with experimental data."
            )
            findings.append(
                "* **Process Patent:** Novel, inventive extraction parameters or delivery systems are **ELIGIBLE** "
                "under Section 2(1)(j) & Section 48(b)."
            )
            findings.append(
                "* **Branding:** File Trademark Form TM-A under Class 5 (Medicines) or Class 3 (Cosmetics)."
            )

        ip_findings = "\n".join(findings)

    outputs["ip_agent"] = ip_findings
    trace.append(
        "IP Specialist Agent: Evaluated patentability bars (Sec 3p/3e/3d) and trademark posture."
    )

    return {"agent_outputs": outputs, "reasoning_trace": trace}


def abs_agent_node(state: AgentState) -> Dict[str, Any]:
    """Specialist sub-agent for Biological Diversity Act 2023 & NBA/SBB duties."""
    target_agents = state.get("target_agents", [])
    if "abs_agent" not in target_agents:
        return state

    trace = state.get("reasoning_trace") or []
    outputs = state.get("agent_outputs") or {}
    classification = state.get("classification") or {}
    category = str(classification.get("category", ""))

    if evaluate_abs_compliance:
        abs_findings = evaluate_abs_compliance(state)
    else:
        findings = [
            "* **IPR Grant Requirement (Section 6, BDA 2023):** Prior approval of the **National Biodiversity "
            "Authority (NBA) via Form III** is mandatory before obtaining any patent for inventions based on Indian biological resources.",
            "* **Commercial Manufacturing (Section 7, BDA 2023):** Commercial operations using Indian biological resources "
            "require prior intimation to the respective **State Biodiversity Board (SBB)**.",
            "* **2023 Amendment Exemptions:** Registered AYUSH practitioners and codified traditional knowledge for personal "
            "clinical practice are exempt from commercial benefit-sharing levies.",
        ]
        abs_findings = "\n".join(findings)

    outputs["abs_agent"] = abs_findings
    trace.append(
        "ABS Specialist Agent: Evaluated Biological Diversity Act 2023 (Section 6 NBA & Section 7 SBB)."
    )

    return {"agent_outputs": outputs, "reasoning_trace": trace}


def export_agent_node(state: AgentState) -> Dict[str, Any]:
    """Specialist sub-agent for WIPO GRATK Treaty (2024), Nagoya Protocol, and US FDA/EMA."""
    target_agents = state.get("target_agents", [])
    if "export_agent" not in target_agents:
        return state

    trace = state.get("reasoning_trace") or []
    outputs = state.get("agent_outputs") or {}
    routing = state.get("routing") or {}

    if evaluate_export_regime:
        export_findings = evaluate_export_regime(state)
    else:
        findings = [
            "* **WIPO GRATK Treaty (2024) - Article 3:** Mandatory disclosure in foreign patent applications "
            "specifying the country of origin for genetic resources and indigenous traditional knowledge.",
            "* **Nagoya Protocol on ABS:** Obligation to obtain Prior Informed Consent (PIC) and establish Mutually "
            "Agreed Terms (MAT) prior to commercial exploitation in signatory nations.",
            "* **US FDA Botanical Drug Guidance:** Provides flexibility for formulations with established human use in India; "
            "Phase 1 clinical trial safety may rely on documented Ayurvedic pharmacopoeial history.",
            "* **EU THMPD (Directive 2004/24/EC):** Traditional Herbal Medicinal Products pathway requires proof of 30 years "
            "of medicinal use (including at least 15 years within the EU).",
        ]
        markets = routing.get("target_export_markets", [])
        if markets:
            findings.append(f"* **Target Regional Focus:** {', '.join(markets)}")

        export_findings = "\n".join(findings)

    outputs["export_agent"] = export_findings
    trace.append(
        "Export Specialist Agent: Evaluated WIPO GRATK (2024) mandatory disclosure and FDA/EMA entry."
    )

    return {"agent_outputs": outputs, "reasoning_trace": trace}


# -------------------------------------------------------------
# 4. Response Synthesis & Verification Node
# -------------------------------------------------------------
def response_synthesis_node(state: AgentState) -> Dict[str, Any]:
    """Synthesizes legal findings from all worker agents into a structured, citation-grounded response."""
    classification = state.get("classification") or {}
    routing = state.get("routing") or {}
    chunks = state.get("retrieved_chunks") or []
    agent_outputs = state.get("agent_outputs") or {}
    trace = state.get("reasoning_trace") or []

    category = classification.get("category", "General")
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
    track_str = routing.get("selected_track", "India Domestic")

    # Build response sections
    response_lines = [
        STATUTORY_WATERMARK,
        f"**Product Classification:** {category_str}",
        f"**Jurisdiction Track:** {track_str}\n",
    ]

    # 1. IP Strategy Section
    if "ip_agent" in agent_outputs:
        response_lines.append("### 1. Intellectual Property & Patent Assessment")
        response_lines.append(agent_outputs["ip_agent"] + "\n")

    # 2. ABS / Biodiversity Section
    if "abs_agent" in agent_outputs:
        response_lines.append(
            "### 2. Biological Diversity & Access and Benefit-Sharing (ABS)"
        )
        response_lines.append(agent_outputs["abs_agent"] + "\n")

    # 3. International & Cross-Border Section
    if "export_agent" in agent_outputs or target_filter in ["INT", "DUAL"]:
        response_lines.append("### 3. Cross-Border & International Regimes")
        if "export_agent" in agent_outputs:
            response_lines.append(agent_outputs["export_agent"] + "\n")
        else:
            response_lines.append(
                "* **WIPO GRATK Treaty (2024):** Mandatory disclosure of origin for Indian genetic resources.\n"
            )

    # 4. Verified Statutory Citations
    response_lines.append("### 4. Verified Grounded Citations")
    if chunks:
        for chunk in chunks:
            anchor = chunk.get("citation_anchor", "Statutory Clause")
            snippet = (
                chunk.get("content", "").split("Statutory Text & Rules:")[-1].strip()
            )
            first_sentence = (
                snippet.split("\n")[0] if snippet else chunk.get("content", "").strip()
            )
            response_lines.append(f"* `[{anchor}]`: {first_sentence}")
    else:
        response_lines.append(
            "* *No direct statutory chunks passed the similarity threshold.*"
        )

    # 5. Escalation Recommendation
    if escalate_to_human:
        response_lines.append(
            "\n> **Recommendation:** Escalation to an empaneled AYUSH IP Facilitator (TISC / Registered Patent Agent) "
            "recommended for formal claim drafting and NBA Form III submission."
        )

    trace.append(
        f"Synthesizer: Formulated source-grounded response with {len(unique_citations)} citations."
    )

    return {
        "final_response": "\n".join(response_lines),
        "citations": unique_citations,
        "confidence_score": confidence_score,
        "escalate_to_human": escalate_to_human,
        "reasoning_trace": trace,
    }


# -------------------------------------------------------------
# 5. Conditional Branching & Diagnostic Stop
# -------------------------------------------------------------
def clarification_router(state: AgentState) -> str:
    """If classification is ambiguous and no user answers exist, branch to diagnostic stop."""
    if state.get("needs_clarification", False):
        return "clarification_needed"
    return "proceed_to_routing"


def clarification_stop_node(state: AgentState) -> Dict[str, Any]:
    """Generates user-facing diagnostic questions when the query is ambiguous."""
    questions = state.get("clarifying_questions", [])
    output = [
        "**Formulation Diagnostic Gate:** Your query requires regulatory classification before proceeding to legal retrieval.\n",
        "Please clarify the following details:\n",
    ]
    for idx, q in enumerate(questions, 1):
        output.append(f"**{idx}. {q['question']}**")
        for opt in q.get("options", []):
            output.append(f"   - [ ] {opt}")
        output.append(f"   *Legal Rationale: {q.get('legal_rationale', '')}*\n")

    output.append("---")
    output.append(
        "*Select options to map your formulation to the correct IP regime (Classical, P&P, Phytopharmaceutical, or Ayurveda-Aahar).*"
    )

    trace = state.get("reasoning_trace") or []
    trace.append(
        "Diagnostic Gate: Paused execution awaiting user clarification on formulation."
    )

    return {
        "final_response": "\n".join(output),
        "citations": [],
        "confidence_score": 0.40,
        "escalate_to_human": False,
        "reasoning_trace": trace,
    }


# -------------------------------------------------------------
# 6. LangGraph StateGraph Assembly
# -------------------------------------------------------------
builder = StateGraph(AgentState)

# 1. Register all nodes
builder.add_node("classifier", classification_node)
builder.add_node("clarification_stop", clarification_stop_node)
builder.add_node("router", routing_node)
builder.add_node("retriever", retrieval_node)
builder.add_node("ip_agent", ip_agent_node)
builder.add_node("abs_agent", abs_agent_node)
builder.add_node("export_agent", export_agent_node)
builder.add_node("synthesizer", response_synthesis_node)

# 2. Build graph topology
builder.set_entry_point("classifier")

builder.add_conditional_edges(
    "classifier",
    clarification_router,
    {"clarification_needed": "clarification_stop", "proceed_to_routing": "router"},
)

builder.add_edge("clarification_stop", END)
builder.add_edge("router", "retriever")

# Sequential agent pipeline: each sub-agent dynamically inspects state['target_agents']
builder.add_edge("retriever", "ip_agent")
builder.add_edge("ip_agent", "abs_agent")
builder.add_edge("abs_agent", "export_agent")
builder.add_edge("export_agent", "synthesizer")
builder.add_edge("synthesizer", END)

orchestration_graph = builder.compile()


# -------------------------------------------------------------
# Module Self-Test
# -------------------------------------------------------------
if __name__ == "__main__":
    print("Executing Multi-Agent LangGraph Orchestration Engine Verification...\n")

    # Test Run 1: Ambiguous Query (Hits Clarification Diagnostic Gate)
    input_state_1: AgentState = {
        "user_query": "I made an herbal oil for headache",
        "user_answers": None,
        "forced_jurisdiction": None,
        "classification": None,
        "routing": None,
        "target_agents": [],
        "agent_outputs": {},
        "reasoning_trace": [],
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

    # Test Run 2: Multi-Domain Dual Query (Exercises IP + ABS + Export Agents)
    input_state_2: AgentState = {
        "user_query": "Can I patent an Ashwagandha root extract for joint pain, export to the US, and what permissions do I need from the Biodiversity Board?",
        "user_answers": {
            "Q1_CLASSICAL_SOURCE": "Novel extraction method from classical herb"
        },
        "forced_jurisdiction": "DUAL",
        "classification": None,
        "routing": None,
        "target_agents": [],
        "agent_outputs": {},
        "reasoning_trace": [],
        "retrieved_chunks": [],
        "final_response": "",
        "citations": [],
        "confidence_score": 0.0,
        "escalate_to_human": False,
        "needs_clarification": False,
        "clarifying_questions": [],
    }

    print("=== TEST 2: Dual Cross-Border Query -> Multi-Agent Execution ===")
    res_2 = orchestration_graph.invoke(input_state_2)
    print(res_2["final_response"])
    print("\nReasoning Trace Log:")
    for step in res_2["reasoning_trace"]:
        print(f" -> {step}")
    print(f"\nExtracted Citations: {res_2['citations']}")
    print(
        f"Confidence: {res_2['confidence_score']} | Escalate: {res_2['escalate_to_human']}"
    )
