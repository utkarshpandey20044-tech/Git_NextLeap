import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
SOURCE_FILE = PROJECT_ROOT / "data" / "sources.csv"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def load_sources():
    """Load all approved sources from sources.csv."""

    with open(
        SOURCE_FILE,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        return list(csv.DictReader(file))


def identify_source(file_name, sources):
    """Identify the exact source entry for a processed document."""

    stem = Path(file_name).stem

    # Remove the final 8-character URL hash.
    # Example:
    # SBI_Multicap_scheme_page_ba63d615
    # becomes:
    # SBI_Multicap_scheme_page
    parts = stem.rsplit("_", 1)

    if len(parts) != 2:
        raise ValueError(
            f"Unexpected filename format: {file_name}"
        )

    source_name = parts[0]

    # Try every source entry and find the one whose
    # scheme + source_type exactly matches the filename.
    for source in sources:

        expected_name = (
            f"{source['scheme']}_"
            f"{source['source_type']}"
        )

        if source_name == expected_name:

            return {
                "scheme": source["scheme"],
                "source_type": source["source_type"],
                "source_url": source["url"],
            }

    raise ValueError(
        f"No source URL found for "
        f"document '{file_name}'"
    )


def create_chunks(text):
    """Split text into overlapping chunks."""

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(
            start + CHUNK_SIZE,
            text_length,
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - CHUNK_OVERLAP

    return chunks


def main():
    """Create JSONL chunks with source metadata."""

    CHUNKS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    sources = load_sources()

    files = list(
        PROCESSED_DIR.glob("*.txt")
    )

    print(
        f"Found {len(files)} processed documents"
    )

    print("-" * 60)

    total_chunks = 0
    failed_documents = 0

    output_file = (
        CHUNKS_DIR / "chunks.jsonl"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as output:

        for file_path in files:

            print(
                f"\nChunking: {file_path.name}"
            )

            try:
                text = file_path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )

                source_metadata = identify_source(
                    file_path.name,
                    sources,
                )

                chunks = create_chunks(text)

                for index, chunk in enumerate(
                    chunks
                ):

                    record = {
                        "chunk_id": (
                            f"{file_path.stem}_"
                            f"{index}"
                        ),
                        "text": chunk,
                        "metadata": {
                            "source_file": file_path.name,
                            "scheme": source_metadata[
                                "scheme"
                            ],
                            "source_type": source_metadata[
                                "source_type"
                            ],
                            "source_url": source_metadata[
                                "source_url"
                            ],
                            "chunk_index": index,
                        },
                    }

                    output.write(
                        json.dumps(
                            record,
                            ensure_ascii=False,
                        )
                        + "\n"
                    )

                print(
                    f"Created {len(chunks)} chunks"
                )

                total_chunks += len(chunks)

            except Exception as error:

                failed_documents += 1

                print(
                    f"FAILED -> {error}"
                )

    print("\n" + "=" * 60)
    print("CHUNKING COMPLETE")
    print(
        f"Total chunks: {total_chunks:,}"
    )
    print(
        f"Failed documents: {failed_documents}"
    )
    print(
        f"Output: {output_file}"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()