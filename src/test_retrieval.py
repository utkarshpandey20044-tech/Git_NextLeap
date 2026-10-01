from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHROMA_DIR = (
    PROJECT_ROOT
    / "data"
    / "chroma"
)

COLLECTION_NAME = "sbimf_facts_only"

EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)


class LocalEmbeddings(Embeddings):
    """Generate embeddings locally using Sentence Transformers."""

    def __init__(self, model_name):
        self.model = SentenceTransformer(
            model_name
        )

    def embed_documents(self, texts):
        """Create embeddings for documents."""

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
        )

        return embeddings.tolist()

    def embed_query(self, text):
        """Create an embedding for a query."""

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return embedding.tolist()


def detect_scheme(question):
    """Detect the scheme mentioned in the question."""

    question_lower = question.lower()

    scheme_keywords = {
        "SBI_ELSS_Tax_Saver": [
            "elss",
            "tax saver",
        ],
        "SBI_Flexicap": [
            "flexicap",
        ],
        "SBI_Multicap": [
            "multicap",
        ],
        "SBI_Large_Cap": [
            "large cap",
            "large-cap",
        ],
    }

    for scheme, keywords in scheme_keywords.items():

        for keyword in keywords:

            if keyword in question_lower:
                return scheme

    return None


def retrieve_documents(
    vector_store,
    question,
    k=5,
):
    """Retrieve documents, using scheme filtering when possible."""

    scheme = detect_scheme(question)

    if scheme:

        print(
            f"Detected scheme: {scheme}"
        )

        results = vector_store.similarity_search_with_score(
            question,
            k=k,
            filter={
                "scheme": scheme
            },
        )

    else:

        print(
            "No specific scheme detected."
        )

        results = vector_store.similarity_search_with_score(
            question,
            k=k,
        )

    return results


def main():
    """Test scheme-aware semantic retrieval."""

    print("=" * 60)
    print("SCHEME-AWARE RAG RETRIEVAL TEST")
    print("=" * 60)

    print(
        "\nLoading local embedding model..."
    )

    embeddings = LocalEmbeddings(
        EMBEDDING_MODEL
    )

    print(
        "Loading ChromaDB..."
    )

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(
            CHROMA_DIR
        ),
    )

    questions = [
        "What is the minimum SIP amount for SBI ELSS Tax Saver Fund?",
        "What is the exit load of SBI Flexicap Fund?",
        "What is the benchmark of SBI Multicap Fund?",
        "How do I download my account statement?",
    ]

    for question in questions:

        print("\n" + "=" * 60)
        print(
            f"QUESTION: {question}"
        )
        print("=" * 60)

        results = retrieve_documents(
            vector_store,
            question,
            k=5,
        )

        for index, (document, score) in enumerate(
            results,
            start=1,
        ):

            print(
                f"\n--- RESULT {index} ---"
            )

            print(
                f"Score: {score:.4f}"
            )

            print(
                f"Scheme: "
                f"{document.metadata.get('scheme')}"
            )

            print(
                f"Source type: "
                f"{document.metadata.get('source_type')}"
            )

            print(
                f"Source URL: "
                f"{document.metadata.get('source_url')}"
            )

            print(
                "\nRetrieved text:"
            )

            print(
                document.page_content[:1000]
            )

    print("\n" + "=" * 60)
    print("RETRIEVAL TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()