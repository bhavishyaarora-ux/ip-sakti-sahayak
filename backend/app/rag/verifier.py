import re
from typing import Dict, Any, List, Tuple


class DPDPGuard:
    """
    Enforces compliance with the Digital Personal Data Protection (DPDP) Act, 2023.
    Redacts personal identifiers, commercial manufacturing premises, and trade-secret ratios.
    """

    def __init__(self):
        self.email_regex = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
        self.phone_regex = re.compile(r"(?:\+91[\-\s]?|91[\-\s]?|0)?[6-9]\d{9}\b")
        self.aadhaar_regex = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")
        self.pan_regex = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b")
        self.ratio_regex = re.compile(
            r"\b\d+(\.\d+)?\s*(%|percent|ratio|w/w|v/v)\b", re.IGNORECASE
        )
        # Masks commercial manufacturing facilities and 6-digit postal PIN codes
        self.location_regex = re.compile(
            r"\b(Plot\s*No\.?\s*\d+|Industrial\s*Area|MIDC|GIDC|RIICO|Phase\s*-[I|V|X\d]+|\b\d{6}\b)",
            re.IGNORECASE,
        )

    def sanitize(self, text: str) -> Tuple[str, List[str]]:
        redacted_log = []
        clean_text = text

        if self.email_regex.search(clean_text):
            clean_text = self.email_regex.sub("[REDACTED_EMAIL_DPDP]", clean_text)
            redacted_log.append("Email Address")

        if self.phone_regex.search(clean_text):
            clean_text = self.phone_regex.sub("[REDACTED_PHONE_DPDP]", clean_text)
            redacted_log.append("Indian Phone Number")

        if self.aadhaar_regex.search(clean_text):
            clean_text = self.aadhaar_regex.sub("[REDACTED_AADHAAR_DPDP]", clean_text)
            redacted_log.append("Aadhaar Identifier")

        if self.pan_regex.search(clean_text):
            clean_text = self.pan_regex.sub("[REDACTED_PAN_DPDP]", clean_text)
            redacted_log.append("PAN Card Number")

        if self.ratio_regex.search(clean_text):
            clean_text = self.ratio_regex.sub(
                "[REDACTED_PROPRIETARY_RATIO]", clean_text
            )
            redacted_log.append("Proprietary Formulation Ratio")

        if self.location_regex.search(clean_text):
            clean_text = self.location_regex.sub(
                "[REDACTED_MANUFACTURING_PREMISES]", clean_text
            )
            redacted_log.append("Commercial Premises / PIN")

        return clean_text, redacted_log


class GroundednessVerifier:
    """
    Computes groundedness by verifying that citations in synthesized outputs
    directly match statutory chunks retrieved from the vector index.
    """

    def verify(
        self, response_text: str, retrieved_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not retrieved_chunks:
            return {
                "groundedness_score": 0.50,
                "hallucination_risk": "MEDIUM",
                "verified_citations": [],
                "unverified_citations": [],
            }

        valid_anchors = {c.get("citation_anchor", "") for c in retrieved_chunks}
        found_citations = re.findall(r"\[(.*?)\]", response_text)

        verified = [
            c for c in found_citations if any(anchor in c for anchor in valid_anchors)
        ]
        unverified = [
            c
            for c in found_citations
            if not any(anchor in c for anchor in valid_anchors)
        ]

        ratio = len(verified) / max(1, len(found_citations))
        risk = "LOW" if ratio >= 0.8 else ("MEDIUM" if ratio >= 0.5 else "HIGH")

        return {
            "groundedness_score": round(ratio, 2),
            "hallucination_risk": risk,
            "verified_citations": verified,
            "unverified_citations": unverified,
        }


if __name__ == "__main__":
    dpdp = DPDPGuard()
    verifier = GroundednessVerifier()

    sample_query = "My email is test@ayush.org and phone is +919876543210. I have a 25% w/w Curcumin extract."
    clean, tags = dpdp.sanitize(sample_query)
    print("=== DPDP SANITIZATION TEST ===")
    print("Original:", sample_query)
    print("Sanitized:", clean)
    print("Redacted Entities:", tags)

    sample_response = "As per [Patents Act 1970, Section 3(p)] and [Invented Law 2099], classical formulas are barred."
    mock_chunks = [{"citation_anchor": "Patents Act 1970, Section 3(p)"}]
    v_report = verifier.verify(sample_response, mock_chunks)
    print("\n=== GROUNDEDNESS VERIFIER TEST ===")
    print("Report:", v_report)
