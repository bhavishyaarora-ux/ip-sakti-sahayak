import os
from pathlib import Path

# Base corpus directory
BASE_DIR = Path("corpus")

CORPUS_FILES = {
    # -------------------------------------------------------------
    # 1. PATENTS REGIME
    # -------------------------------------------------------------
    "patents/patents_act_key_sections.md": """---
doc_id: IN-PAT-ACT-1970-CORE
jurisdiction: IN
regime: Patent
act_name: The Patents Act, 1970 (as amended)
amendment_rules: Patents Rules, 2024
citation_anchor: Patents Act 1970
category: Statutory Exclusion
---

# The Patents Act, 1970: Key Provisions for AYUSH Inventions

## Section 2(1)(j) - Definition of "Invention"
"Invention" means a new product or process involving an inventive step and capable of industrial application.
- For Ayurvedic compounds, industrial application and novel chemical/therapeutic profile must be established beyond natural state occurrence.

## Section 3(d) - Incremental Inventions & Derivatives
"The mere discovery of a new form of a known substance which does not result in the enhancement of the known efficacy of that substance or the mere discovery of any new property or new use for a known substance or of the mere use of a known process, machine or apparatus unless such known process results in a new product or employs at least one new reactant."
- *Explanation*: Salts, esters, ethers, polymorphs, metabolites, pure form, particle size, isomers, complexes, and other derivatives of known substances shall be considered to be the same substance, unless they differ significantly in properties with regard to efficacy.
- *AYUSH Relevance*: Extracting a known active fraction (e.g., withanolides from Ashwagandha) must prove statistically significant *therapeutic enhancement* over whole-plant extract to overcome Section 3(d).

## Section 3(e) - Admixture Exclusion
"A substance obtained by a mere admixture resulting only in the aggregation of the properties of the components thereof or a process for producing such substance."
- *AYUSH Relevance*: Combining known classical herbs (e.g., Curcumin + Piperine) is barred unless synergistic interaction (super-additive efficacy) is scientifically proven via comparative biological assays or clinical trials.

## Section 3(i) - Method of Treatment Bar
"Any process for the medicinal, surgical, curative, prophylactic diagnostic, therapeutic or other treatment of human beings or any process for a similar treatment of animals to render them free of disease or to increase their economic value or that of their products."
- *AYUSH Relevance*: Ayurvedic therapeutic administration protocols, dosage regimens, or Panchakarma therapeutic processes cannot be patented. Only product formulations or specific novel manufacturing processes are patent-eligible.

## Section 3(p) - Traditional Knowledge Exclusion Bar
"An invention which in effect, is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components."
- *Statutory Impact*: Absolute statutory bar for classical formulations documented in First Schedule texts. Defended by the Indian Patent Office and CSIR via TKDL citations.
""",
    "patents/patents_rules_2024_forms.md": """---
doc_id: IN-PAT-RULES-2024-PROC
jurisdiction: IN
regime: Patent Procedure
act_name: Patents Rules, 2003 (Amended up to Patents Rules, 2024)
citation_anchor: Patents Rules 2024
category: Procedural Compliance
---

# Patent Office Procedures & Filing Rules (2024 Updates)

## Form 1: Application for Grant of Patent
- *Mandatory Disclosure*: Requires applicants to declare whether the invention uses biological material from India.
- If YES: Requires mandatory declaration of NBA (National Biodiversity Authority) approval under Section 6 of Biological Diversity Act.

## Form 18A: Expedited Examination of Applications
- Available for AYUSH startups recognized under DPIIT, small entities/MSMEs, female applicants, and government-funded research institutes.
- Reduces examination turnaround from 36–48 months to under 12 months.

## Rule 131 & Form 27: Statement of Working of Patents (2024 Amendment)
- *Major 2024 Change*: Form 27 is now required to be submitted **once every three financial years** (starting from the financial year immediately succeeding the grant year), rather than annually.
- The Controller may condone delays or non-filing upon petition under Rule 137.
- Patentee must state whether the patent is worked commercially in India and provide broad revenue justification without disclosing sensitive pricing secrets.
""",
    # -------------------------------------------------------------
    # 2. BIODIVERSITY & ABS REGIME
    # -------------------------------------------------------------
    "biodiversity/bda_2002_2023_amendment.md": """---
doc_id: IN-BIO-BDA-2002-2023
jurisdiction: IN
regime: Access and Benefit Sharing (ABS)
act_name: Biological Diversity Act, 2002 (as amended by BD Amendment Act, 2023)
subordinate_rules: Biological Diversity Rules, 2024
citation_anchor: Biological Diversity Act 2002/2023
category: Sovereign Bio-Resource Mandates
---

# Biological Diversity Act (2002 / 2023 Amendment)

## Section 3: Approval of NBA for Foreign Entities
Non-Indian citizens, non-residents, and companies registered in India with foreign equity/management participation must obtain prior approval from the National Biodiversity Authority (NBA) before obtaining any biological resource occurring in India or associated knowledge for research, commercial utilization, or bio-survey.

## Section 6: Prior NBA Approval for Intellectual Property Rights
- **Section 6(1)**: No person shall apply for any intellectual property right, in or outside India, for any invention based on any research or information on a biological resource obtained from India, without obtaining previous approval of the National Biodiversity Authority.
- *Timing (2023 Amendment)*: For patent applications, NBA approval must be obtained **before the actual grant of the patent**, not at the date of initial filing.
- The NBA may impose a benefit-sharing fee or royalty mechanism as a condition of granting approval.

## Section 7 & Section 40: Commercial Utilization & AYUSH Exemptions
- **Section 7**: Indian citizens and domestic companies must give prior intimation to the State Biodiversity Board (SBB) before accessing resources for commercial utilization.
- **2023/2024 Amendment Exemption**: Local Vaidyas, registered AYUSH practitioners, and codified traditional knowledge users are explicitly exempt from prior intimation and benefit-sharing payments for practicing medicine.
- Cultivated medicinal plants are exempted from ABS, provided growers obtain a Certificate of Origin from local Biodiversity Management Committees (BMCs) or designated authorities.
- **Section 40 (Normally Traded Commodities - NTC)**: The Central Government exempts listed agricultural items from the Act's provisions when traded strictly as commodities (e.g., Ginger, Black Pepper traded purely as food).
""",
    "biodiversity/nba_forms_and_procedures.md": """---
doc_id: IN-BIO-NBA-FORMS-2024
jurisdiction: IN
regime: NBA Procedural Compliance
act_name: Biological Diversity Rules, 2004 / 2024
citation_anchor: BD Rules Forms
category: ABS Application Forms
---

# National Biodiversity Authority (NBA) Statutory Forms

## Form I: Application for Access to Biological Resources
- *Applicant*: Non-Indian citizens, foreign companies, or Indian companies with foreign shareholding.
- *Purpose*: Commercial utilization, bio-survey, or bio-utilization.
- *Fee & SLA*: Prescribed fee with NBA evaluation within 6 months.

## Form II: Transfer of Results of Research
- *Trigger*: Transferring research results relating to biological resources occurring in India to non-citizens or foreign entities.
- *Mandate*: Requires approval before executing material transfer agreements (MTAs).

## Form III: Application for Seeking Prior Approval for IPR Application
- *Crucial AYUSH Hook*: Submitted by any researcher or company seeking a patent on an Ayurvedic formulation or biological derivative sourced in India.
- *Submission Window*: After provisional/complete filing at Patent Office, but strictly before the issuance of the patent grant letter.
- *Benefit-Sharing Formula*: 0.1% to 0.5% of annual gross ex-factory sales minus taxes, or 3.0% to 5.0% of upfront licensing fees.

## Form IV: Third-Party Transfer
- Required before transferring accessed biological resources or associated traditional knowledge to another third-party commercial firm.
""",
    # -------------------------------------------------------------
    # 3. REGULATORY, DRUGS & FOOD
    # -------------------------------------------------------------
    "regulatory/drugs_and_cosmetics_chapter_iva.md": """---
doc_id: IN-REG-DCA-1940-CH4A
jurisdiction: IN
regime: Drug Regulatory & Licensing
act_name: Drugs and Cosmetics Act, 1940 & Rules, 1945
citation_anchor: Drugs & Cosmetics Act 1940 Chapter IV-A
category: ASU Drug Classification & Manufacturing
---

# Drugs and Cosmetics Act, 1940 (Chapter IV-A) & Rule 158B

## Section 3(a) - Ayurvedic, Siddha or Unani (ASU) Drug Definition
Medicines intended for internal or external use in the diagnosis, treatment, mitigation or prevention of disease in human beings or animals, manufactured strictly in accordance with formulae described in the authoritative books specified in the **First Schedule**.

## Section 3(h) - Patent or Proprietary (P&P) Medicine
In relation to ASU systems, a drug that is not solely a classical text formula, but contains ingredients mentioned in the First Schedule books, manufactured according to modern or altered formulations.

## Rule 158B: Licensing Criteria for ASU Drugs
1. **Classical Drugs**: Formulated strictly according to First Schedule texts.
   - *Evidence Required*: Proof of authoritative textual reference. No safety/efficacy trial data required.
2. **Patent & Proprietary (P&P) Formulation Categories**:
   - *Same Ingredients, New Ratio/Form*: Requires published safety data and pilot trial for indications.
   - *New ASU Formulation*: Requires acute oral toxicity study reports and documented clinical trial efficacy evidence prior to state SLA license approval.
3. **Traceability (Rule 158B Sub-rule VII updates)**:
   - Mandatory Specific Product Code (S.P.C.) format on labels linking state code, license type (D/E), and unique batch registration.
""",
    "regulatory/phytopharmaceuticals_2015.md": """---
doc_id: IN-REG-PHYTO-2015
jurisdiction: IN
regime: Phytopharmaceutical Regulation
act_name: Drugs and Cosmetics Rules, 1945 (Amendment 2015, GSR 918(E))
citation_anchor: CDSCO Phytopharmaceutical Guidelines 2015
category: New Herbal Drug Pathways
---

# Phytopharmaceutical Drug Regulatory Architecture

## Definition (Rule 2(eb))
A "Phytopharmaceutical drug" is a purified, standardized fraction with defined minimum quantitative markers (containing not less than four bioactive or analytical marker compounds) derived from an extract of a medicinal plant part, intended for internal or external use on humans or animals for diagnosis, treatment, or prevention of disease.
- Whole crude plant powders or simple traditional aqueous decoctions do not qualify.

## Licensing & Approval Gateway (Rule 122DA & 122E)
- Regulated by the Central Drugs Standard Control Organization (CDSCO / DCGI), not state AYUSH licensing authorities.
- Requires Phase I, II, and III clinical trials similar to synthetic New Chemical Entities (NCEs).
- Pre-clinical data must document stability studies, chemical fingerprints (HPLC/LC-MS), and heavy metal/pesticide limits.
- **High IP Alignment**: High patentability potential for extraction isolation methods, active marker ratios, and specific therapeutic claims.
""",
    "regulatory/fssai_ayurveda_aahara_2022.md": """---
doc_id: IN-REG-FSSAI-AA-2022
jurisdiction: IN
regime: Food / Nutraceutical Compliance
act_name: Food Safety and Standards (Ayurveda Aahara) Regulations, 2022
citation_anchor: FSSAI Ayurveda Aahara 2022
category: Non-Medicinal Food Supplements
---

# FSSAI Ayurveda Aahara Regulations, 2022

## Scope and Legal Boundary
- Applies to food prepared in accordance with the recipes, ingredients, and processes described in the authoritative books of Ayurveda listed under Schedule A of the regulations.
- Products cannot claim therapeutic cures or claim to diagnose or treat specific diseases (preventing collision with the Drugs and Magic Remedies Act, 1954).

## Critical Formulation Constraints
- Prohibits the addition of synthetic vitamins, minerals, amino acids, or purified synthetic bio-actives.
- Permissible botanicals must strictly adhere to positive list monographs.
- Mandatory display of the official **Ayurveda Aahara logo** alongside FSSAI license numbers.
- IP Protection is primarily restricted to Trade Marks, Packaging Trade Dress, and Proprietary Manufacturing Processes; formulation recipes are usually non-patentable under Section 3(p).
""",
    # -------------------------------------------------------------
    # 4. INTERNATIONAL TREATIES & EXPORT
    # -------------------------------------------------------------
    "international/wipo_gratk_treaty_2024.md": """---
doc_id: INT-WIPO-GRATK-2024
jurisdiction: INT
regime: International IP & Traditional Knowledge
act_name: WIPO Treaty on Intellectual Property, Genetic Resources and Associated Traditional Knowledge (2024)
citation_anchor: WIPO GRATK Treaty 2024
category: International Patent Disclosure
---

# WIPO GRATK Treaty (Adopted May 2024)

## Article 3: Mandatory Patent Disclosure Obligation
- **Article 3.1 (Genetic Resources)**: Where the claimed invention in a patent application is *based on* genetic resources, each Contracting Party shall require applicants to disclose the country of origin of the genetic resources (or source, if country of origin is unknown).
- **Article 3.2 (Traditional Knowledge)**: Where the claimed invention in a patent application is *based on* traditional knowledge associated with genetic resources, applicants must disclose the Indigenous Peoples or local community that provided the knowledge (or source, if community is unknown).
- **Article 3.3 (Declaration of Absence)**: If information is unknown, the applicant must submit a formal declaration to that effect.

## Article 5: Non-Revocation Safeguards
- A granted patent cannot be revoked, invalidated, or rendered unenforceable solely on the basis of a failure to disclose, **unless fraudulent intent is proven** under applicable national patent laws.
- Contracting Parties must provide an opportunity to rectify omissions prior to penal actions.
""",
    "international/trips_and_nagoya_protocol.md": """---
doc_id: INT-TRIPS-NAGOYA-COMBINED
jurisdiction: INT
regime: Multilateral Trade & Bio-Sovereignty
act_name: WTO TRIPS Agreement & Nagoya Protocol on ABS
citation_anchor: TRIPS Art. 27 / Nagoya Protocol
category: Cross-Border Trade & Sourcing
---

# Multilateral IP & Biodiversity Regimes

## WTO TRIPS Agreement: Article 27
- **Article 27.1**: Patents shall be available for any inventions, whether products or processes, in all fields of technology, provided they are new, involve an inventive step, and are capable of industrial application.
- **Article 27.2**: Members may exclude inventions from patentability to protect *ordre public* or morality, including to protect human, animal, or plant life or health.
- **Article 27.3(b)**: Members may exclude plants and animals (other than micro-organisms) and essentially biological processes for the production of plants or animals. Members must provide for the protection of plant varieties either by patents or by an effective *sui generis* system (e.g., India's PPV&FR Act, 2001).

## The Nagoya Protocol on Access and Benefit-Sharing (ABS)
- Operates under the Convention on Biological Diversity (CBD).
- **Prior Informed Consent (PIC)**: Mandates approval from provider state authorities before harvesting or collecting indigenous genetic resources.
- **Mutually Agreed Terms (MAT)**: Commercial contracts establishing commercial benefit-sharing arrangements (royalties, technology transfers, joint research) between foreign commercial developers and native custodians.
""",
    "international/us_fda_botanical_guidance.md": """---
doc_id: INT-USFDA-BOTANICAL-2016
jurisdiction: INT
regime: US Drug Market Access
act_name: FDA Guidance for Industry: Botanical Drug Development (Dec 2016)
citation_anchor: US FDA Botanical Guidance 2016
category: Export Drug Approval Standards
---

# US FDA Botanical Drug Guidance

## Definition of Botanical Drug Product
A product consisting of vegetable materials, which may include plant materials, algae, macroscopic fungi, or combinations thereof. It may be available as a solution, powder, tablet, capsule, or spray. Highly purified substances (e.g., Paclitaxel) or fermentation-derived materials are not botanical drugs.

## Dual Regulatory Pathways for Ayurvedic Formulations in the US
1. **Dietary Supplement (DSHEA 1994)**:
   - Cannot claim to diagnose, cure, mitigate, treat, or prevent any disease.
   - May carry structure/function claims (e.g., "Supports joint health").
   - Does not require pre-market clinical efficacy proof, but requires GMP compliance (21 CFR Part 111).
2. **Prescription Botanical Drug (NDA / IND route)**:
   - Requires formal Investigational New Drug (IND) application and Phase 1-3 clinical trials.
   - Accepts historical human use data in India to satisfy initial Phase 1/Phase 2 safety requirements, easing early development costs.
   - *Batch Consistency Hurdle*: Because herbal raw material constitution varies seasonally, the applicant must establish multi-batch chemical fingerprints and raw material control from farm to formulation.
""",
}


def setup():
    print("Scaffolding IP-SAKTI Sahayak Golden Legal Corpus...")
    created_count = 0
    for relative_path, content in CORPUS_FILES.items():
        file_path = BASE_DIR / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        print(f" Created: {file_path}")
        created_count += 1

    print(
        f"\nCompleted! {created_count} curated legal source files successfully written to /{BASE_DIR}/"
    )


if __name__ == "__main__":
    setup()
