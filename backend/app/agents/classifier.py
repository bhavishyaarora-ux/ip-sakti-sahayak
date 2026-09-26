import re
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class FormulationCategory(str, Enum):
    CLASSICAL = "Classical / Generic ASU"
    PATENT_PROPRIETARY = "Patent or Proprietary (P&P) ASU"
    PHYTOPHARMACEUTICAL = "Phytopharmaceutical Drug"
    AYURVEDA_AAHAR = "Ayurveda-Aahar (Nutraceutical)"
    COSMETIC = "Ayurvedic Cosmetic"
    UNCERTAIN = "Needs Clarification"


class ClarifyingQuestion(BaseModel):
    question_id: str
    question: str
    options: List[str]
    legal_rationale: str


class ClassificationResult(BaseModel):
    category: FormulationCategory
    confidence: float
    is_definitive: bool
    rationale: str
    clarifying_questions: List[ClarifyingQuestion] = Field(default_factory=list)
    ip_posture: str
    abs_mandate: str
    statutory_governance: str
    recommended_retrieval_tags: List[str]


# -------------------------------------------------------------
# Canonical Clarifying Questions (Problem Statement Decision Gate)
# -------------------------------------------------------------
CANONICAL_QUESTIONS = [
    ClarifyingQuestion(
        question_id="Q1_CLASSICAL_SOURCE",
        question="Is this exact formulation and method directly drawn from a First Schedule authoritative text (e.g., Charaka Samhita, Sharangadhara, Sahasrayogam)?",
        options=[
            "Yes, identical classical recipe",
            "No, modified ratio / modern combination",
        ],
        legal_rationale="Classical recipes are barred from patenting under Section 3(p) and protected as Traditional Knowledge via TKDL.",
    ),
    ClarifyingQuestion(
        question_id="Q2_EXTRACTION_DEPTH",
        question="What is the nature of the active formulation?",
        options=[
            "Whole herb / Traditional aqueous extract (Kwatha, Asava, Swarasa)",
            "Purified, standardized fraction with quantified marker compounds (HPLC/LC-MS)",
        ],
        legal_rationale="Purified fractions fall under CDSCO Phytopharmaceutical Rules (Rule 122E) with genuine patentability potential.",
    ),
    ClarifyingQuestion(
        question_id="Q3_INTENDED_USE",
        question="What is the commercial intended use and claim of the product?",
        options=[
            "Therapeutic medicine (cure, mitigation, or treatment of disease)",
            "Nutritional supplement / Daily wellness without disease claims",
            "Topical skin, hair, or oral hygiene (Cosmetic)",
        ],
        legal_rationale="Therapeutic claims require AYUSH/CDSCO drug licensing, whereas health supplements fall under FSSAI Ayurveda-Aahar Regulations, 2022.",
    ),
]

# -------------------------------------------------------------
# Statutory Postures Per Category
# -------------------------------------------------------------
CATEGORY_POSTURES = {
    FormulationCategory.CLASSICAL: {
        "ip_posture": "Strictly barred from product patents under Section 3(p) of the Patents Act (Traditional Knowledge). Defended by CSIR through TKDL prior art.",
        "abs_mandate": "Exempt from NBA Access & Benefit Sharing under Section 40 / 2023 Amendment for registered AYUSH practitioners and codified formulations.",
        "statutory_governance": "Drugs & Cosmetics Act 1940 (Chapter IV-A, First Schedule authoritative texts).",
        "tags": ["TK_Bar", "ASU_Licensing_Proof", "NTC_Exemption"],
    },
    FormulationCategory.PATENT_PROPRIETARY: {
        "ip_posture": "Faces strict patent exclusion under Section 3(e) (mere admixture). Patentable ONLY if synergistic, super-additive therapeutic efficacy is proven with comparative clinical data.",
        "abs_mandate": "Mandatory prior intimation to State Biodiversity Board (SBB) under Section 7 of Biological Diversity Act for commercial production.",
        "statutory_governance": "Drugs & Cosmetics Rules 1945 (Rule 158B licensing pathway).",
        "tags": [
            "Synergy_Admixture",
            "ASU_Licensing_Proof",
            "BDA_Mandatory_Intimation",
        ],
    },
    FormulationCategory.PHYTOPHARMACEUTICAL: {
        "ip_posture": "High patentability potential for novel isolation processes, purified bioactive fractions, and specific therapeutic indications.",
        "abs_mandate": "Mandatory NBA Form III approval before patent grant, and Form I approval for foreign entity commercial access.",
        "statutory_governance": "CDSCO / DCGI Rules 122DA & 122E (Phytopharmaceutical Guidelines, 2015).",
        "tags": ["Efficacy_Enhancement", "Phyto_CDSCO_Gateway", "NBA_IPR_Approval"],
    },
    FormulationCategory.AYURVEDA_AAHAR: {
        "ip_posture": "Formulation patent barred under Section 3(p). Protection limited to Trade Marks, Trade Dress, and novel manufacturing trade secrets. Cannot claim disease cures.",
        "abs_mandate": "Subject to SBB benefit-sharing if biological resources are wild-harvested; exempted if purchased as Normally Traded Commodities (NTC).",
        "statutory_governance": "FSSAI Food Safety and Standards (Ayurveda Aahara) Regulations, 2022 (Schedule A positive list).",
        "tags": ["FSSAI_Food_Reg", "NTC_Exemption", "TK_Bar"],
    },
    FormulationCategory.COSMETIC: {
        "ip_posture": "Recipe generally non-patentable under Section 3(e). IP relies on Design Registrations (packaging), Trade Marks (Class 3), and proprietary formulations.",
        "abs_mandate": "Prior intimation to SBB required if commercial bio-resources are procured directly from Indian habitats.",
        "statutory_governance": "Drugs & Cosmetics Act 1940 (Schedule S Indian Standards for Cosmetics).",
        "tags": ["ASU_Licensing_Proof", "BDA_Mandatory_Intimation"],
    },
}


class FormulationClassifier:
    """
    Deterministic diagnostic gate executing heuristic keyword screening
    and triage routing before vector retrieval.
    """

    def __init__(self):
        # Lexical pattern triggers
        self.classical_keywords = [
            r"charak",
            r"sushrut",
            r"ashtang",
            r"sahasrayogam",
            r"sharangadhar",
            r"bhavaprakash",
            r"first schedule",
            r"classical",
            r"churna",
            r"kwatha",
            r"arishta",
            r"asava",
            r"bhasma",
            r"taila",
            r"ghrita",
            r"lehyam",
        ]
        self.phyto_keywords = [
            r"phytopharmaceutical",
            r"standardized fraction",
            r"isolated fraction",
            r"marker compound",
            r"bioactive isolate",
            r"hplc fingerprint",
            r"purified extract",
            r"chromatographic",
            r"withanolide a",
            r"curcuminoid fraction",
        ]
        self.aahar_keywords = [
            r"ayurveda aahar",
            r"ayurvedic food",
            r"nutraceutical",
            r"dietary supplement",
            r"health drink",
            r"herbal tea",
            r"wellness tea",
            r"fssai",
            r"energy bar",
            r"candy",
        ]
        self.cosmetic_keywords = [
            r"cream",
            r"lotion",
            r"face wash",
            r"hair oil",
            r"lip balm",
            r"soap",
            r"cosmetic",
            r"skin care",
            r"shampoo",
            r"sunscreen",
        ]

    def _matches_any(self, patterns: List[str], text: str) -> bool:
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    def classify(
        self, user_query: str, user_answers: Optional[Dict[str, str]] = None
    ) -> ClassificationResult:
        """
        Evaluates input text and optional clarifying answers to categorize the AYUSH formulation.
        """
        answers = user_answers or {}
        text = user_query.strip()

        # Step 1: Evaluate explicit questionnaire answers if provided
        if answers.get("Q1_CLASSICAL_SOURCE") == "Yes, identical classical recipe":
            return self._build_result(
                category=FormulationCategory.CLASSICAL,
                confidence=0.98,
                is_definitive=True,
                rationale="User confirmed the formulation is sourced directly from a First Schedule authoritative text.",
            )

        if (
            answers.get("Q2_EXTRACTION_DEPTH")
            == "Purified, standardized fraction with quantified marker compounds (HPLC/LC-MS)"
        ):
            return self._build_result(
                category=FormulationCategory.PHYTOPHARMACEUTICAL,
                confidence=0.95,
                is_definitive=True,
                rationale="User identified the product as an isolated, standardized botanical fraction governed under Rule 122E.",
            )

        if (
            answers.get("Q3_INTENDED_USE")
            == "Nutritional supplement / Daily wellness without disease claims"
        ):
            return self._build_result(
                category=FormulationCategory.AYURVEDA_AAHAR,
                confidence=0.92,
                is_definitive=True,
                rationale="User confirmed non-medicinal nutritional supplement positioning under FSSAI Ayurveda-Aahar Regulations.",
            )

        if (
            answers.get("Q3_INTENDED_USE")
            == "Topical skin, hair, or oral hygiene (Cosmetic)"
        ):
            return self._build_result(
                category=FormulationCategory.COSMETIC,
                confidence=0.92,
                is_definitive=True,
                rationale="User specified topical aesthetic application governed under D&C Act Schedule S cosmetic standards.",
            )

        if (
            answers.get("Q3_INTENDED_USE")
            == "Therapeutic medicine (cure, mitigation, or treatment of disease)"
            and answers.get("Q1_CLASSICAL_SOURCE")
            == "No, modified ratio / modern combination"
        ):
            return self._build_result(
                category=FormulationCategory.PATENT_PROPRIETARY,
                confidence=0.94,
                is_definitive=True,
                rationale="Identified as a modern therapeutic combination governed as a Patent & Proprietary (P&P) ASU medicine.",
            )

        # Step 2: Direct heuristic screening from query text
        if self._matches_any(self.phyto_keywords, text):
            return self._build_result(
                category=FormulationCategory.PHYTOPHARMACEUTICAL,
                confidence=0.88,
                is_definitive=True,
                rationale="Query specifically describes purified/standardized fractions or chromatographic markers.",
            )

        if self._matches_any(self.aahar_keywords, text):
            return self._build_result(
                category=FormulationCategory.AYURVEDA_AAHAR,
                confidence=0.85,
                is_definitive=True,
                rationale="Query references food, beverage, or FSSAI nutraceutical product positioning.",
            )

        if self._matches_any(self.cosmetic_keywords, text):
            return self._build_result(
                category=FormulationCategory.COSMETIC,
                confidence=0.85,
                is_definitive=True,
                rationale="Query indicates topical aesthetic or cosmetic hygiene application.",
            )

        if self._matches_any(self.classical_keywords, text):
            return self._build_result(
                category=FormulationCategory.CLASSICAL,
                confidence=0.87,
                is_definitive=True,
                rationale="Query directly references classical texts, traditional galenicals (kwatha/churna), or generic Ayurvedic terminology.",
            )

        # Step 3: Ambiguous or Under-specified Query -> Trigger Clarifying Questions
        return ClassificationResult(
            category=FormulationCategory.UNCERTAIN,
            confidence=0.40,
            is_definitive=False,
            rationale="Query lacks sufficient regulatory specifics (authoritative text status, extraction level, or intended therapeutic claim).",
            clarifying_questions=CANONICAL_QUESTIONS,
            ip_posture="Indeterminate. Awaiting formulation clarity to establish patentability vs Section 3(p) exclusion.",
            abs_mandate="Indeterminate. Dependent on practitioner exemption vs commercial exploitation.",
            statutory_governance="General ASU Drug & Biodiversity Gateway.",
            recommended_retrieval_tags=[
                "TK_Bar",
                "Synergy_Admixture",
                "ASU_Licensing_Proof",
            ],
        )

    def _build_result(
        self,
        category: FormulationCategory,
        confidence: float,
        is_definitive: bool,
        rationale: str,
    ) -> ClassificationResult:
        posture = CATEGORY_POSTURES[category]
        return ClassificationResult(
            category=category,
            confidence=confidence,
            is_definitive=is_definitive,
            rationale=rationale,
            clarifying_questions=[],
            ip_posture=posture["ip_posture"],
            abs_mandate=posture["abs_mandate"],
            statutory_governance=posture["statutory_governance"],
            recommended_retrieval_tags=posture["tags"],
        )


# -------------------------------------------------------------
# Module Self-Test
# -------------------------------------------------------------
if __name__ == "__main__":
    classifier = FormulationClassifier()

    # Test Case 1: Ambiguous Query (Matches problem statement example)
    q1 = "I have a Tulsi extract for asthma"
    res1 = classifier.classify(q1)
    print("=== TEST CASE 1: Ambiguous Query ===")
    print(f"Query: '{q1}'")
    print(f"Category: {res1.category.value} (Confidence: {res1.confidence})")
    print(f"Definitive: {res1.is_definitive}")
    print(f"Clarifying Questions Needed: {len(res1.clarifying_questions)}")
    for q in res1.clarifying_questions:
        print(f"  [{q.question_id}] {q.question}")

    # Test Case 2: User provides clarifying answers to resolve Test Case 1
    user_answers = {
        "Q1_CLASSICAL_SOURCE": "No, modified ratio / modern combination",
        "Q2_EXTRACTION_DEPTH": "Whole herb / Traditional aqueous extract (Kwatha, Asava, Swarasa)",
        "Q3_INTENDED_USE": "Therapeutic medicine (cure, mitigation, or treatment of disease)",
    }
    res2 = classifier.classify(q1, user_answers=user_answers)
    print("\n=== TEST CASE 2: Resolved with Clarifying Answers ===")
    print(f"Category: {res2.category.value} (Confidence: {res2.confidence})")
    print(f"IP Posture: {res2.ip_posture}")
    print(f"ABS Mandate: {res2.abs_mandate}")
    print(f"Recommended Tags: {res2.recommended_retrieval_tags}")

    # Test Case 3: Clear Phytopharmaceutical
    q3 = "We isolated a standardized fraction from Ashwagandha with 4 withanolide markers for cognitive decline"
    res3 = classifier.classify(q3)
    print("\n=== TEST CASE 3: Clear Phytopharmaceutical ===")
    print(f"Category: {res3.category.value} (Confidence: {res3.confidence})")
    print(f"IP Posture: {res3.ip_posture}")
    print(f"Statutory Governance: {res3.statutory_governance}")
