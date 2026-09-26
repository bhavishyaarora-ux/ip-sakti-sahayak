import re
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class JurisdictionTrack(str, Enum):
    INDIA = "India Domestic"
    INTERNATIONAL = "International & Cross-Border"
    DUAL_COMPARISON = "Dual Comparison (India vs International)"


class RoutingDecision(BaseModel):
    selected_track: JurisdictionTrack
    active_jurisdictions: List[str] = Field(
        ..., description="List containing 'IN', 'INT', or both for vector DB filtering"
    )
    confidence: float
    routing_rationale: str
    target_export_markets: List[str] = Field(default_factory=list)
    applicable_treaties_and_statutes: List[str] = Field(default_factory=list)


class JurisdictionRouter:
    """
    Directs legal queries to isolated jurisdictional pipelines to prevent
    statutory conflation between Indian acts and international regimes.
    """

    def __init__(self):
        # Lexical pattern banks for international / export cues
        self.intl_general_patterns = [
            r"\b(international|abroad|global|foreign|cross-border|export|exporting|overseas)\b",
            r"\b(wipo|gratk|pct|patent cooperation treaty|madrid|hague|trips|nagoya|cbd)\b",
        ]
        self.us_market_patterns = [
            r"\b(us\b|usa|united states|fda|botanical drug|dshea|ind\b|nda\b|21 cfr)\b"
        ]
        self.eu_market_patterns = [
            r"\b(eu\b|europe|european union|ema|thmpd|directive 2004/24/ec)\b"
        ]

        # Lexical pattern banks for domestic Indian cues
        self.india_patterns = [
            r"\b(india|indian|domestic|inpass|ipo\b|delhi|mumbai|chennai|kolkata)\b",
            r"\b(patents act 1970|section 3\(p\)|section 3\(e\)|section 3\(d\)|rule 131|form 27)\b",
            r"\b(nba\b|sbb\b|bmc\b|national biodiversity authority|state biodiversity board)\b",
            r"\b(ayush|ccras|pcimh|tkdl|first schedule|charaka|fssai|ayurveda aahar)\b",
        ]

    def _has_match(self, patterns: List[str], text: str) -> bool:
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    def route(
        self, query: str, forced_override: Optional[str] = None
    ) -> RoutingDecision:
        """
        Determines the jurisdictional pipeline.
        :param query: Natural language user query.
        :param forced_override: Manual UI toggle ('IN', 'INT', or 'DUAL').
        """
        # 1. Respect explicit manual override from UI switch if provided
        if forced_override:
            mode = forced_override.strip().upper()
            if mode in ["IN", "INDIA"]:
                return RoutingDecision(
                    selected_track=JurisdictionTrack.INDIA,
                    active_jurisdictions=["IN"],
                    confidence=1.0,
                    routing_rationale="User explicitly locked jurisdiction to India via interface toggle.",
                    applicable_treaties_and_statutes=[
                        "Patents Act 1970",
                        "Biological Diversity Act 2002/2023",
                        "D&C Act 1940",
                    ],
                )
            elif mode in ["INT", "INTERNATIONAL"]:
                return RoutingDecision(
                    selected_track=JurisdictionTrack.INTERNATIONAL,
                    active_jurisdictions=["INT"],
                    confidence=1.0,
                    routing_rationale="User explicitly locked jurisdiction to International via interface toggle.",
                    applicable_treaties_and_statutes=[
                        "WIPO GRATK Treaty 2024",
                        "Nagoya Protocol",
                        "TRIPS Art 27",
                        "US FDA Guidance",
                    ],
                )
            elif mode in ["DUAL", "BOTH", "COMPARE"]:
                return RoutingDecision(
                    selected_track=JurisdictionTrack.DUAL_COMPARISON,
                    active_jurisdictions=["IN", "INT"],
                    confidence=1.0,
                    routing_rationale="User enabled Dual Comparison mode to evaluate domestic compliance against global regimes.",
                    applicable_treaties_and_statutes=[
                        "Patents Act 1970",
                        "BDA 2023",
                        "WIPO GRATK",
                        "Nagoya Protocol",
                    ],
                )

        # 2. Dynamic heuristic inspection from query text
        text = query.strip()
        has_intl_general = self._has_match(self.intl_general_patterns, text)
        has_us = self._has_match(self.us_market_patterns, text)
        has_eu = self._has_match(self.eu_market_patterns, text)
        has_india = self._has_match(self.india_patterns, text)

        detected_markets = []
        if has_us:
            detected_markets.append("United States (US FDA)")
        if has_eu:
            detected_markets.append("European Union (EMA)")
        if has_intl_general:
            detected_markets.append("Multilateral (WIPO / PCT / Nagoya)")

        # Case A: Dual comparison trigger (Mentions both domestic and cross-border elements)
        if (has_intl_general or has_us or has_eu) and has_india:
            return RoutingDecision(
                selected_track=JurisdictionTrack.DUAL_COMPARISON,
                active_jurisdictions=["IN", "INT"],
                confidence=0.92,
                routing_rationale="Query contains both domestic Indian statutory hooks and international export/treaty terminology.",
                target_export_markets=detected_markets,
                applicable_treaties_and_statutes=[
                    "Patents Act (S. 3)",
                    "NBA Form III",
                    "WIPO GRATK (Art. 3)",
                    "Target Market Regs",
                ],
            )

        # Case B: Clear International / Export intent
        if has_intl_general or has_us or has_eu:
            return RoutingDecision(
                selected_track=JurisdictionTrack.INTERNATIONAL,
                active_jurisdictions=["INT"],
                confidence=0.90,
                routing_rationale="Query is directed toward international filing, foreign markets, or cross-border disclosure treaties.",
                target_export_markets=detected_markets,
                applicable_treaties_and_statutes=[
                    "WIPO GRATK 2024",
                    "Nagoya Protocol",
                    "TRIPS",
                    "US FDA / EMA Guidelines",
                ],
            )

        # Case C: Default to Domestic India Track
        return RoutingDecision(
            selected_track=JurisdictionTrack.INDIA,
            active_jurisdictions=["IN"],
            confidence=0.85,
            routing_rationale="Defaulting to Domestic India jurisdiction (no foreign market or treaty references detected).",
            target_export_markets=[],
            applicable_treaties_and_statutes=[
                "Patents Act 1970",
                "Biological Diversity Act 2002/2023",
                "FSSAI",
                "D&C Act",
            ],
        )


# -------------------------------------------------------------
# Module Self-Test
# -------------------------------------------------------------
if __name__ == "__main__":
    router = JurisdictionRouter()

    # Test 1: User Query with Domestic Intent
    q1 = "How do I file Form 27 and avoid Section 3(p) objections for my Chyawanprash?"
    res1 = router.route(q1)
    print("=== TEST 1: Domestic India Query ===")
    print(f"Query: '{q1}'")
    print(
        f"Track: {res1.selected_track.value} | Active Jurisdictions: {res1.active_jurisdictions}"
    )
    print(f"Rationale: {res1.routing_rationale}")

    # Test 2: User Query with International Intent
    q2 = "What are the disclosure requirements under the new 2024 WIPO GRATK treaty for genetic resources?"
    res2 = router.route(q2)
    print("\n=== TEST 2: International Treaty Query ===")
    print(f"Query: '{q2}'")
    print(
        f"Track: {res2.selected_track.value} | Active Jurisdictions: {res2.active_jurisdictions}"
    )
    print(f"Markets: {res2.target_export_markets}")

    # Test 3: Dual-Jurisdiction Query (Exporting from India to US)
    q3 = "If I have an AYUSH license in India, can I sell this formulation as a botanical drug in the US with FDA approval?"
    res3 = router.route(q3)
    print("\n=== TEST 3: Cross-Border / Dual Query ===")
    print(f"Query: '{q3}'")
    print(
        f"Track: {res3.selected_track.value} | Active Jurisdictions: {res3.active_jurisdictions}"
    )
    print(f"Markets: {res3.target_export_markets}")

    # Test 4: Explicit UI Toggle Override (Forces 'INT' even on Indian text)
    q4 = "What are the patent rules for herbal extracts?"
    res4 = router.route(q4, forced_override="INT")
    print("\n=== TEST 4: Explicit UI Override ('INT') ===")
    print(
        f"Track: {res4.selected_track.value} | Active Jurisdictions: {res4.active_jurisdictions}"
    )
    print(f"Rationale: {res4.routing_rationale}")
