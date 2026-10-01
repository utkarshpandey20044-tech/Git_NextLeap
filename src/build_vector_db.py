import json
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHUNKS_FILE = (
    PROJECT_ROOT
    / "data"
    / "chunks"
    / "chunks.jsonl"
)

CHROMA_DIR = (
    PROJECT_ROOT
    / "data"
    / "chroma"
)

COLLECTION_NAME = "sbimf_facts_only"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class LocalEmbeddings(Embeddings):
    """Generate embeddings locally using Sentence Transformers."""

    def __init__(self, model_name):
        self.model = SentenceTransformer(
            model_name
        )

    def embed_documents(self, texts):
        """Create embeddings for multiple documents."""

        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            normalize_embeddings=True,
        )

        return embeddings.tolist()

    def embed_query(self, text):
        """Create an embedding for one query."""

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return embedding.tolist()


def load_chunks():
    """Load chunk records from chunks.jsonl."""

    chunks = []

    with open(
        CHUNKS_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            if line.strip():
                chunks.append(
                    json.loads(line)
                )

    return chunks


def main():
    """Build the Chroma vector database."""

    print("=" * 60)
    print("BUILDING LOCAL CHROMA VECTOR DATABASE")
    print("=" * 60)

    print(
        f"\nLoading chunks from:\n{CHUNKS_FILE}"
    )

    chunks = load_chunks()

    print(
        f"Loaded {len(chunks):,} chunks"
    )

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    metadatas = [
        chunk["metadata"]
        for chunk in chunks
    ]

    ids = [
        chunk["chunk_id"]
        for chunk in chunks
    ]

    print(
        "\nLoading local embedding model..."
    )

    print(
        f"Model: {EMBEDDING_MODEL}"
    )

    embeddings = LocalEmbeddings(
        EMBEDDING_MODEL
    )

    print(
        "\nLocal embedding model loaded."
    )

    print(
        "\nCreating Chroma vector store..."
    )

    CHROMA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(
            CHROMA_DIR
        ),
    )

    print(
        "\nGenerating embeddings and "
        "adding documents..."
    )

    vector_store.add_texts(
        texts=texts,
        metadatas=metadatas,
        ids=ids,
    )

    print("\n" + "=" * 60)
    print("VECTOR DATABASE COMPLETE")
    print("=" * 60)

    print(
        f"Documents stored: {len(texts):,}"
    )

    print(
        f"Collection: {COLLECTION_NAME}"
    )

    print(
        f"Database location: {CHROMA_DIR}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()