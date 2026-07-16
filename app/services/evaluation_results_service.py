from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit

from pydantic import ValidationError

from app.schemas.evaluation import EvaluationArtifactResponse


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS_PATH = "eval/results/latest_eval_results.json"


class EvaluationArtifactError(Exception):
    """Base error for safe, read-only evaluation artifact access."""


class EvaluationArtifactNotFoundError(EvaluationArtifactError):
    """Raised when the configured JSON or corresponding CSV does not exist."""


class EvaluationArtifactInvalidError(EvaluationArtifactError):
    """Raised when the artifact exists but cannot be validated safely."""


def _safe_backend_label(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        return "Configured backend"

    hostname = urlsplit(value).hostname
    if hostname in {"localhost", "127.0.0.1", "::1"}:
        return "Local backend"
    return "Configured backend"


class EvaluationResultsService:
    def __init__(
        self,
        configured_path: str | Path = DEFAULT_RESULTS_PATH,
        *,
        repository_root: Path = REPOSITORY_ROOT,
    ) -> None:
        self.repository_root = repository_root.resolve()
        self.json_path = self._resolve_path(configured_path)
        self.csv_path = self.json_path.with_suffix(".csv")

    def _resolve_path(self, configured_path: str | Path) -> Path:
        candidate = Path(configured_path)
        if candidate.is_absolute():
            raise EvaluationArtifactInvalidError(
                "The evaluation artifact path must be repository-relative."
            )

        resolved = (self.repository_root / candidate).resolve()
        try:
            resolved.relative_to(self.repository_root)
        except ValueError as exc:
            raise EvaluationArtifactInvalidError(
                "The evaluation artifact path must remain inside the repository."
            ) from exc
        return resolved

    def _benchmark_question_count(self) -> int | None:
        dataset_path = self.repository_root / "eval" / "questions.jsonl"
        try:
            return sum(
                1
                for line in dataset_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        except OSError:
            return None

    def load_latest(self) -> EvaluationArtifactResponse:
        if not self.json_path.is_file():
            raise EvaluationArtifactNotFoundError(
                "No evaluation result is available."
            )

        try:
            content = self.json_path.read_text(encoding="utf-8")
            stat = self.json_path.stat()
        except OSError as exc:
            raise EvaluationArtifactInvalidError(
                "The evaluation result could not be validated."
            ) from exc

        if not content.strip():
            raise EvaluationArtifactInvalidError(
                "The evaluation result could not be validated."
            )

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise EvaluationArtifactInvalidError(
                "The evaluation result could not be validated."
            ) from exc

        if not isinstance(payload, Mapping):
            raise EvaluationArtifactInvalidError(
                "The evaluation result could not be validated."
            )

        missing = {"run", "summary", "results"} - payload.keys()
        if missing:
            raise EvaluationArtifactInvalidError(
                "The evaluation result could not be validated."
            )

        raw_run = payload["run"]
        if not isinstance(raw_run, Mapping):
            raise EvaluationArtifactInvalidError(
                "The evaluation result could not be validated."
            )

        run = dict(raw_run)
        run["backend_base_label"] = _safe_backend_label(run.pop("base_url", None))
        dataset_path = run.get("dataset_path")
        if isinstance(dataset_path, str) and Path(dataset_path).is_absolute():
            run["dataset_path"] = Path(dataset_path).name

        raw_results = payload["results"]
        if not isinstance(raw_results, list):
            raise EvaluationArtifactInvalidError(
                "The evaluation result could not be validated."
            )

        benchmark_count = self._benchmark_question_count()
        raw_question_count = run.get("question_count")
        partial = bool(run.get("question_id") or run.get("limit"))
        if (
            benchmark_count is not None
            and isinstance(raw_question_count, int)
            and raw_question_count < benchmark_count
        ):
            partial = True

        response_payload = {
            "artifact": {
                "updated_at": datetime.fromtimestamp(
                    stat.st_mtime,
                    tz=timezone.utc,
                ),
                "question_count": len(raw_results),
                "benchmark_question_count": benchmark_count,
                "is_partial": partial,
            },
            "run": run,
            "summary": payload["summary"],
            "results": raw_results,
        }

        try:
            response = EvaluationArtifactResponse.model_validate(response_payload)
        except ValidationError as exc:
            raise EvaluationArtifactInvalidError(
                "The evaluation result could not be validated."
            ) from exc

        if not (
            response.run.question_count
            == response.summary.total_questions
            == response.artifact.question_count
            == len(response.results)
        ):
            raise EvaluationArtifactInvalidError(
                "The evaluation result could not be validated."
            )

        return response

    def read_latest_csv(self) -> bytes:
        if not self.csv_path.is_file():
            raise EvaluationArtifactNotFoundError(
                "No evaluation CSV result is available."
            )
        try:
            content = self.csv_path.read_bytes()
        except OSError as exc:
            raise EvaluationArtifactInvalidError(
                "The evaluation CSV result could not be read."
            ) from exc
        if not content.strip():
            raise EvaluationArtifactInvalidError(
                "The evaluation CSV result could not be read."
            )
        return content
