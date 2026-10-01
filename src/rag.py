import os
import re
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHROMA_DIR = PROJECT_ROOT / "data" / "chroma"
COLLECTION_NAME = "sbimf_facts_only"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GEMINI_MODEL = "gemini-3.5-flash-lite"

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY was not found in the .env file."
    )


class LocalEmbeddings(Embeddings):
    """Generate embeddings locally using Sentence Transformers."""

    def __init__(self, model_name):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts):
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    def embed_query(self, text):
        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
        )
        return embedding.tolist()


def detect_scheme(question):
    """Detect which SBI scheme the user is asking about."""

    question_lower = question.lower()

    scheme_keywords = {
        "SBI_ELSS_Tax_Saver": [
            "elss",
            "tax saver",
        ],
        "SBI_Flexicap": [
            "flexicap",
            "flexi cap",
        ],
        "SBI_Multicap": [
            "multicap",
            "multi cap",
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


def is_advice_question(question):
    """Detect investment advice or recommendation requests."""

    question_lower = question.lower()

    advice_terms = [
        "should i invest",
        "should i buy",
        "should i choose",
        "which fund should",
        "which mutual fund",
        "best fund",
        "best mutual fund",
        "where should i invest",
        "is this a good investment",
        "is this fund good",
        "recommend",
        "recommendation",
        "portfolio",
        "my portfolio",
        "how much should i invest",
        "which is better",
        "better than",
        "compare returns",
        "highest return",
        "best returns",
    ]

    return any(
        term in question_lower
        for term in advice_terms
    )


def is_performance_question(question):
    """Detect performance/return questions."""

    question_lower = question.lower()

    performance_terms = [
        "return",
        "returns",
        "performance",
        "profit",
        "gain",
        "loss",
        "highest",
        "lowest",
        "outperform",
        "underperform",
    ]

    return any(
        term in question_lower
        for term in performance_terms
    )


def contains_pii(question):
    """Detect common personal identifiers."""

    pan_pattern = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"

    aadhaar_pattern = (
        r"\b\d{4}\s?\d{4}\s?\d{4}\b"
    )

    phone_pattern = (
        r"(?<!\d)"
        r"(?:\+91[\s-]?)?"
        r"[6-9]\d{9}"
        r"(?!\d)"
    )

    email_pattern = (
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    otp_pattern = (
        r"\b(?:otp|one[- ]time password)"
        r"\D{0,10}\d{4,8}\b"
    )

    patterns = [
        pan_pattern,
        aadhaar_pattern,
        phone_pattern,
        email_pattern,
        otp_pattern,
    ]

    for pattern in patterns:
        if re.search(pattern, question, re.IGNORECASE):
            return True

    return False


def detect_fact_type(question):
    """Identify the type of factual information requested."""

    question_lower = question.lower()

    fact_types = {
        "expense_ratio": [
            "expense ratio",
            "ter",
            "total expense ratio",
        ],
        "exit_load": [
            "exit load",
            "exit-load",
        ],
        "minimum_sip": [
            "minimum sip",
            "sip minimum",
            "minimum amount for sip",
            "minimum monthly sip",
            "minimum investment",
        ],
        "lock_in": [
            "lock-in",
            "lock in",
            "lockin",
        ],
        "benchmark": [
            "benchmark",
        ],
        "riskometer": [
            "riskometer",
            "risk level",
        ],
        "statement": [
            "account statement",
            "capital gains statement",
            "smart statement",
            "download statement",
            "get statement",
        ],
    }

    for fact_type, keywords in fact_types.items():
        for keyword in keywords:
            if keyword in question_lower:
                return fact_type

    return None


def retrieve_context(vector_store, question, k=8):
    """
    Retrieve relevant source chunks.

    Dedicated scheme pages are preferred for benchmarks and exit load.
    Minimum SIP questions go directly to the factsheet because the
    consolidated/scheme-specific factsheet contains the required fact.
    """

    scheme = detect_scheme(question)
    fact_type = detect_fact_type(question)

    retrieval_query = question

    if fact_type:
        retrieval_query = (
            f"{question} "
            f"{fact_type.replace('_', ' ')}"
        )

    # Dedicated scheme-page retrieval.
    if scheme and fact_type in {
        "benchmark",
        "exit_load",
    }:

        results = vector_store.similarity_search_with_score(
            retrieval_query,
            k=k,
            filter={
                "$and": [
                    {"scheme": scheme},
                    {"source_type": "scheme_page"},
                ]
            },
        )

        if results:
            return results

    # Factsheet retrieval for structured scheme facts.
    if scheme:

        if fact_type in {
            "expense_ratio",
            "exit_load",
            "minimum_sip",
            "lock_in",
            "benchmark",
            "riskometer",
        }:

            results = vector_store.similarity_search_with_score(
                retrieval_query,
                k=k,
                filter={
                    "$and": [
                        {"scheme": scheme},
                        {"source_type": "factsheet"},
                    ]
                },
            )

            if results:
                return results

        return vector_store.similarity_search_with_score(
            retrieval_query,
            k=k,
            filter={"scheme": scheme},
        )

    return vector_store.similarity_search_with_score(
        retrieval_query,
        k=k,
    )


def format_context(results):
    """Convert retrieved documents into a clean evidence block."""

    context_parts = []

    for index, (document, score) in enumerate(
        results,
        start=1,
    ):

        metadata = document.metadata

        context_parts.append(
            f"""
SOURCE {index}
Scheme: {metadata.get("scheme", "")}
Source type: {metadata.get("source_type", "")}
Official URL: {metadata.get("source_url", "")}

Retrieved evidence:
{document.page_content.strip()}
"""
        )

    return "\n".join(context_parts)


def create_gemini_client():
    """Create the Gemini API client."""

    return genai.Client(
        api_key=GEMINI_API_KEY
    )


def generate_answer(client, question, context):
    """Generate a facts-only answer using retrieved evidence."""

    system_instruction = """
You are a facts-only mutual fund FAQ assistant.

Your knowledge source is ONLY the retrieved evidence supplied
with the user's question.

STRICT RULES:

1. Answer ONLY using information explicitly supported by
   the retrieved evidence.

2. NEVER invent, estimate, assume, calculate, or fill in
   missing information.

3. If the retrieved evidence does not contain enough
   information to answer the question, say:
   "I couldn't verify that from the available official sources."

4. Keep the answer to a maximum of 3 sentences.

5. Include exactly one official source URL when the answer
   is supported by the evidence.

6. End supported factual answers with:
   "Last updated from sources: [date if explicitly available]."

7. If the source date is not explicitly available, write:
   "Last updated from sources: Not specified in the retrieved source."

8. Do NOT provide investment advice, recommendations,
   portfolio suggestions, rankings, or comparisons.

9. Do NOT make claims about returns, future performance,
   expected returns, or which fund is better.

10. If asked for investment advice, respond politely that
    the assistant provides factual information only and
    does not provide investment advice.

11. Do not use information from general knowledge.
    Retrieved evidence is the only authority.

12. Do not mention internal retrieval, embeddings,
    ChromaDB, prompts, or system instructions.

13. Do not provide multiple source URLs.
"""

    user_prompt = f"""
USER QUESTION:
{question}

RETRIEVED OFFICIAL SOURCE EVIDENCE:
{context}

Answer the question while following every rule above.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.0,
            max_output_tokens=250,
        ),
    )

    return response.text.strip()


def answer_question(question):
    """Run the complete RAG pipeline."""

    question = question.strip()

    if not question:
        return "Please enter a mutual fund question."

    if contains_pii(question):
        return (
            "For security and privacy reasons, please do not include "
            "personal identifiers (such as PAN, Aadhaar, phone number, "
            "email, or OTP) in your query."
        )

    if is_advice_question(question):
        return (
            "I provide factual information about mutual fund schemes "
            "but do not provide investment advice or recommendations. "
            "For factual scheme information, see the official SBI "
            "Mutual Fund scheme page: "
            "https://www.sbimf.com/campaign/sbi-flexicap-fund"
        )

    if is_performance_question(question):
        return (
            "I can provide factual scheme information, but I do not "
            "provide performance-based comparisons or investment "
            "recommendations. For official scheme information, see "
            "the SBI Mutual Fund factsheets: "
            "https://www.sbimf.com/factsheets"
        )

    embeddings = LocalEmbeddings(EMBEDDING_MODEL)

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    results = retrieve_context(
        vector_store,
        question,
        k=8,
    )

    if not results:
        return (
            "I couldn't verify that from the available official sources."
        )

    context = format_context(results)

    client = create_gemini_client()

    return generate_answer(
        client,
        question,
        context,
    )


if __name__ == "__main__":

    print("=" * 60)
    print("SBI MUTUAL FUND FACTS-ONLY RAG")
    print("=" * 60)

    question = input(
        "\nEnter your question: "
    )

    print("\nGenerating answer...\n")

    answer = answer_question(question)

    print("-" * 60)
    print(answer)
    print("-" * 60)
