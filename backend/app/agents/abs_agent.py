"""
ABS & Biodiversity Specialist Agent (abs_agent.py)
Evaluates statutory duties under:
- Biological Diversity Act, 2002 (Amended 2023)
- Biological Diversity Rules, 2024
- National Biodiversity Authority (NBA) & State Biodiversity Board (SBB) procedures
"""

from typing import Dict, Any, List


def evaluate_abs_compliance(state: Dict[str, Any]) -> str:
    """
    Evaluates Access and Benefit-Sharing (ABS) compliance obligations,
    statutory forms, and practitioner exemptions under the BDA 2023.
    """
    classification = state.get("classification") or {}
    category = str(classification.get("category", "")).lower()
    query = state.get("user_query", "").lower()

    findings: List[str] = []

    # 1. Patent / IPR Approval Mandate (Section 6)
    findings.append(
        "* **Mandatory Prior Approval for IPR Filing (Section 6, BDA 2023):** "
        "Any person applying for an Intellectual Property Right (patent) inside or outside India based on an invention "
        "derived from any biological resource obtained from India (or associated traditional knowledge) is required to obtain "
        "prior approval from the **National Biodiversity Authority (NBA)** before the grant of the patent. "
        "The statutory application must be submitted through **NBA Form III**."
    )

    # 2. Commercial Access vs. SBB Intimation (Section 7)
    if "classical" in category:
        findings.append(
            "* **Commercial Utilization & SBB Intimation (Section 7):** "
            "Indian citizens and domestic corporate entities utilizing biological resources for commercial production must give "
            "prior intimation to the concerned **State Biodiversity Board (SBB)** in the prescribed state form."
        )
    else:
        findings.append(
            "* **Commercial Sourcing & Value Addition (Section 7):** "
            "Commercial manufacturing using Indian biological resources (roots, bark, seeds) requires formal intimation "
            "to the State Biodiversity Board (SBB). If sourcing involves non-Indian entities or foreign-funded companies "
            "(defined under Section 3(2)), approval must be sought directly from the NBA via **Form I**."
        )

    # 3. 2023 Amendment Decriminalization & Statutory Exemptions
    findings.append(
        "* **2023 Statutory Exemptions (Section 40 & Proviso to Section 7):**"
        "\n  - **Registered AYUSH Practitioners:** Vaidyas, Hakims, and Siddha practitioners practicing codified medicine "
        "are exempt from commercial benefit-sharing fees."
        "\n  - **Cultivated Medicinal Plants:** If raw herbs are sourced exclusively from registered growers and cultivated "
        "lands (holding a Certificate of Origin), access fees are exempted."
        "\n  - **Codified Traditional Knowledge:** Formulations prepared directly from First Schedule texts are exempted "
        "from commercial ABS levies under Section 40, though sourcing transparency remains mandatory."
        "\n  - **Decriminalization:** Offenses under the 2023 Amendment are decriminalized; penalties are now civil financial "
        "adjudications rather than custodial sentences."
    )

    # 4. Fair and Equitable Benefit-Sharing Calculation
    findings.append(
        "* **Benefit-Sharing Levies:** Under the 2024 ABS Guidelines, commercial manufacturers must share between "
        "**0.1% to 0.5%** of the ex-factory gross sales turnover with the State Biodiversity Board, depending on annual turnover brackets."
    )

    return "\n".join(findings)


# -------------------------------------------------------------
# Module Self-Test
# -------------------------------------------------------------
if __name__ == "__main__":
    dummy_state = {
        "user_query": "I am sourcing wild Guggal from Rajasthan forests for my startup.",
        "classification": {"category": "Patent & Proprietary"},
        "retrieved_chunks": [],
    }
    print("=== ABS Specialist Agent Test ===")
    print(evaluate_abs_compliance(dummy_state))
