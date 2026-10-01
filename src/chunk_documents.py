import json
from pathlib import Path


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"


# Chunking configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def get_metadata(file_name):
    """Extract basic metadata from the processed filename."""

    name = Path(file_name).stem

    parts = name.split("_")

    if name.startswith("ALL_"):
        scheme = "ALL"
        source_type = "_".join(parts[1:-1])

    elif name.startswith("SEBI_"):
        scheme = "SEBI"
        source_type = "_".join(parts[1:-1])

    else:
        # Scheme names may contain underscores.
        # The source type is the part immediately before the hash.
        scheme = "_".join(parts[:-2])
        source_type = parts[-2]

    return {
        "source_file": file_name,
        "scheme": scheme,
        "source_type": source_type,
    }


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
    """Create JSONL chunks from processed documents."""

    CHUNKS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = list(PROCESSED_DIR.glob("*.txt"))

    print(f"Found {len(files)} processed documents")
    print("-" * 60)

    total_chunks = 0

    output_file = CHUNKS_DIR / "chunks.jsonl"

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as output:

        for file_path in files:

            print(f"\nChunking: {file_path.name}")

            try:
                text = file_path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )

                metadata = get_metadata(
                    file_path.name
                )

                chunks = create_chunks(text)

                for index, chunk in enumerate(chunks):

                    record = {
                        "chunk_id": (
                            f"{file_path.stem}_"
                            f"{index}"
                        ),
                        "text": chunk,
                        "metadata": {
                            **metadata,
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
                print(
                    f"FAILED -> {error}"
                )

    print("\n" + "=" * 60)
    print("CHUNKING COMPLETE")
    print(f"Total chunks: {total_chunks:,}")
    print(f"Output: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()