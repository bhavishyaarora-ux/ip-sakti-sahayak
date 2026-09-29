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
    target_agents: List[str] = Field(
        default_factory=list,
        description="Sub-agents to trigger in LangGraph: 'ip_agent', 'abs_agent', 'export_agent'",
    )
    confidence: float
    routing_rationale: str
    target_export_markets: List[str] = Field(default_factory=list)
    applicable_treaties_and_statutes: List[str] = Field(default_factory=list)


class JurisdictionRouter:
    """
    Directs legal queries to isolated jurisdictional pipelines to prevent
    statutory conflation between Indian acts and international regimes, while
    dispatching execution to specialized sub-agents.
    """

    def __init__(self):
        # 1. Lexical pattern banks for international / export cues
        self.intl_general_patterns = [
            r"\b(international|abroad|global|foreign|cross-border|export|exporting|overseas)\b",
            r"\b(wipo|gratk|pct|patent cooperation treaty|madrid|hague|trips|nagoya|cbd)\b",
            r"\b(mandatory disclosure|country of origin|traditional knowledge digital library abroad)\b",
        ]
        self.us_market_patterns = [
            r"\b(us\b|usa|united states|fda|botanical drug|dshea|ind\b|nda\b|21 cfr|gras)\b"
        ]
        self.eu_market_patterns = [
            r"\b(eu\b|europe|european union|ema|thmpd|directive 2004/24/ec|novel food)\b"
        ]

        # 2. Lexical pattern banks for domestic Indian cues
        self.india_patterns = [
            r"\b(india|indian|domestic|inpass|ipo\b|delhi|mumbai|chennai|kolkata)\b",
            r"\b(patents act 1970|section 3\(p\)|section 3\(e\)|section 3\(d\)|rule 131|form 27|form 1|form 2)\b",
            r"\b(nba\b|sbb\b|bmc\b|national biodiversity authority|state biodiversity board)\b",
            r"\b(ayush|ccras|pcimh|tkdl|first schedule|charaka|sushruta|bhavaprakasha|fssai|ayurveda aahar)\b",
            r"\b(drugs and cosmetics act|magic remedies|cosmetics rules 2020|ppvfr|plant variety)\b",
        ]

        # 3. Lexical pattern banks for sub-agent specialization
        self.abs_patterns = [
            r"\b(biodiversity|bda|nba|sbb|bmc|access and benefit sharing|abs|biological resource)\b",
            r"\b(raw herb|forest produce|wild harvest|cultivator|tribal|folk knowledge|local community)\b",
            r"\b(form i|form iii|section 6|section 7|commercial utilization|benefit sharing fee)\b",
            r"\b(vaidya exemption|codified text exemption)\b",
        ]

        self.ip_patterns = [
            r"\b(patent|patentable|prior art|novelty|inventive step|synergy|synergistic|mere admixture)\b",
            r"\b(trademark|trade mark|brand name|logo|tm-a|form tm-a|class 5|class 3|class 30)\b",
            r"\b(geographical indication|gi tag|design|industrial design|trade secret|proprietary recipe)\b",
            r"\b(section 3\(p\)|section 3\(e\)|section 3\(d\)|section 2\(1\)\(j\)|process patent|product patent)\b",
            r"\b(plant variety|breeder right|ppvfr)\b",
        ]

    def _has_match(self, patterns: List[str], text: str) -> bool:
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    def _detect_sub_agents(
        self, text: str, selected_track: JurisdictionTrack
    ) -> List[str]:
        """
        Determines which specialized worker agents must be invoked.
        """
        agents = set()

        has_ip = self._has_match(self.ip_patterns, text)
        has_abs = self._has_match(self.abs_patterns, text)
        has_intl = (
            selected_track
            in [JurisdictionTrack.INTERNATIONAL, JurisdictionTrack.DUAL_COMPARISON]
            or self._has_match(self.intl_general_patterns, text)
            or self._has_match(self.us_market_patterns, text)
            or self._has_match(self.eu_market_patterns, text)
        )

        if has_ip:
            agents.add("ip_agent")
        if has_abs:
            agents.add("abs_agent")
        if has_intl:
            agents.add("export_agent")

        # Fallback defaults:
        # If no specific domain hook is detected, default to IP agent for domestic,
        # or Export agent for international tracks.
        if not agents:
            if selected_track == JurisdictionTrack.INTERNATIONAL:
                agents.add("export_agent")
            elif selected_track == JurisdictionTrack.DUAL_COMPARISON:
                agents.update(["ip_agent", "export_agent"])
            else:
                agents.add("ip_agent")

        return sorted(list(agents))

    def route(
        self, query: str, forced_override: Optional[str] = None
    ) -> RoutingDecision:
        """
        Determines the jurisdictional pipeline and dispatches required sub-agents.
        :param query: Natural language user query.
        :param forced_override: Manual UI toggle ('IN', 'INT', or 'DUAL').
        """
        text = query.strip()

        # -------------------------------------------------------------
        # 1. Handle Explicit Manual Override from UI Switch
        # -------------------------------------------------------------
        if forced_override:
            mode = forced_override.strip().upper()
            if mode in ["IN", "INDIA"]:
                track = JurisdictionTrack.INDIA
                return RoutingDecision(
                    selected_track=track,
                    active_jurisdictions=["IN"],
                    target_agents=self._detect_sub_agents(text, track),
                    confidence=1.0,
                    routing_rationale="User explicitly locked jurisdiction to India via interface toggle.",
                    applicable_treaties_and_statutes=[
                        "Patents Act 1970 (Amended 2024)",
                        "Biological Diversity Act 2002/2023 & 2024 Rules",
                        "Drugs and Cosmetics Act 1940 (Chapter IVA)",
                        "Trade Marks Act 1999",
                    ],
                )
            elif mode in ["INT", "INTERNATIONAL"]:
                track = JurisdictionTrack.INTERNATIONAL
                return RoutingDecision(
                    selected_track=track,
                    active_jurisdictions=["INT"],
                    target_agents=self._detect_sub_agents(text, track),
                    confidence=1.0,
                    routing_rationale="User explicitly locked jurisdiction to International via interface toggle.",
                    applicable_treaties_and_statutes=[
                        "WIPO GRATK Treaty 2024 (Art. 3 Mandatory Disclosure)",
                        "Nagoya Protocol on Access and Benefit Sharing",
                        "TRIPS Agreement Art 27",
                        "US FDA Botanical Guidance / EU THMPD",
                    ],
                )
            elif mode in ["DUAL", "BOTH", "COMPARE"]:
                track = JurisdictionTrack.DUAL_COMPARISON
                return RoutingDecision(
                    selected_track=track,
                    active_jurisdictions=["IN", "INT"],
                    target_agents=self._detect_sub_agents(text, track),
                    confidence=1.0,
                    routing_rationale="User enabled Dual Comparison mode to evaluate domestic compliance against global regimes.",
                    applicable_treaties_and_statutes=[
                        "Patents Act 1970 (Sec. 3p/3e)",
                        "BDA 2023 (Sec. 6 NBA Form III)",
                        "WIPO GRATK Treaty 2024",
                        "Nagoya Protocol",
                    ],
                )

        # -------------------------------------------------------------
        # 2. Dynamic Heuristic Inspection from Query Text
        # -------------------------------------------------------------
        has_intl_general = self._has_match(self.intl_general_patterns, text)
        has_us = self._has_match(self.us_market_patterns, text)
        has_eu = self._has_match(self.eu_market_patterns, text)
        has_india = self._has_match(self.india_patterns, text)

        detected_markets = []
        if has_us:
            detected_markets.append("United States (US FDA / DSHEA)")
        if has_eu:
            detected_markets.append("European Union (EMA / THMPD)")
        if has_intl_general:
            detected_markets.append("Multilateral (WIPO / PCT / Nagoya Protocol)")

        # Case A: Dual comparison trigger (Both domestic & cross-border elements present)
        if (has_intl_general or has_us or has_eu) and has_india:
            track = JurisdictionTrack.DUAL_COMPARISON
            return RoutingDecision(
                selected_track=track,
                active_jurisdictions=["IN", "INT"],
                target_agents=self._detect_sub_agents(text, track),
                confidence=0.92,
                routing_rationale="Query contains both domestic Indian statutory hooks and international export/treaty terminology.",
                target_export_markets=detected_markets,
                applicable_treaties_and_statutes=[
                    "Patents Act (Sec. 3p/3e)",
                    "Biological Diversity Act 2023 (Sec. 6 Approval)",
                    "WIPO GRATK (Art. 3 Origin Disclosure)",
                    "Target Market Regs (US FDA / EMA)",
                ],
            )

        # Case B: Clear International / Export intent
        if has_intl_general or has_us or has_eu:
            track = JurisdictionTrack.INTERNATIONAL
            return RoutingDecision(
                selected_track=track,
                active_jurisdictions=["INT"],
                target_agents=self._detect_sub_agents(text, track),
                confidence=0.90,
                routing_rationale="Query is directed toward international filing, foreign markets, or cross-border disclosure treaties.",
                target_export_markets=detected_markets,
                applicable_treaties_and_statutes=[
                    "WIPO GRATK 2024",
                    "Nagoya Protocol",
                    "TRIPS Agreement",
                    "US FDA Botanical Guidance / EU THMPD",
                ],
            )

        # Case C: Default to Domestic India Track
        track = JurisdictionTrack.INDIA
        return RoutingDecision(
            selected_track=track,
            active_jurisdictions=["IN"],
            target_agents=self._detect_sub_agents(text, track),
            confidence=0.85,
            routing_rationale="Defaulting to Domestic India jurisdiction (no foreign market or cross-border treaty cues detected).",
            target_export_markets=[],
            applicable_treaties_and_statutes=[
                "Patents Act 1970 (Amended 2024)",
                "Biological Diversity Act 2002/2023",
                "FSSAI Ayurveda Aahara 2022",
                "Drugs & Cosmetics Act 1940",
            ],
        )


def determine_sub_agents(query: str, jurisdiction: Optional[str] = None) -> List[str]:
    """
    Convenience helper function for LangGraph state machine conditional edges.
    """
    router = JurisdictionRouter()
    decision = router.route(query, forced_override=jurisdiction)
    return decision.target_agents


# -------------------------------------------------------------
# Module Self-Test
# -------------------------------------------------------------
if __name__ == "__main__":
    router = JurisdictionRouter()

    # Test 1: Domestic IP Query
    q1 = "How do I file Form 27 and avoid Section 3(p) objections for my Chyawanprash?"
    res1 = router.route(q1)
    print("=== TEST 1: Domestic India IP Query ===")
    print(
        f"Track: {res1.selected_track.value} | Jurisdictions: {res1.active_jurisdictions}"
    )
    print(f"Target Agents: {res1.target_agents}")
    print(f"Rationale: {res1.routing_rationale}\n")

    # Test 2: Domestic Bio-resource / ABS Query
    q2 = "I am sourcing wild Guggal from local forests in Rajasthan. Do I need NBA Form I or SBB intimation?"
    res2 = router.route(q2)
    print("=== TEST 2: Domestic ABS Query ===")
    print(
        f"Track: {res2.selected_track.value} | Jurisdictions: {res2.active_jurisdictions}"
    )
    print(f"Target Agents: {res2.target_agents}")
    print(f"Rationale: {res2.routing_rationale}\n")

    # Test 3: Multi-Domain Query (Both IP and ABS)
    q3 = "Can I patent my novel extract of Ashwagandha and what permission do I need from the Biodiversity Board?"
    res3 = router.route(q3)
    print("=== TEST 3: Domestic Dual Domain (IP + ABS) ===")
    print(
        f"Track: {res3.selected_track.value} | Jurisdictions: {res3.active_jurisdictions}"
    )
    print(f"Target Agents: {res3.target_agents}")
    print(f"Rationale: {res3.routing_rationale}\n")

    # Test 4: International Treaty Query
    q4 = "What are the disclosure requirements under the new 2024 WIPO GRATK treaty for genetic resources?"
    res4 = router.route(q4)
    print("=== TEST 4: International Treaty Query ===")
    print(
        f"Track: {res4.selected_track.value} | Jurisdictions: {res4.active_jurisdictions}"
    )
    print(f"Target Agents: {res4.target_agents}")
    print(f"Markets: {res4.target_export_markets}\n")

    # Test 5: Cross-Border Dual Query
    q5 = "If I have an AYUSH license in India, can I sell this formulation as a botanical drug in the US with FDA approval?"
    res5 = router.route(q5)
    print("=== TEST 5: Cross-Border / Dual Query ===")
    print(
        f"Track: {res5.selected_track.value} | Jurisdictions: {res5.active_jurisdictions}"
    )
    print(f"Target Agents: {res5.target_agents}")
    print(f"Markets: {res5.target_export_markets}\n")

    # Test 6: Explicit UI Toggle Override
    q6 = "What are the patent rules for herbal extracts?"
    res6 = router.route(q6, forced_override="INT")
    print("=== TEST 6: Explicit UI Override ('INT') ===")
    print(
        f"Track: {res6.selected_track.value} | Jurisdictions: {res6.active_jurisdictions}"
    )
    print(f"Target Agents: {res6.target_agents}")
    print(f"Rationale: {res6.routing_rationale}")
