"""
Export & International Specialist Agent (export_agent.py)
Evaluates cross-border obligations under:
- WIPO Treaty on Intellectual Property, Genetic Resources and Associated Traditional Knowledge (GRATK, 2024)
- Nagoya Protocol on Access and Benefit Sharing
- US FDA Botanical Drug Guidance & DSHEA (21 CFR)
- European Medicines Agency (EMA) Directive 2004/24/EC (THMPD)
"""

from typing import Dict, Any, List


def evaluate_export_regime(state: Dict[str, Any]) -> str:
    """
    Evaluates export compliance, foreign market entry pathways, and international
    traditional knowledge disclosure duties.
    """
    routing = state.get("routing") or {}
    query = state.get("user_query", "").lower()
    markets = routing.get("target_export_markets", [])

    findings: List[str] = []

    # 1. WIPO GRATK Treaty (2024) - Mandatory Disclosure
    findings.append(
        "* **WIPO GRATK Treaty (2024) - Article 3 Mandatory Disclosure:**"
        "\n  When filing patent applications internationally (via the Patent Cooperation Treaty - PCT or national offices abroad), "
        "applicants **must explicitly disclose**:"
        "\n  1. The Country of Origin of the genetic resources used (India)."
        "\n  2. The Indigenous Peoples or Local Community that provided the traditional knowledge (if based on AYUSH texts/practices)."
        "\n  *Failure to comply can trigger pre-grant and post-grant opposition under multilateral patent frameworks.*"
    )

    # 2. Nagoya Protocol (Access & Benefit Sharing Abroad)
    findings.append(
        "* **Nagoya Protocol Compliance:** "
        "Exporting Indian biological resources for foreign R&D or commercialization requires obtaining **Prior Informed Consent (PIC)** "
        "and **Mutually Agreed Terms (MAT)**, evidenced by an Internationally Recognized Certificate of Compliance (IRCC) "
        "issued by India's NBA."
    )

    # 3. United States Market Access (US FDA / DSHEA)
    if (
        not markets
        or any("united states" in m.lower() or "fda" in m.lower() for m in markets)
        or "us" in query
    ):
        findings.append(
            "* **United States Market Regulatory Pathways (US FDA):**"
            "\n  - **Dietary Supplement Route (DSHEA / 21 CFR Part 111):** Ayurvedic herbs can enter as dietary supplements "
            "if ingredients were marketed before Oct 15, 1994, or submit a New Dietary Ingredient (NDI) notification. "
            "**Strict Bar:** Cannot carry any disease mitigation, cure, or treatment claims on labels."
            "\n  - **Botanical Drug Pathway (CDER Guidance):** If therapeutic claims are made, the formulation must follow "
            "the Botanical IND pathway. The FDA permits reliance on documented Ayurvedic pharmacopoeial use in India to "
            "substantiate initial human safety, allowing expedited entry into Phase 2 clinical trials."
        )

    # 4. European Union Market Access (EMA THMPD)
    if (
        not markets
        or any("europe" in m.lower() or "eu" in m.lower() for m in markets)
        or "europe" in query
    ):
        findings.append(
            "* **European Union Market Entry (Directive 2004/24/EC - THMPD):**"
            "\n  To qualify for the Traditional Herbal Medicinal Products Directive pathway without full clinical trials, "
            "you must document **30 years of continuous medicinal use**, including at least **15 years within the European Union**. "
            "Otherwise, entry is restricted to Food Supplements (EFSA) or full marketing authorization (MA)."
        )

    return "\n".join(findings)


# -------------------------------------------------------------
# Module Self-Test
# -------------------------------------------------------------
if __name__ == "__main__":
    dummy_state = {
        "user_query": "How do I export my Ayurvedic formulation to the United States and file a patent?",
        "routing": {"target_export_markets": ["United States (US FDA)"]},
        "classification": {"category": "Patent & Proprietary"},
    }
    print("=== Export Specialist Agent Test ===")
    print(evaluate_export_regime(dummy_state))
