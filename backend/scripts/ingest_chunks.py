import sys
import uuid
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

# Ensure parent directory is in path so we can import from app
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.rag.chunker import process_entire_corpus

# Configuration
COLLECTION_NAME = "ayush_legal_corpus"
STORAGE_PATH = BASE_DIR / "qdrant_storage"
MODEL_NAME = "BAAI/bge-small-en-v1.5"  # Fast, highly accurate, lightweight on CPU


def run_ingestion():
    print(f"Loading embedding model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    embedding_dim = model.get_sentence_embedding_dimension()

    print(f"Initializing local Qdrant at: {STORAGE_PATH.resolve()}...")
    client = QdrantClient(path=str(STORAGE_PATH))

    # Recreate collection to ensure clean state
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
    )

    print("Extracting structural statutory chunks from corpus...")
    chunks = process_entire_corpus()
    print(f"Total chunks to embed: {len(chunks)}")

    points = []
    contents = [c["content"] for c in chunks]

    print("Generating dense vector embeddings...")
    embeddings = model.encode(
        contents, show_progress_bar=True, normalize_embeddings=True
    )

    for i, chunk in enumerate(chunks):
        # Generate a stable UUID from chunk_id
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk["chunk_id"]))

        points.append(
            PointStruct(
                id=point_id,
                vector=embeddings[i].tolist(),
                payload={
                    "chunk_id": chunk["chunk_id"],
                    "content": chunk["content"],
                    "metadata": chunk["metadata"],
                    "jurisdiction": chunk["metadata"]["jurisdiction"],
                    "regime": chunk["metadata"]["regime"],
                    "compliance_tag": chunk["metadata"]["compliance_tag"],
                    "citation_anchor": chunk["metadata"]["citation_anchor"],
                },
            )
        )

    # Upsert all points into Qdrant
    client.upsert(collection_name=COLLECTION_NAME, points=points)

    info = client.get_collection(COLLECTION_NAME)
    print(
        f"\nIngestion Complete! Total points indexed in '{COLLECTION_NAME}': {info.points_count}"
    )


if __name__ == "__main__":
    run_ingestion()
