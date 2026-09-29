"""
IP Specialist Agent (ip_agent.py)
Evaluates statutory eligibility under:
- Indian Patents Act, 1970 (and Patents (Amendment) Rules, 2024)
- Trade Marks Act, 1999
- Geographical Indications of Goods Act, 1999
- Designs Act, 2000 & Trade Secrets
"""

from typing import Dict, Any, List


def evaluate_ip_regime(state: Dict[str, Any]) -> str:
    """
    Evaluates the intellectual property posture based on formulation classification
    and user claims.
    """
    classification = state.get("classification") or {}
    category = str(classification.get("category", "")).lower()
    query = state.get("user_query", "").lower()
    chunks = state.get("retrieved_chunks") or []

    findings: List[str] = []

    # 1. Classical / Generic Formulations
    if "classical" in category:
        findings.append(
            "* **Product Patent Eligibility: BARRED under Section 3(p) of the Patents Act, 1970.** "
            "Formulations, ingredients, and therapeutic uses codified in First Schedule authoritative texts "
            "(e.g., Charaka Samhita, Sushruta Samhita, Sahasrayogam) constitute prior art protected within the TKDL."
        )
        findings.append(
            "* **Novel Process Patent: EXTREMELY RESTRICTED.** Mere standard decoction, boiling, or extraction "
            "methods are barred under Section 3(d) as known processes unless a completely novel, non-obvious "
            "extraction parameter or technical carrier is utilized."
        )
        findings.append(
            "* **Recommended IP Strategy:**"
            "\n  - **Trademark Registration (Form TM-A):** Protect your distinct brand and commercial product name "
            "under **Nice Class 5** (Pharmaceuticals/Ayurvedic Medicines)."
            "\n  - **Geographical Indication (GI):** If ingredients originate from a defined geographic origin "
            "possessing distinctive reputation or qualities (e.g., Navara Rice, Alleppey Green Cardamom), register "
            "as an authorized user under the GI of Goods Act, 1999."
        )

    # 2. Phytopharmaceuticals
    elif "phytopharmaceutical" in category:
        findings.append(
            "* **Patent Eligibility: HIGH (Product & Process Patents under Section 2(1)(j)).** "
            "Standardized botanical fractions extracted from medicinal plants with demonstrated therapeutic efficacy "
            "are eligible for Composition of Matter and Novel Extraction Process patents."
        )
        findings.append(
            "* **Section 3(d) Requirement:** Must submit comparative chromatographic and preclinical data proving "
            "enhanced therapeutic efficacy over the raw herbal crude drug."
        )
        findings.append(
            "* **Regulatory Mandate (CDSCO):** Governed under Chapter VIA / New Drugs Rules, 2019. Requires validation "
            "of at least **4 bioactive/analytical marker compounds** and formal safety/clinical trial clearance."
        )
        findings.append(
            "* **Recommended IP Strategy:** File a provisional patent application immediately (Form 1 & Form 2) "
            "before any clinical trial data or scientific papers enter the public domain."
        )

    # 3. Ayurveda-Aahar / Nutraceuticals
    elif "aahar" in category or "nutraceutical" in category:
        findings.append(
            "* **Patent Eligibility: EXCLUDED for Therapeutic / Medicinal Claims.** Products licensed under the "
            "FSSAI (Ayurveda Aahara) Regulations, 2022 cannot claim to prevent, mitigate, or cure human diseases."
        )
        findings.append(
            "* **Recommended IP Strategy:**"
            "\n  - **Trade Secret Protection:** Maintain precise processing steps, temperature profiles, and ingredient "
            "ratios under Non-Disclosure Agreements (NDAs) and restricted employee access."
            "\n  - **Trademark Registration (Form TM-A):** Protect brand names and logos under **Nice Class 30** (Dietary foods) "
            "and **Class 29** (Herbal preparations)."
            "\n  - **Industrial Design Registration:** Protect novel packaging containers, bottles, or dispensers under the "
            "Designs Act, 2000."
        )

    # 4. Ayurvedic Cosmetics
    elif "cosmetic" in category:
        findings.append(
            "* **Formulation Patent: CONDITIONAL under Section 3(e).** Topical formulations using known herbal oils "
            "(e.g., Kumkumadi, Bhringraj) are presumed to be mere aggregations. To claim patentability, you must furnish "
            "experimental evidence of unexpected synergistic stability, penetration, or cutaneous absorption."
        )
        findings.append(
            "* **Process & Delivery System Patent:** Novel nanotechnology carriers (liposomes, transfersomes) or supercritical "
            "fluid extraction (SFE) techniques are eligible under Section 2(1)(j) & Section 48(b)."
        )
        findings.append(
            "* **Branding & Look-and-Feel:** Register Trademarks under **Nice Class 3** (Cosmetics/Soaps) and register "
            "proprietary bottle/container shapes under the Designs Act, 2000."
        )

    # 5. Patent & Proprietary (P&P) Formulations (Default)
    else:
        findings.append(
            "* **Formulation / Recipe Patent: STRICT SECTION 3(e) OBJECTION.** Mixing classical herbs in novel proportions "
            "faces severe rejection as a 'mere admixture'. You must submit quantitative bio-assay data establishing that "
            "the combination achieves statistically significant therapeutic synergy (Combination Index CI < 1.0)."
        )
        findings.append(
            "* **Process Patent: POTENTIALLY ELIGIBLE under Section 2(1)(j) & Section 48(b).** "
            "Novel solvent systems, temperature/pressure profiles, or modified release dosage forms can be protected "
            "as inventive processes."
        )
        findings.append(
            "* **Procedural Note (Patent Rules 2024):** Statement of Working (Form 27) is now required once every "
            "3 financial years rather than annually, reducing administrative compliance costs for AYUSH startups."
        )

    # Cross-reference with retrieved chunks for specific citations
    patent_chunks = [
        c
        for c in chunks
        if "patents" in c.get("file_source", "").lower()
        or c.get("jurisdiction") == "IN"
    ]
    if patent_chunks:
        matched_anchors = list(
            dict.fromkeys(
                [
                    c.get("citation_anchor")
                    for c in patent_chunks
                    if c.get("citation_anchor")
                ]
            )
        )
        if matched_anchors:
            findings.append(
                f"* **Applicable Statutory Anchors:** {', '.join(f'`[{a}]`' for a in matched_anchors[:3])}"
            )

    return "\n".join(findings)


# -------------------------------------------------------------
# Module Self-Test
# -------------------------------------------------------------
if __name__ == "__main__":
    dummy_state = {
        "user_query": "Can I patent an Ashwagandha root syrup for arthritis?",
        "classification": {"category": "Patent & Proprietary"},
        "retrieved_chunks": [
            {
                "citation_anchor": "Patents Act Sec. 3(e)",
                "file_source": "patents_act_key_sections.md",
                "jurisdiction": "IN",
            }
        ],
    }
    print("=== IP Specialist Agent Test ===")
    print(evaluate_ip_regime(dummy_state))
