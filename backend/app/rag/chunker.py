import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any

# Dynamic path resolution to backend root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CORPUS_DIR = BASE_DIR / "corpus"

# Statutory compliance tag classification map
TAG_RULES = [
    (r"3\(p\)", "TK_Bar"),
    (r"3\(d\)", "Efficacy_Enhancement"),
    (r"3\(e\)", "Synergy_Admixture"),
    (r"3\(i\)", "Treatment_Method_Bar"),
    (r"Form\s+III", "NBA_IPR_Approval"),
    (r"Form\s+I\b", "NBA_Access_Approval"),
    (r"Form\s+27|Rule\s+131", "Working_Statement_Compliance"),
    (r"Rule\s+158B|Chapter\s+IV-A", "ASU_Licensing_Proof"),
    (r"Phytopharmaceutical|122E|122DA", "Phyto_CDSCO_Gateway"),
    (r"Ayurveda\s+Aahara|Schedule\s+A", "FSSAI_Food_Reg"),
    (r"GRATK|Article\s+3", "WIPO_Origin_Disclosure"),
    (r"Nagoya|PIC|MAT", "Nagoya_ABS_Sovereignty"),
    (r"Botanical\s+Drug|DSHEA", "USFDA_Market_Access"),
    (r"Section\s+40|Normally\s+Traded", "NTC_Exemption"),
    (r"Section\s+6|Section\s+7", "BDA_Mandatory_Intimation"),
]


def derive_compliance_tag(provision_text: str, content: str) -> str:
    combined = f"{provision_text} {content}"
    for pattern, tag in TAG_RULES:
        if re.search(pattern, combined, re.IGNORECASE):
            return tag
    return "General_Statutory_Provision"


def parse_frontmatter(raw_text: str) -> tuple[Dict[str, str], str]:
    """Extracts YAML frontmatter without requiring external pyyaml dependencies."""
    frontmatter = {}
    content = raw_text

    if raw_text.startswith("---"):
        parts = raw_text.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            content = parts[2].strip()
            for line in fm_text.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    frontmatter[key.strip()] = val.strip().strip('"').strip("'")

    return frontmatter, content


def extract_statutory_chunks(file_path: Path) -> List[Dict[str, Any]]:
    """Splits a legal markdown document along H2 (##) structural boundaries."""
    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    frontmatter, body = parse_frontmatter(raw_text)

    # Split by H2 markdown headers (e.g., ## Section 3(p) - Title)
    h2_pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    split_positions = [m.start() for m in h2_pattern.finditer(body)]

    if not split_positions:
        # Fallback: single chunk if no H2 sections exist
        return [
            {
                "chunk_id": f"{frontmatter.get('doc_id', file_path.stem)}_full",
                "content": body.strip(),
                "metadata": {
                    **frontmatter,
                    "provision": "Full Document",
                    "title": file_path.stem,
                    "compliance_tag": "Full_Statute",
                    "file_path": str(file_path.relative_to(BASE_DIR)),
                },
            }
        ]

    chunks = []
    # Capture any preamble before the first H2
    preamble = body[: split_positions[0]].strip()
    act_title_match = re.search(r"^#\s+(.+)$", preamble, re.MULTILINE)
    act_heading = (
        act_title_match.group(1).strip()
        if act_title_match
        else frontmatter.get("act_name", "")
    )

    for i, pos in enumerate(split_positions):
        end_pos = split_positions[i + 1] if i + 1 < len(split_positions) else len(body)
        section_raw = body[pos:end_pos].strip()

        lines = section_raw.splitlines()
        header_line = lines[0].replace("##", "").strip()
        section_body = "\n".join(lines[1:]).strip()

        # Parse provision identifier and title
        if "-" in header_line:
            provision_part, title_part = header_line.split("-", 1)
            provision = provision_part.strip()
            title = title_part.strip()
        elif ":" in header_line:
            provision_part, title_part = header_line.split(":", 1)
            provision = provision_part.strip()
            title = title_part.strip()
        else:
            provision = header_line
            title = header_line

        # Generate a clean statutory citation anchor
        base_anchor = frontmatter.get(
            "citation_anchor", frontmatter.get("act_name", "Statute")
        )
        citation_anchor = f"{base_anchor}, {provision}"

        # Clean slug for unique ID
        clean_slug = re.sub(r"[^a-zA-Z0-9]", "_", provision).strip("_")
        chunk_id = f"{frontmatter.get('doc_id', file_path.stem)}_{clean_slug}"
        compliance_tag = derive_compliance_tag(provision, section_body)

        # Context-rich content block for embedding
        rich_chunk_content = (
            f"Statute: {frontmatter.get('act_name', act_heading)}\n"
            f"Provision: {provision} ({title})\n"
            f"Jurisdiction: {frontmatter.get('jurisdiction', 'IN')} | Regime: {frontmatter.get('regime', 'General')}\n"
            f"Statutory Text & Rules:\n{section_body}"
        )

        chunks.append(
            {
                "chunk_id": chunk_id,
                "content": rich_chunk_content,
                "metadata": {
                    "doc_id": frontmatter.get("doc_id", "UNKNOWN"),
                    "jurisdiction": frontmatter.get("jurisdiction", "IN"),
                    "regime": frontmatter.get("regime", "General"),
                    "act_name": frontmatter.get("act_name", act_heading),
                    "provision": provision,
                    "title": title,
                    "compliance_tag": compliance_tag,
                    "citation_anchor": citation_anchor,
                    "source_file": str(file_path.relative_to(BASE_DIR)),
                },
            }
        )

    return chunks


def process_entire_corpus(corpus_root: Path = CORPUS_DIR) -> List[Dict[str, Any]]:
    """Crawls all categories in /corpus and structurally chunks all markdown files."""
    all_chunks = []
    for md_file in corpus_root.rglob("*.md"):
        chunks = extract_statutory_chunks(md_file)
        all_chunks.extend(chunks)
    return all_chunks


if __name__ == "__main__":
    print(f"Scanning legal corpus at: {CORPUS_DIR.resolve()}")
    chunks = process_entire_corpus()
    print(
        f"Generated {len(chunks)} structural statutory chunks across 4 legal regimes.\n"
    )

    # Print sample chunk for verification
    if chunks:
        sample = chunks[3]  # Likely Section 3(p) or Section 3(e)
        print("=== SAMPLE EXTRACTED CHUNK ===")
        print(f"Chunk ID       : {sample['chunk_id']}")
        print(f"Citation Anchor: {sample['metadata']['citation_anchor']}")
        print(f"Jurisdiction   : {sample['metadata']['jurisdiction']}")
        print(f"Compliance Tag : {sample['metadata']['compliance_tag']}")
        print(f"Content Preview:\n{sample['content'][:250]}...")
