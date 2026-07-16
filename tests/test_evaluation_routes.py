import os
from pathlib import Path

from fastapi.testclient import TestClient

os.environ["DEBUG"] = "false"

from app.api.main import create_app
from app.api.routes.evaluations import get_evaluation_results_service
from app.services.evaluation_results_service import EvaluationResultsService
from tests.test_api_evaluation_results_service import write_artifact


def test_json_route_success(tmp_path: Path) -> None:
    write_artifact(tmp_path)
    app = create_app()
    app.dependency_overrides[get_evaluation_results_service] = lambda: (
        EvaluationResultsService(
            "eval/results/latest_eval_results.json",
            repository_root=tmp_path,
        )
    )

    response = TestClient(app).get("/api/v1/evaluations/latest")

    assert response.status_code == 200
    assert response.json()["run"]["run_id"] == "run-123"
    assert response.json()["artifact"]["question_count"] == 1
    assert response.headers["content-type"].startswith("application/json")


def test_json_route_not_found_is_safe(tmp_path: Path) -> None:
    app = create_app()
    app.dependency_overrides[get_evaluation_results_service] = lambda: (
        EvaluationResultsService(
            "eval/results/latest_eval_results.json",
            repository_root=tmp_path,
        )
    )

    response = TestClient(app).get("/api/v1/evaluations/latest")

    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "EVALUATION_NOT_FOUND",
        "message": "No evaluation result is available.",
    }
    assert str(tmp_path) not in response.text


def test_json_route_validation_failure_is_safe(tmp_path: Path) -> None:
    path = write_artifact(tmp_path)
    path.write_text("{invalid", encoding="utf-8")
    app = create_app()
    app.dependency_overrides[get_evaluation_results_service] = lambda: (
        EvaluationResultsService(
            "eval/results/latest_eval_results.json",
            repository_root=tmp_path,
        )
    )

    response = TestClient(app).get("/api/v1/evaluations/latest")

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "EVALUATION_INVALID",
        "message": "The evaluation result could not be validated.",
    }
    assert str(tmp_path) not in response.text


def test_csv_route_success(tmp_path: Path) -> None:
    json_path = write_artifact(tmp_path)
    json_path.with_suffix(".csv").write_bytes(b"id,result\ncase-1,passed\n")
    app = create_app()
    app.dependency_overrides[get_evaluation_results_service] = lambda: (
        EvaluationResultsService(
            "eval/results/latest_eval_results.json",
            repository_root=tmp_path,
        )
    )

    response = TestClient(app).get("/api/v1/evaluations/latest.csv")

    assert response.status_code == 200
    assert response.content == b"id,result\ncase-1,passed\n"
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        'attachment; filename="policygpt-latest-evaluation.csv"'
    )


def test_csv_route_not_found_is_safe(tmp_path: Path) -> None:
    write_artifact(tmp_path)
    app = create_app()
    app.dependency_overrides[get_evaluation_results_service] = lambda: (
        EvaluationResultsService(
            "eval/results/latest_eval_results.json",
            repository_root=tmp_path,
        )
    )

    response = TestClient(app).get("/api/v1/evaluations/latest.csv")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EVALUATION_NOT_FOUND"
    assert str(tmp_path) not in response.text
