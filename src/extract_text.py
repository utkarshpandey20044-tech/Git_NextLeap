from pathlib import Path

import pymupdf
from bs4 import BeautifulSoup


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def extract_pdf_text(file_path):
    """Extract text from a PDF file."""

    text_parts = []

    document = pymupdf.open(file_path)

    try:
        for page in document:
            text = page.get_text()
            text_parts.append(text)
    finally:
        document.close()

    return "\n".join(text_parts)


def extract_html_text(file_path):
    """Extract readable text from an HTML file."""

    html = file_path.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    soup = BeautifulSoup(html, "html.parser")

    # Remove elements that don't contain useful page content.
    for element in soup(
        ["script", "style", "noscript", "svg"]
    ):
        element.decompose()

    return soup.get_text(
        separator="\n",
        strip=True,
    )


def clean_text(text):
    """Perform safe cleanup without altering source meaning."""

    # Normalize non-breaking spaces.
    text = text.replace("\xa0", " ")

    lines = []

    for line in text.splitlines():
        # Collapse repeated whitespace.
        line = " ".join(line.split())

        if line:
            lines.append(line)

    return "\n".join(lines)
def extract_document(file_path):
    """Extract text based on the file extension."""

    if file_path.suffix.lower() == ".pdf":
        return extract_pdf_text(file_path)

    if file_path.suffix.lower() == ".html":
        return extract_html_text(file_path)

    raise ValueError(
        f"Unsupported file type: {file_path.suffix}"
    )


def main():
    """Extract text from every downloaded document."""

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = list(DOCUMENTS_DIR.iterdir())

    print(f"Found {len(files)} documents")
    print("-" * 60)

    successful = 0
    failed = 0

    for file_path in files:

        if not file_path.is_file():
            continue

        print(f"\nProcessing: {file_path.name}")

        try:
            text = extract_document(file_path)
            text = clean_text(text)

            output_path = (
                PROCESSED_DIR
                / f"{file_path.stem}.txt"
            )

            output_path.write_text(
                text,
                encoding="utf-8",
            )

            print(
                f"SUCCESS -> {output_path.name}"
            )
            print(
                f"Characters extracted: {len(text):,}"
            )

            successful += 1

        except Exception as error:
            print(f"FAILED -> {error}")
            failed += 1

    print("\n" + "=" * 60)
    print("TEXT EXTRACTION COMPLETE")
    print(f"Successful: {successful}")
    print(f"Failed:     {failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()