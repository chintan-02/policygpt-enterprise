import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.pdf_extraction_service import PDFExtractionService

DEFAULT_PDF_PATH = PROJECT_ROOT / "examples" / "sample_hr_policy.pdf"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print PDF text page-by-page for evaluation verification.",
    )
    parser.add_argument(
        "pdf_path",
        nargs="?",
        type=Path,
        default=DEFAULT_PDF_PATH,
        help="PDF to inspect (default: examples/sample_hr_policy.pdf)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf_path = args.pdf_path.expanduser().resolve()

    if not pdf_path.is_file():
        print(f"PDF file does not exist: {pdf_path}", file=sys.stderr)
        return 1

    extraction_result = PDFExtractionService().extract_text_from_pdf(
        pdf_path.read_bytes()
    )

    for index, page in enumerate(extraction_result.pages):
        if index:
            print()
        print(f"PAGE {page.page_number}")
        print(page.text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
