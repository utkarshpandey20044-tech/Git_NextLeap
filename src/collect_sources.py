import csv
import hashlib
from pathlib import Path
from urllib.parse import urlparse

import requests


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILE = PROJECT_ROOT / "data" / "sources.csv"
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"


def make_filename(scheme, source_type, url):
    """Create a safe and unique filename for a downloaded source."""
    parsed = urlparse(url)

    extension = ".html"

    if parsed.path.lower().endswith(".pdf"):
        extension = ".pdf"

    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()[:8]

    return f"{scheme}_{source_type}_{url_hash}{extension}"


def download_source(url):
    """Download a URL and return its content and content type."""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/154.0 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    return response.content, response.headers.get("Content-Type", "")


def main():
    """Read sources.csv and download every approved source."""

    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(SOURCE_FILE, "r", encoding="utf-8", newline="") as file:
        sources = list(csv.DictReader(file))

    print(f"Found {len(sources)} sources in sources.csv")
    print("-" * 60)

    successful = 0
    failed = 0

    for source in sources:
        scheme = source["scheme"]
        source_type = source["source_type"]
        url = source["url"]

        print(f"\nDownloading: {scheme} | {source_type}")
        print(url)

        try:
            content, content_type = download_source(url)

            filename = make_filename(
                scheme,
                source_type,
                url,
            )

            output_path = DOCUMENTS_DIR / filename
            output_path.write_bytes(content)

            print(f"SUCCESS -> {filename}")
            print(f"Content type: {content_type}")

            successful += 1

        except Exception as error:
            print(f"FAILED -> {error}")
            failed += 1

    print("\n" + "=" * 60)
    print("COLLECTION COMPLETE")
    print(f"Successful: {successful}")
    print(f"Failed:     {failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()