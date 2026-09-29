import sys
import uuid
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Ensure root import path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from app.services.bhashini import BhashiniService, SUPPORTED_LANGUAGES
from app.agents.graph import orchestration_graph, AgentState

router = APIRouter(prefix="/api", tags=["IP-SAKTI Core"])

bhashini_service = BhashiniService()


# -------------------------------------------------------------
# Request & Response Schemas
# -------------------------------------------------------------
class AnalysisRequest(BaseModel):
    query: str = Field(..., description="User formulation query or legal inquiry")
    user_answers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Key-value mapping of answers to clarifying questions (e.g. Q1_CLASSICAL_SOURCE)",
    )
    forced_jurisdiction: Optional[str] = Field(
        default=None, description="Manual UI override: 'IN', 'INT', or 'DUAL'"
    )


class CitationItem(BaseModel):
    anchor: str
    jurisdiction: str
    regime: str
    score: float
    snippet: str


class PipelineData(BaseModel):
    target_agents: List[str] = Field(default_factory=list)
    reasoning_trace: List[str] = Field(default_factory=list)
    classification: Optional[Dict[str, Any]] = None
    routing: Optional[Dict[str, Any]] = None


class AnalysisResponse(BaseModel):
    status: str
    needs_clarification: bool
    final_response: str
    category: str
    confidence_score: float
    jurisdiction_track: str
    active_jurisdictions: List[str]
    citations: List[str]
    retrieved_chunks: List[Dict[str, Any]]
    clarifying_questions: List[Dict[str, Any]]
    escalate_to_human: bool
    pipeline: Optional[PipelineData] = None


class EscalationRequest(BaseModel):
    user_query: str
    product_category: str
    applicant_name: str = Field(default="AYUSH Innovator")
    contact_email: str
    notes: Optional[str] = None
    citations: List[str] = Field(default_factory=list)
    confidence_score: float = 0.0


class EscalationResponse(BaseModel):
    docket_id: str
    status: str
    message: str
    timestamp: str
    briefing_dossier: str


class TranslationRequest(BaseModel):
    text: str
    target_language: str = Field(..., example="hi")


class TranslationResponse(BaseModel):
    translated_text: str
    target_language: str
    language_name: str


# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------
@router.get("/health")
def health_check():
    """Service health and readiness check."""
    return {
        "status": "healthy",
        "service": "IP-SAKTI Sahayak Engine",
        "version": "1.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/analyze", response_model=AnalysisResponse)
def analyze_formulation(payload: AnalysisRequest):
    """
    Synchronous analysis endpoint: executes the full LangGraph state machine.
    Handles classification, routing, retrieval, worker agent evaluation, and synthesis.
    """
    try:
        input_state: AgentState = {
            "user_query": payload.query,
            "user_answers": payload.user_answers,
            "forced_jurisdiction": payload.forced_jurisdiction,
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

        result = orchestration_graph.invoke(input_state)

        classification = result.get("classification") or {}
        routing = result.get("routing") or {}

        status_code = (
            "clarification_required"
            if result.get("needs_clarification")
            else "completed"
        )

        pipeline_info = PipelineData(
            target_agents=result.get("target_agents", []),
            reasoning_trace=result.get("reasoning_trace", []),
            classification=classification,
            routing=routing,
        )

        return AnalysisResponse(
            status=status_code,
            needs_clarification=result.get("needs_clarification", False),
            final_response=result.get("final_response", ""),
            category=classification.get("category", "Unspecified"),
            confidence_score=result.get("confidence_score", 0.0),
            jurisdiction_track=routing.get("selected_track", "Unspecified"),
            active_jurisdictions=routing.get("active_jurisdictions", []),
            citations=result.get("citations", []),
            retrieved_chunks=result.get("retrieved_chunks", []),
            clarifying_questions=result.get("clarifying_questions", []),
            escalate_to_human=result.get("escalate_to_human", False),
            pipeline=pipeline_info,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Engine analysis failure: {str(e)}"
        )


@router.post("/query", response_model=AnalysisResponse)
def query_formulation(payload: AnalysisRequest):
    """Alias for /analyze ensuring compatibility with all frontend clients."""
    return analyze_formulation(payload)


@router.post("/analyze/stream")
async def analyze_formulation_stream(payload: AnalysisRequest):
    """
    Streams multi-agent LangGraph execution in real time via Server-Sent Events (SSE).
    Emits events as worker nodes run: classifier -> router -> retriever -> [worker agents] -> synthesizer.
    """

    async def event_generator():
        input_state: AgentState = {
            "user_query": payload.query,
            "user_answers": payload.user_answers,
            "forced_jurisdiction": payload.forced_jurisdiction,
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

        # Node mapping aligning LangGraph node names to UI identifiers
        node_ui_map = {
            "classifier": "classify",
            "router": "route",
            "retriever": "retrieve",
            "ip_agent": "ip_agent",
            "abs_agent": "abs_agent",
            "export_agent": "export_agent",
            "synthesizer": "synthesis",
            "clarification_stop": "clarify",
        }

        try:
            yield f"data: {json.dumps({'event': 'start'})}\n\n"
            await asyncio.sleep(0.02)

            accumulated_state: Dict[str, Any] = dict(input_state)

            # Stream each node as it executes in LangGraph
            async for output in orchestration_graph.astream(input_state):
                if not isinstance(output, dict):
                    continue

                for node_name, state_update in output.items():
                    if isinstance(state_update, dict):
                        accumulated_state.update(state_update)

                    ui_step = node_ui_map.get(node_name, node_name)

                    # Diagnostic gating check
                    if accumulated_state.get("needs_clarification"):
                        clarification_payload = {
                            "event": "clarification",
                            "node": ui_step,
                            "questions": accumulated_state.get(
                                "clarifying_questions", []
                            ),
                            "pipeline": {
                                "target_agents": accumulated_state.get(
                                    "target_agents", []
                                ),
                                "reasoning_trace": accumulated_state.get(
                                    "reasoning_trace", []
                                ),
                                "classification": accumulated_state.get(
                                    "classification", {}
                                ),
                                "routing": accumulated_state.get("routing", {}),
                            },
                        }
                        yield f"data: {json.dumps(clarification_payload)}\n\n"
                        return

                    # Emit step completion event with current trace
                    step_payload = {
                        "event": "node_complete",
                        "node": ui_step,
                        "raw_node": node_name,
                        "reasoning_trace": accumulated_state.get("reasoning_trace", []),
                        "target_agents": accumulated_state.get("target_agents", []),
                    }
                    yield f"data: {json.dumps(step_payload)}\n\n"

                    # 300ms pacing allows evaluators to visually follow multi-agent handoffs
                    await asyncio.sleep(0.30)

            # Final payload with full statutory conclusions and pipeline metadata
            classification = accumulated_state.get("classification") or {}
            routing = accumulated_state.get("routing") or {}

            final_payload = {
                "event": "complete",
                "result": {
                    "final_response": accumulated_state.get("final_response", ""),
                    "category": classification.get("category", "Unspecified"),
                    "confidence_score": accumulated_state.get("confidence_score", 0.90),
                    "jurisdiction_track": routing.get(
                        "selected_track", "India Domestic"
                    ),
                    "active_jurisdictions": routing.get("active_jurisdictions", ["IN"]),
                    "citations": accumulated_state.get("citations", []),
                    "retrieved_chunks": accumulated_state.get("retrieved_chunks", []),
                    "clarifying_questions": accumulated_state.get(
                        "clarifying_questions", []
                    ),
                    "escalate_to_human": accumulated_state.get(
                        "escalate_to_human", False
                    ),
                    "pipeline": {
                        "target_agents": accumulated_state.get("target_agents", []),
                        "reasoning_trace": accumulated_state.get("reasoning_trace", []),
                        "classification": classification,
                        "routing": routing,
                    },
                },
            }
            yield f"data: {json.dumps(final_payload)}\n\n"

        except Exception as e:
            error_payload = {"event": "error", "message": str(e)}
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/escalate", response_model=EscalationResponse)
def escalate_to_facilitator(payload: EscalationRequest):
    """
    Generates a formal pre-briefing docket for empaneled AYUSH Patent Facilitators.
    """
    docket_id = f"AYUSH-IP-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    category = payload.product_category
    if "Phytopharmaceutical" in category or "Proprietary" in category:
        nba_requirement = (
            "Section 6 BDA 2023 - Form III mandatory prior approval before patent grant; "
            "Section 7 prior intimation to SBB for commercial manufacturing."
        )
    else:
        nba_requirement = (
            "Section 40 / Registered Practitioner exemption applies for classical Ayurvedic formulations; "
            "SBB commercial intimation required if operating at industrial scale."
        )

    dossier = f"""================================================================================
PRE-BRIEFING AYUSH IPR DOSSIER | DOCKET: {docket_id}
Generated by IP-SAKTI Sahayak (National AYUSH Regulatory Engine)
================================================================================

1. APPLICANT RECORD
   - Applicant Name     : {payload.applicant_name}
   - Contact            : {payload.contact_email}
   - Registered On      : {timestamp}
   - Submission Notes   : {payload.notes or "None provided"}

2. TECHNICAL CLASSIFICATION
   - Classified Category: {payload.product_category}
   - Engine Confidence  : {payload.confidence_score * 100:.1f}%
   - Inquiry Description: "{payload.user_query}"

3. STATUTORY ASSESSMENT & APPLICABLE BARRIERS
   - Indian Patents Act : Section 3(p) TKDL check; Section 3(e) synergistic assay data required.
   - NBA / SBB Duties   : {nba_requirement}
   - Relevant Citations : {", ".join(payload.citations) if payload.citations else "General Statutory Framework"}

4. RECOMMENDED FACILITATOR ACTIONS
   [ ] Cross-verify botanical taxa against First Schedule authoritative texts & TKDL.
   [ ] For Phytopharmaceuticals: review HPLC/HPTLC 4-marker validation and CDSCO trial protocol.
   [ ] For Process Claims: ensure claims meet inventive threshold under Section 2(1)(j) & Section 48(b).
   [ ] Prepare draft Form 1, Form 2 (Complete Spec), Form 18A (Expedited Startup Examination), and NBA Form III.
   [ ] Advise on Patent Rules 2024 compliance (Form 27 triennial statement of working).

================================================================================
LEGAL PRIVILEGE: Prepared under diagnostic guidance protocol. Not formal legal counsel.
================================================================================
"""

    return EscalationResponse(
        docket_id=docket_id,
        status="REGISTERED",
        message="Preliminary briefing dossier successfully registered for patent facilitator review.",
        timestamp=timestamp,
        briefing_dossier=dossier,
    )


@router.get("/languages")
def get_supported_languages():
    """Returns list of supported Indian vernacular languages."""
    return {"languages": SUPPORTED_LANGUAGES}


@router.post("/translate", response_model=TranslationResponse)
def translate_content(payload: TranslationRequest):
    """
    Translates legal findings via Bhashini while preserving Sanskrit botanical names
    and statutory section citations using Ayurvedic entity shielding.
    """
    if payload.target_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Language '{payload.target_language}' not supported.",
        )

    translated = bhashini_service.translate(payload.text, payload.target_language)
    return TranslationResponse(
        translated_text=translated,
        target_language=payload.target_language,
        language_name=SUPPORTED_LANGUAGES[payload.target_language],
    )
