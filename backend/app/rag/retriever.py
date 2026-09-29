import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from fastembed import TextEmbedding

# Resolve root path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

COLLECTION_NAME = "ayush_legal_corpus"
STORAGE_PATH = BASE_DIR / "qdrant_storage"
MODEL_NAME = "BAAI/bge-small-en-v1.5"


class StatutoryRetriever:
    def __init__(self):
        print("Initializing Qdrant client & embedding model...")
        self.client = QdrantClient(path=str(STORAGE_PATH))
        self.model = TextEmbedding(model_name=MODEL_NAME)

    def retrieve(
        self,
        query: str,
        jurisdiction: Optional[str] = None,
        jurisdiction_filter: Optional[str] = None,
        regime: Optional[str] = None,
        top_k: int = 3,
        score_threshold: float = 0.50,
    ) -> List[Dict[str, Any]]:
        """
        Performs dense vector retrieval filtered by jurisdiction and regulatory regime.
        """
        # Generate query vector
        query_vector = list(self.model.embed([query]))[0].tolist()

        # Construct metadata filters
        must_conditions = []
        if jurisdiction:
            must_conditions.append(
                FieldCondition(key="jurisdiction", match=MatchValue(value=jurisdiction))
            )
        if regime:
            must_conditions.append(
                FieldCondition(key="regime", match=MatchValue(value=regime))
            )

        query_filter = Filter(must=must_conditions) if must_conditions else None

        # Execute query using query_points API
        response = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
            score_threshold=score_threshold,
        )

        formatted_results = []
        for res in response.points:
            formatted_results.append(
                {
                    "chunk_id": res.payload.get("chunk_id"),
                    "score": round(res.score, 4),
                    "citation_anchor": res.payload.get("citation_anchor"),
                    "jurisdiction": res.payload.get("jurisdiction"),
                    "regime": res.payload.get("regime"),
                    "compliance_tag": res.payload.get("compliance_tag"),
                    "content": res.payload.get("content"),
                }
            )

        return formatted_results

    def close(self):
        """Explicitly close client to avoid Python garbage collection warnings."""
        if hasattr(self, "client"):
            self.client.close()


if __name__ == "__main__":
    retriever = StatutoryRetriever()
    try:
        # Test Query 1: Domestic Ayurvedic Patent Exclusion
        test_query_in = "Can I patent a classical formula mentioned in Charaka Samhita?"
        print(f"\n[TEST 1] Query: '{test_query_in}' (Filter: IN)")
        hits_in = retriever.retrieve(test_query_in, jurisdiction="IN", top_k=2)
        for h in hits_in:
            print(
                f" -> [{h['citation_anchor']}] (Score: {h['score']}) | Tag: {h['compliance_tag']}"
            )

        # Test Query 2: International Traditional Knowledge & Origin Disclosure
        test_query_int = (
            "Do I need to disclose the country of origin when filing a patent abroad?"
        )
        print(f"\n[TEST 2] Query: '{test_query_int}' (Filter: INT)")
        hits_int = retriever.retrieve(test_query_int, jurisdiction="INT", top_k=2)
        for h in hits_int:
            print(
                f" -> [{h['citation_anchor']}] (Score: {h['score']}) | Tag: {h['compliance_tag']}"
            )
    finally:
        retriever.close()
