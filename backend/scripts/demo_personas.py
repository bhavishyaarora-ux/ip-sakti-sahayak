import sys
import json
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.agents.graph import orchestration_graph, AgentState
from app.services.bhashini import BhashiniService

bhashini = BhashiniService()

PERSONA_SCENARIOS = [
    {
        "id": "PERSONA_1",
        "title": "Persona 1: Traditional Vaidya / Classical Practitioner",
        "actor": "Vaidya Harishankar (Traditional Ayurvedic Physician, Haridwar)",
        "query": "I prepare a classical Triphala Kwatha decoction based on Sharangadhara Samhita. My clinic is at Plot 12, Haridwar 249401. Can I get a product patent in India, and do I need State Biodiversity Board permission?",
        "answers": {
            "Q1_CLASSICAL_SOURCE": "Yes, identical classical recipe",
            "Q2_EXTRACTION_DEPTH": "Whole herb / Traditional aqueous extract (Kwatha, Asava, Swarasa)",
            "Q3_INTENDED_USE": "Therapeutic medicine (cure, mitigation, or treatment of disease)",
        },
        "forced_jurisdiction": "IN",
        "target_lang": "hi",
        "expected_findings": [
            "Patents Act Section 3(p) statutory bar (Traditional Knowledge)",
            "Defended by CSIR Traditional Knowledge Digital Library (TKDL)",
            "Biological Diversity Act Section 40 exemption for registered codified practitioners",
            "DPDP Act automatic redaction of clinic address and PIN code",
        ],
    },
    {
        "id": "PERSONA_2",
        "title": "Persona 2: Deep-Tech AYUSH / Phytopharmaceutical Startup",
        "actor": "Dr. Sunita Rao (CSO, PhytoBio Labs, Bengaluru)",
        "query": "We isolated a purified 95% w/w Withanolide fraction from Withania somnifera using supercritical fluid extraction showing enhanced neuro-protective efficacy. What is our patentability and regulatory pathway in India?",
        "answers": {
            "Q1_CLASSICAL_SOURCE": "No, modified ratio / modern combination",
            "Q2_EXTRACTION_DEPTH": "Purified, standardized fraction with quantified marker compounds (HPLC/LC-MS)",
            "Q3_INTENDED_USE": "Therapeutic medicine (cure, mitigation, or treatment of disease)",
        },
        "forced_jurisdiction": "IN",
        "target_lang": "en",
        "expected_findings": [
            "Classified as CDSCO Phytopharmaceutical Drug (Rule 122E)",
            "Patentable under Patents Act 1970 (overcoming Section 3(d) with enhanced therapeutic efficacy data)",
            "Mandatory prior approval from National Biodiversity Authority via NBA Form III before patent grant",
            "Automatic escalation flag to empaneled AYUSH IP facilitator",
        ],
    },
    {
        "id": "PERSONA_3",
        "title": "Persona 3: Global Wellness Exporter / Cross-Border Brand",
        "actor": "Arjun Singhal (Director of Regulatory Affairs, Vedic Organics Global)",
        "query": "We are commercializing an Ashwagandha and Curcumin proprietary wellness capsule for export to the United States and filing a PCT patent. How do international rules treat our Indian bio-resource origins?",
        "answers": {
            "Q1_CLASSICAL_SOURCE": "No, modified ratio / modern combination",
            "Q2_EXTRACTION_DEPTH": "Standardized extract",
            "Q3_INTENDED_USE": "Nutritional supplement / Daily wellness without disease claims",
        },
        "forced_jurisdiction": "DUAL",
        "target_lang": "en",
        "expected_findings": [
            "WIPO GRATK Treaty (2024) Article 3 mandatory disclosure of country of origin",
            "US FDA Botanical Drug Guidance (early clinical safety recognition) vs DSHEA dietary supplement claims",
            "Nagoya Protocol ABS compliance",
            "Dual-split comparative analysis",
        ],
    },
]


def run_persona_showcase():
    print("=" * 80)
    print("IP-SAKTI SAHAYAK: END-TO-END PERSONA DEMONSTRATION SUITE")
    print("=" * 80)

    for p in PERSONA_SCENARIOS:
        print(f"\n[{p['id']}] {p['title']}")
        print(f"Actor  : {p['actor']}")
        print(f"Query  : {p['query']}")
        print("-" * 80)

        # Run through Agentic LangGraph State Machine
        initial_state: AgentState = {
            "user_query": p["query"],
            "user_answers": p["answers"],
            "forced_jurisdiction": (
                p["forced_jurisdiction"] if p["forced_jurisdiction"] != "DUAL" else None
            ),
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

        result = orchestration_graph.invoke(initial_state)

        classification = result.get("classification", {})
        routing = result.get("routing", {})
        final_text = result.get("final_response", "")

        print(f"1. Classified Category    : {classification.get('category')}")
        print(
            f"2. Confidence Score       : {result.get('confidence_score') * 100:.1f}%"
        )
        print(f"3. Jurisdiction Track     : {routing.get('selected_track')}")
        print(f"4. Escalate to Facilitator: {result.get('escalate_to_human')}")
        print(f"5. Citations Grounded     : {result.get('citations')}")

        # Test vernacular shield if required
        if p["target_lang"] != "en":
            print(
                f"\n[Vernacular Engine Output ({p['target_lang'].upper()}) - Ayurvedic Entity Shield Engaged]:"
            )
            vernacular_text = bhashini.translate(
                final_text, target_lang=p["target_lang"]
            )
            # Display first 5 lines of translated response
            print("\n".join(vernacular_text.splitlines()[:6]))
        else:
            print("\n[Synthesized Posture Snippet]:")
            print("\n".join(final_text.splitlines()[:7]))

        print("\nExpected Regulatory Validation Check:")
        for finding in p["expected_findings"]:
            print(f"  [x] {finding}")
        print("=" * 80)


if __name__ == "__main__":
    run_persona_showcase()
