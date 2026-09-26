import os
import re
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv

# Load credentials from backend/.env
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# Canonical Ayurvedic, botanical, and statutory tokens protected from translation corruption
PROTECTED_ENTITIES = [
    # Botanical Taxa & Common Names
    "Withania somnifera",
    "Ashwagandha",
    "Curcuma longa",
    "Curcumin",
    "Ocimum sanctum",
    "Tulsi",
    "Piper longum",
    "Pippali",
    "Triphala",
    "Phyllanthus emblica",
    "Amla",
    "Tinospora cordifolia",
    "Giloy",
    "Guduchi",
    "Bacopa monnieri",
    "Brahmi",
    "Commiphora mukul",
    "Guggulu",
    "Azadirachta indica",
    "Neem",
    "Terminalia arjuna",
    "Arjuna",
    # Classical Dosages & Galenical Forms
    "Kwatha",
    "Asava",
    "Arishta",
    "Bhasma",
    "Taila",
    "Ghrita",
    "Lehyam",
    "Vati",
    "Gutika",
    "Churna",
    "Rasayana",
    "Avaleha",
    # Authoritative Texts
    "Charaka Samhita",
    "Sushruta Samhita",
    "Ashtanga Hridaya",
    "Sahasrayogam",
    "Bhavaprakasha",
    "Sharangadhara Samhita",
    "First Schedule",
    # Statutory Provisions & Regulatory Bodies
    "Section 3(p)",
    "Section 3(e)",
    "Section 3(d)",
    "Section 3(i)",
    "Section 2(1)(j)",
    "Rule 158B",
    "Rule 122E",
    "Rule 122DA",
    "Rule 131",
    "Form 27",
    "Form 18A",
    "Form 1",
    "Form I",
    "Form II",
    "Form III",
    "Form IV",
    "NBA",
    "SBB",
    "BMC",
    "TKDL",
    "WIPO GRATK Treaty",
    "Nagoya Protocol",
    "TRIPS Article 27",
    "Ayurveda Aahara",
    "FSSAI",
    "CDSCO",
]

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi (हिन्दी)",
    "ta": "Tamil (தமிழ்)",
    "te": "Telugu (తెలుగు)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "ml": "Malayalam (മലയാളം)",
    "mr": "Marathi (मराठी)",
    "bn": "Bengali (বাংলা)",
    "gu": "Gujarati (ગુજરાતી)",
}


class AyurvedicEntityShield:
    """Protects classical Sanskrit and statutory terminology from machine translation corruption."""

    def __init__(self, entities: List[str] = PROTECTED_ENTITIES):
        self.entities = sorted(entities, key=len, reverse=True)

    def mask(self, text: str) -> Tuple[str, Dict[str, str]]:
        masked_text = text
        token_map: Dict[str, str] = {}

        for idx, entity in enumerate(self.entities):
            pattern = re.compile(rf"\b{re.escape(entity)}\b", re.IGNORECASE)
            if pattern.search(masked_text):
                token = f"__AYUR_SHIELD_{idx}__"
                token_map[token] = entity
                masked_text = pattern.sub(token, masked_text)

        return masked_text, token_map

    def unmask(self, translated_text: str, token_map: Dict[str, str]) -> str:
        restored = translated_text
        for token, original in token_map.items():
            tolerant_pattern = re.compile(
                re.escape(token).replace(r"\_", r"[\s\_]*"), re.IGNORECASE
            )
            restored = tolerant_pattern.sub(original, restored)
        return restored


class BhashiniService:
    """
    Official Bhashini ULCA / Dhruva Translation Service with
    Ayurvedic Entity Shielding and graceful offline fallbacks.
    """

    def __init__(self):
        self.user_id = os.getenv("BHASHINI_USER_ID", "")
        self.ulca_api_key = os.getenv("BHASHINI_ULCA_API_KEY", "")
        self.inference_key = os.getenv("BHASHINI_INFERENCE_KEY", "")
        self.pipeline_id = os.getenv("BHASHINI_PIPELINE_ID", "64392f96daac500b55c543d7")
        self.config_url = (
            "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
        )
        self.shield = AyurvedicEntityShield()

    def translate(self, text: str, target_lang: str) -> str:
        if target_lang == "en" or not text.strip():
            return text

        # Step 1: Mask botanical and legal entities
        masked_text, token_map = self.shield.mask(text)

        # Step 2: Perform translation via live API or fallback
        raw_translation = self._call_bhashini_api(masked_text, target_lang)

        # Step 3: Unmask and restore canonical nomenclature
        return self.shield.unmask(raw_translation, token_map)

    def _call_bhashini_api(self, text: str, target_lang: str) -> str:
        if not self.user_id or not self.ulca_api_key:
            return self._local_fallback(text, target_lang)

        try:
            # 1. Pipeline Config Call (Fetch active model endpoint & service ID)
            config_headers = {
                "userID": self.user_id,
                "ulcaApiKey": self.ulca_api_key,
                "Content-Type": "application/json",
            }
            config_payload = {
                "pipelineTasks": [
                    {
                        "taskType": "translation",
                        "config": {
                            "language": {
                                "sourceLanguage": "en",
                                "targetLanguage": target_lang,
                            }
                        },
                    }
                ],
                "pipelineRequestConfig": {"pipelineId": self.pipeline_id},
            }

            cfg_res = requests.post(
                self.config_url, json=config_payload, headers=config_headers, timeout=6
            )

            if cfg_res.status_code != 200:
                return self._local_fallback(text, target_lang)

            cfg_data = cfg_res.json()
            callback_url = cfg_data["pipelineInferenceAPIEndPoint"]["callbackUrl"]
            inference_auth_key = cfg_data["pipelineInferenceAPIEndPoint"][
                "inferenceApiKey"
            ]["value"]
            service_id = cfg_data["pipelineResponseConfig"][0]["config"][0]["serviceId"]

            # 2. Pipeline Compute Call (Inference)
            compute_headers = {
                "Authorization": inference_auth_key,
                "Content-Type": "application/json",
            }
            compute_payload = {
                "pipelineTasks": [
                    {
                        "taskType": "translation",
                        "config": {
                            "language": {
                                "sourceLanguage": "en",
                                "targetLanguage": target_lang,
                            },
                            "serviceId": service_id,
                        },
                    }
                ],
                "inputData": {"input": [{"source": text}]},
            }

            compute_res = requests.post(
                callback_url, json=compute_payload, headers=compute_headers, timeout=8
            )
            if compute_res.status_code == 200:
                result_json = compute_res.json()
                return result_json["pipelineResponse"][0]["output"][0]["target"]

        except Exception:
            pass

        return self._local_fallback(text, target_lang)

    def _local_fallback(self, text: str, target_lang: str) -> str:
        """Deterministic fallback keeping legal and clinical headers intact."""
        if target_lang == "hi":
            t = text
            t = t.replace(
                "**Product Classification:**",
                "**उत्पाद वर्गीकरण (Product Classification):**",
            )
            t = t.replace(
                "**Jurisdiction Track:**", "**अधिकार क्षेत्र (Jurisdiction Track):**"
            )
            t = t.replace(
                "**Core Legal & Regulatory Posture:**",
                "**मुख्य कानूनी और नियामक स्थिति:**",
            )
            t = t.replace(
                "* **IP & Patentability:**", "* **बौद्धिक संपदा और पेटेंट पात्रता:**"
            )
            t = t.replace(
                "* **Access & Benefit-Sharing (ABS):**",
                "* **पहुंच और लाभ साझाकरण (ABS):**",
            )
            t = t.replace(
                "**Statutory References & Grounded Rules:**",
                "**सांविधिक संदर्भ और नियम:**",
            )
            t = t.replace(
                "Strictly barred from product patents under",
                "के तहत उत्पाद पेटेंट से पूर्णतः वर्जित",
            )
            t = t.replace(
                "High patentability potential for novel isolation processes",
                "नवीन पृथक्करण प्रक्रियाओं के लिए उच्च पेटेंट क्षमता",
            )
            return t
        elif target_lang == "ta":
            t = text
            t = t.replace("**Product Classification:**", "**தயாரிப்பு வகைப்பாடு:**")
            t = t.replace(
                "**Core Legal & Regulatory Posture:**", "**முக்கிய சட்ட நிலை:**"
            )
            return t
        return text


if __name__ == "__main__":
    service = BhashiniService()
    sample_text = (
        "Triphala Kwatha prepared as per Sharangadhara Samhita is strictly barred from product patents "
        "under Section 3(p). Defended by TKDL prior art."
    )
    print("Testing Bhashini Engine...")
    translated = service.translate(sample_text, "hi")
    print("\nResult (Hindi):")
    print(translated)
