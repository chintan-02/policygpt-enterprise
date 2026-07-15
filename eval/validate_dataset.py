import json
from collections import Counter
from pathlib import Path
from typing import Any

DATASET_PATH = Path(__file__).with_name("questions.jsonl")

REQUIRED_FIELDS = {
    "id",
    "question",
    "expected_answer_keywords",
    "expected_pages",
    "should_answer",
    "category",
    "difficulty",
    "evaluation_focus",
    "notes",
}
ALLOWED_DIFFICULTIES = {"easy", "moderate", "hard"}
ALLOWED_EVALUATION_FOCUS = {
    "retrieval",
    "citation",
    "answer_content",
    "fallback",
    "condition",
    "exception",
    "deadline",
    "numeric_accuracy",
}
EXPECTED_DIFFICULTY_COUNTS = {"easy": 6, "moderate": 6, "hard": 4}


class DatasetValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("\n".join(errors))


def load_dataset(path: Path = DATASET_PATH) -> list[dict[str, Any]]:
    if not path.is_file():
        raise DatasetValidationError([f"Dataset file does not exist: {path}"])

    records: list[dict[str, Any]] = []
    errors: list[str] = []

    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"Line {line_number}: invalid JSON ({exc.msg})")
            continue

        if not isinstance(record, dict):
            errors.append(f"Line {line_number}: record must be a JSON object")
            continue

        records.append(record)

    if errors:
        raise DatasetValidationError(errors)

    return records


def validate_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    seen_ids: set[str] = set()

    if len(records) != 16:
        errors.append(f"Expected exactly 16 records, found {len(records)}")

    for index, record in enumerate(records, start=1):
        label = f"Record {index}"
        missing_fields = REQUIRED_FIELDS - record.keys()

        if missing_fields:
            errors.append(
                f"{label}: missing fields: {', '.join(sorted(missing_fields))}"
            )

        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id.strip():
            errors.append(f"{label}: id must be a non-empty string")
        elif record_id in seen_ids:
            errors.append(f"{label}: duplicate id: {record_id}")
        else:
            seen_ids.add(record_id)
            label = f"Record {index} ({record_id})"

        question = record.get("question")
        if not isinstance(question, str) or not question.strip():
            errors.append(f"{label}: question must be a non-empty string")

        keywords = record.get("expected_answer_keywords")
        keywords_are_valid = isinstance(keywords, list) and all(
            isinstance(keyword, str) and bool(keyword.strip())
            for keyword in keywords
        )
        if not keywords_are_valid:
            errors.append(
                f"{label}: expected_answer_keywords must be a list of "
                "non-empty strings"
            )

        pages = record.get("expected_pages")
        pages_are_valid = isinstance(pages, list) and all(
            isinstance(page, int) and not isinstance(page, bool) and page > 0
            for page in pages
        )
        if not pages_are_valid:
            errors.append(
                f"{label}: expected_pages must be a list of positive integers"
            )

        should_answer = record.get("should_answer")
        if not isinstance(should_answer, bool):
            errors.append(f"{label}: should_answer must be boolean")
        elif should_answer:
            if keywords_are_valid and not keywords:
                errors.append(
                    f"{label}: supported questions require expected keywords"
                )
            if pages_are_valid and not pages:
                errors.append(
                    f"{label}: supported questions require expected pages"
                )
        else:
            if isinstance(keywords, list) and keywords:
                errors.append(
                    f"{label}: unsupported questions cannot have expected keywords"
                )
            if isinstance(pages, list) and pages:
                errors.append(
                    f"{label}: unsupported questions cannot have expected pages"
                )

        category = record.get("category")
        if not isinstance(category, str) or not category.strip():
            errors.append(f"{label}: category must be a non-empty string")

        difficulty = record.get("difficulty")
        if difficulty not in ALLOWED_DIFFICULTIES:
            errors.append(
                f"{label}: difficulty must be one of "
                f"{', '.join(sorted(ALLOWED_DIFFICULTIES))}"
            )

        evaluation_focus = record.get("evaluation_focus")
        if not isinstance(evaluation_focus, list) or not evaluation_focus:
            errors.append(
                f"{label}: evaluation_focus must be a non-empty list"
            )
        elif not all(isinstance(value, str) for value in evaluation_focus):
            errors.append(f"{label}: evaluation_focus values must be strings")
        else:
            invalid_focus = set(evaluation_focus) - ALLOWED_EVALUATION_FOCUS
            if invalid_focus:
                errors.append(
                    f"{label}: invalid evaluation_focus values: "
                    f"{', '.join(sorted(invalid_focus))}"
                )

        notes = record.get("notes")
        if not isinstance(notes, str) or not notes.strip():
            errors.append(f"{label}: notes must be a non-empty string")

    supported_count = sum(record.get("should_answer") is True for record in records)
    unsupported_count = sum(
        record.get("should_answer") is False for record in records
    )
    difficulty_counts = Counter(record.get("difficulty") for record in records)

    if supported_count != 11:
        errors.append(f"Expected 11 supported questions, found {supported_count}")
    if unsupported_count != 5:
        errors.append(f"Expected 5 unsupported questions, found {unsupported_count}")
    if dict(difficulty_counts) != EXPECTED_DIFFICULTY_COUNTS:
        errors.append(
            "Expected difficulty distribution "
            f"{EXPECTED_DIFFICULTY_COUNTS}, found {dict(difficulty_counts)}"
        )

    if errors:
        raise DatasetValidationError(errors)

    category_counts = Counter(record["category"] for record in records)
    return {
        "total": len(records),
        "supported": supported_count,
        "unsupported": unsupported_count,
        "difficulty_counts": dict(difficulty_counts),
        "category_counts": dict(sorted(category_counts.items())),
    }


def validate_dataset(path: Path = DATASET_PATH) -> dict[str, Any]:
    return validate_records(load_dataset(path))


def main() -> int:
    try:
        summary = validate_dataset()
    except DatasetValidationError as exc:
        print("Dataset validation failed")
        for error in exc.errors:
            print(f"- {error}")
        return 1

    difficulty_counts = summary["difficulty_counts"]
    categories = ", ".join(
        f"{category}={count}"
        for category, count in summary["category_counts"].items()
    )

    print("Dataset validation passed")
    print(f"Total questions: {summary['total']}")
    print(f"Supported: {summary['supported']}")
    print(f"Unsupported: {summary['unsupported']}")
    print(f"Easy: {difficulty_counts['easy']}")
    print(f"Moderate: {difficulty_counts['moderate']}")
    print(f"Hard: {difficulty_counts['hard']}")
    print(f"Categories: {categories}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
