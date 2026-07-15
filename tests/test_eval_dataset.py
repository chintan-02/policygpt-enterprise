from collections import Counter
from pathlib import Path

import fitz

from eval.validate_dataset import (
    ALLOWED_DIFFICULTIES,
    ALLOWED_EVALUATION_FOCUS,
    EXPECTED_DIFFICULTY_COUNTS,
    load_dataset,
    validate_dataset,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "eval" / "questions.jsonl"
PDF_PATH = PROJECT_ROOT / "examples" / "sample_hr_policy.pdf"


def _records() -> list[dict[str, object]]:
    return load_dataset(DATASET_PATH)


def test_dataset_validation_succeeds() -> None:
    summary = validate_dataset(DATASET_PATH)

    assert summary["total"] == 16
    assert summary["supported"] == 11
    assert summary["unsupported"] == 5
    assert summary["difficulty_counts"] == EXPECTED_DIFFICULTY_COUNTS


def test_record_counts_ids_and_difficulty_distribution() -> None:
    records = _records()
    ids = [record["id"] for record in records]
    difficulty_counts = Counter(record["difficulty"] for record in records)

    assert len(records) == 16
    assert len(ids) == len(set(ids))
    assert sum(record["should_answer"] is True for record in records) == 11
    assert sum(record["should_answer"] is False for record in records) == 5
    assert dict(difficulty_counts) == EXPECTED_DIFFICULTY_COUNTS


def test_supported_and_unsupported_ground_truth_fields() -> None:
    for record in _records():
        if record["should_answer"]:
            assert record["expected_answer_keywords"]
            assert record["expected_pages"]
        else:
            assert record["expected_answer_keywords"] == []
            assert record["expected_pages"] == []


def test_pages_are_in_pdf_and_keywords_are_grounded_on_expected_pages() -> None:
    with fitz.open(PDF_PATH) as pdf_document:
        page_count = pdf_document.page_count
        normalized_pages = {
            page_number: " ".join(
                pdf_document.load_page(page_number - 1).get_text("text").split()
            ).casefold()
            for page_number in range(1, page_count + 1)
        }

    for record in _records():
        expected_pages = record["expected_pages"]
        assert all(1 <= page <= page_count for page in expected_pages)

        if not record["should_answer"]:
            continue

        expected_page_text = " ".join(
            normalized_pages[page] for page in expected_pages
        )
        for keyword in record["expected_answer_keywords"]:
            normalized_keyword = " ".join(keyword.split()).casefold()
            assert normalized_keyword in expected_page_text, (
                f"{record['id']}: keyword {keyword!r} was not found on "
                f"expected pages {expected_pages}"
            )


def test_enum_like_values_are_allowed() -> None:
    for record in _records():
        assert record["difficulty"] in ALLOWED_DIFFICULTIES
        assert record["evaluation_focus"]
        assert set(record["evaluation_focus"]) <= ALLOWED_EVALUATION_FOCUS
