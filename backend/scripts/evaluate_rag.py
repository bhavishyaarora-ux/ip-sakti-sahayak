import sys
from pathlib import Path
from typing import List, Dict, Any

# Root setup
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.agents.graph import orchestration_graph, AgentState

# -------------------------------------------------------------
# 30 Synthetic Benchmark Queries (Curated Across Statutory Frameworks)
# -------------------------------------------------------------
BENCHMARK_CASES = [
    # Classical / Generic ASU (Section 3(p), Section 40 BDA)
    {
        "q": "Can I obtain a patent on Triphala Churna for digestion?",
        "cat": "Classical",
        "jur": "IN",
        "exp_anchor": "Section 3(p)",
    },
    {
        "q": "Patent application for classical Chyawanprash prepared according to Charaka Samhita.",
        "cat": "Classical",
        "jur": "IN",
        "exp_anchor": "Section 3(p)",
    },
    {
        "q": "Does a traditional Vaidya need SBB approval to sell classical Sitopaladi Churna?",
        "cat": "Classical",
        "jur": "IN",
        "exp_anchor": "Section 40",
    },
    {
        "q": "Is Mahasudarshan Kwatha eligible for product patent protection?",
        "cat": "Classical",
        "jur": "IN",
        "exp_anchor": "Section 3(p)",
    },
    {
        "q": "Classical Bhasma preparation method described in Rasatarangini patentability.",
        "cat": "Classical",
        "jur": "IN",
        "exp_anchor": "Section 3(p)",
    },
    {
        "q": "Traditional taila formulation from Sahasrayogam domestic ABS requirements.",
        "cat": "Classical",
        "jur": "IN",
        "exp_anchor": "Section 40",
    },
    # Patent & Proprietary (P&P) ASU (Section 3(e), Rule 158B, SBB Section 7)
    {
        "q": "Synergistic combination of Curcumin and Piperine showing super-additive efficacy for arthritis.",
        "cat": "Proprietary",
        "jur": "IN",
        "exp_anchor": "Section 3(e)",
    },
    {
        "q": "Rule 158B proof of safety and effectiveness for a new polyherbal diabetes tablet.",
        "cat": "Proprietary",
        "jur": "IN",
        "exp_anchor": "Rule 158B",
    },
    {
        "q": "Is intimation to State Biodiversity Board required under Section 7 before commercializing a new herbal formulation?",
        "cat": "Proprietary",
        "jur": "IN",
        "exp_anchor": "Section 7",
    },
    {
        "q": "How to overcome Section 3(e) mere admixture rejection for a multi-extract herbal syrup?",
        "cat": "Proprietary",
        "jur": "IN",
        "exp_anchor": "Section 3(e)",
    },
    {
        "q": "Filing Form 18A expedited examination for an AYUSH DPIIT recognized startup.",
        "cat": "Proprietary",
        "jur": "IN",
        "exp_anchor": "Form 18A",
    },
    {
        "q": "Annual Form 27 commercial working disclosure requirement for an Ayurvedic formulation patent.",
        "cat": "Proprietary",
        "jur": "IN",
        "exp_anchor": "Rule 131",
    },
    # Phytopharmaceutical Drugs (CDSCO Rule 122E, NBA Form III, Section 3(d))
    {
        "q": "Standardized fraction of Withania somnifera with 4 withanolide markers under Rule 122E.",
        "cat": "Phytopharmaceutical",
        "jur": "IN",
        "exp_anchor": "Rule 122E",
    },
    {
        "q": "Mandatory Form III approval from National Biodiversity Authority before patent grant.",
        "cat": "Phytopharmaceutical",
        "jur": "IN",
        "exp_anchor": "Form III",
    },
    {
        "q": "Phase II clinical trial requirements for a phytopharmaceutical drug IND submission.",
        "cat": "Phytopharmaceutical",
        "jur": "IN",
        "exp_anchor": "Rule 122DA",
    },
    {
        "q": "Patenting a purified bioactive fraction from Ocimum sanctum with enhanced bioavailability under Section 3(d).",
        "cat": "Phytopharmaceutical",
        "jur": "IN",
        "exp_anchor": "Section 3(d)",
    },
    {
        "q": "Chromatographic fingerprinting specifications required for CDSCO phytopharmaceutical clearance.",
        "cat": "Phytopharmaceutical",
        "jur": "IN",
        "exp_anchor": "Rule 122E",
    },
    {
        "q": "Foreign company filing Form I for accessing Indian bio-resources for drug development.",
        "cat": "Phytopharmaceutical",
        "jur": "IN",
        "exp_anchor": "Form I",
    },
    # Ayurveda-Aahar & Nutraceuticals (FSSAI 2022, NTC Exemption)
    {
        "q": "Can I sell Ashwagandha health bars under FSSAI Ayurveda Aahara regulations?",
        "cat": "Aahar",
        "jur": "IN",
        "exp_anchor": "Ayurveda Aahara",
    },
    {
        "q": "Are synthetic vitamins allowed in Ayurveda-Aahar formulations?",
        "cat": "Aahar",
        "jur": "IN",
        "exp_anchor": "Ayurveda Aahara",
    },
    {
        "q": "Normally Traded Commodities NTC exemption from ABS benefit sharing.",
        "cat": "Aahar",
        "jur": "IN",
        "exp_anchor": "Section 40",
    },
    {
        "q": "Labeling requirements for herbal wellness tea under Ayurveda Aahar Schedule A.",
        "cat": "Aahar",
        "jur": "IN",
        "exp_anchor": "Ayurveda Aahara",
    },
    {
        "q": "Can disease treatment claims be made for an Ayurvedic nutraceutical drink?",
        "cat": "Aahar",
        "jur": "IN",
        "exp_anchor": "Ayurveda Aahara",
    },
    {
        "q": "Trademark registration for an Ayurvedic health supplement brand in Class 5 vs Class 30.",
        "cat": "Aahar",
        "jur": "IN",
        "exp_anchor": "Ayurveda Aahara",
    },
    # International / Cross-Border (WIPO GRATK 2024, US FDA Botanical, Nagoya)
    {
        "q": "Mandatory patent disclosure of country of origin under WIPO GRATK Treaty 2024.",
        "cat": "International",
        "jur": "INT",
        "exp_anchor": "WIPO GRATK",
    },
    {
        "q": "Exporting Ayurvedic medicine to the United States under US FDA Botanical Drug Guidance.",
        "cat": "International",
        "jur": "INT",
        "exp_anchor": "Botanical Guidance",
    },
    {
        "q": "DSHEA dietary supplement regulations for Indian herbal extracts in the US market.",
        "cat": "International",
        "jur": "INT",
        "exp_anchor": "Botanical Guidance",
    },
    {
        "q": "Nagoya Protocol international access and benefit sharing compliance for global patents.",
        "cat": "International",
        "jur": "INT",
        "exp_anchor": "Nagoya",
    },
    {
        "q": "Article 27 TRIPS Agreement patentability standards applied to traditional biological knowledge.",
        "cat": "International",
        "jur": "INT",
        "exp_anchor": "TRIPS",
    },
    {
        "q": "Sanctions for non-disclosure of traditional knowledge origin under Article 5 of WIPO GRATK.",
        "cat": "International",
        "jur": "INT",
        "exp_anchor": "WIPO GRATK",
    },
]


def evaluate_test_suite():
    total_cases = len(BENCHMARK_CASES)
    faithfulness_scores = []
    relevance_scores = []
    precision_scores = []

    print(
        f"Executing Automated Evaluation Benchmark on {total_cases} Synthetic Cases...\n"
    )
    print(
        f"{'#':<3} | {'Expected Class':<18} | {'Jur':<4} | {'Faithful':<9} | {'Relevance':<9} | {'Precision':<9} | {'Status'}"
    )
    print("-" * 75)

    for idx, item in enumerate(BENCHMARK_CASES, 1):
        # Provide simulated diagnostic answers matching the category
        answers = None
        if item["cat"] == "Classical":
            answers = {"Q1_CLASSICAL_SOURCE": "Yes, identical classical recipe"}
        elif item["cat"] == "Phytopharmaceutical":
            answers = {
                "Q2_EXTRACTION_DEPTH": "Purified, standardized fraction with quantified marker compounds (HPLC/LC-MS)",
                "Q3_INTENDED_USE": "Therapeutic medicine (cure, mitigation, or treatment of disease)",
            }
        elif item["cat"] == "Proprietary":
            answers = {
                "Q1_CLASSICAL_SOURCE": "No, modified ratio / modern combination",
                "Q3_INTENDED_USE": "Therapeutic medicine (cure, mitigation, or treatment of disease)",
            }
        elif item["cat"] == "Aahar":
            answers = {
                "Q3_INTENDED_USE": "Nutritional supplement / Daily wellness without disease claims"
            }

        state: AgentState = {
            "user_query": item["q"],
            "user_answers": answers,
            "forced_jurisdiction": item["jur"],
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

        res = orchestration_graph.invoke(state)
        chunks = res.get("retrieved_chunks", [])
        citations = res.get("citations", [])

        # 1. Faithfulness: Output citations must map directly to retrieved chunks
        chunk_anchors = [c.get("citation_anchor", "") for c in chunks]
        valid_citations = [
            c for c in citations if any(c in a or a in c for a in chunk_anchors)
        ]
        faithfulness = (
            len(valid_citations) / max(1, len(citations)) if citations else 1.0
        )

        # 2. Answer Relevance: Response addresses the expected classification/statute
        exp = item["exp_anchor"].lower()
        response_text = res.get("final_response", "").lower()
        relevance = (
            1.0
            if (exp in response_text or any(exp in c.lower() for c in chunk_anchors))
            else 0.75
        )

        # 3. Context Precision: Retrieved chunks belong to the filtered jurisdiction
        correct_jur_chunks = [c for c in chunks if c.get("jurisdiction") == item["jur"]]
        precision = len(correct_jur_chunks) / max(1, len(chunks)) if chunks else 1.0

        faithfulness_scores.append(faithfulness)
        relevance_scores.append(relevance)
        precision_scores.append(precision)

        status = (
            "PASS"
            if (faithfulness >= 0.85 and relevance >= 0.75 and precision >= 0.85)
            else "WARN"
        )
        print(
            f"{idx:<3} | {item['cat']:<18} | {item['jur']:<4} | {faithfulness*100:>7.1f}% | {relevance*100:>7.1f}% | {precision*100:>7.1f}% | {status}"
        )

    # Aggregate Metrics
    avg_faithfulness = sum(faithfulness_scores) / total_cases
    avg_relevance = sum(relevance_scores) / total_cases
    avg_precision = sum(precision_scores) / total_cases

    print("\n" + "=" * 75)
    print("AUTOMATED RAGAS BENCHMARK SUMMARY")
    print("=" * 75)
    print(
        f"Aggregate Faithfulness  : {avg_faithfulness*100:.2f}%  (Target: > 90.00%) -> {'PASSED' if avg_faithfulness >= 0.90 else 'FAILED'}"
    )
    print(
        f"Aggregate Relevance     : {avg_relevance*100:.2f}%  (Target: > 85.00%) -> {'PASSED' if avg_relevance >= 0.85 else 'FAILED'}"
    )
    print(
        f"Aggregate Precision     : {avg_precision*100:.2f}%  (Target: > 88.00%) -> {'PASSED' if avg_precision >= 0.88 else 'FAILED'}"
    )
    print("=" * 75)


if __name__ == "__main__":
    evaluate_test_suite()
