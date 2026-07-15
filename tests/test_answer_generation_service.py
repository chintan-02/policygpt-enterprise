from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.document import CitationCard
from app.services.answer_generation_service import AnswerGenerationService


class ProviderHTTPError(Exception):
    def __init__(
        self,
        status_code: int,
        *,
        headers: dict[str, str] | None = None,
        message: str = "provider request failed",
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = SimpleNamespace(
            status_code=status_code,
            headers=headers or {},
        )


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "DEBUG": False,
        "LLM_PROVIDER": "groq",
        "GROQ_API_KEY": "groq-test-secret",
        "GROQ_MODEL_NAME": "groq-test-model",
        "OPENAI_API_KEY": None,
        "OPENAI_MODEL_NAME": "openai-test-model",
        "LLM_MAX_RETRIES": 2,
        "LLM_RETRY_BASE_DELAY_SECONDS": 1.0,
        "LLM_RETRY_MAX_DELAY_SECONDS": 5.0,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def _service(**settings_overrides: object) -> AnswerGenerationService:
    service = AnswerGenerationService.__new__(AnswerGenerationService)
    service.settings = _settings(**settings_overrides)
    return service


def _citation() -> CitationCard:
    return CitationCard(
        document_id="document-1",
        filename="policy.pdf",
        page_number=5,
        section_title="Remote Work",
        chunk_index=1,
        excerpt="Public citation excerpt.",
        evidence_text="Private policy evidence that must never be logged.",
        retrieval_score=0.8,
    )


def _completion(answer: str = "Grounded answer.") -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=answer))]
    )


def _client_with_side_effect(side_effect: object) -> Mock:
    client = Mock()
    client.chat.completions.create.side_effect = side_effect
    return client


def test_groq_succeeds_on_first_attempt() -> None:
    client = _client_with_side_effect([_completion()])
    service = _service()

    with (
        patch(
            "app.services.answer_generation_service.OpenAI",
            return_value=client,
        ),
        patch("app.services.answer_generation_service.time.sleep") as sleep,
    ):
        result = service.generate_answer("What is covered?", [_citation()])

    assert result == ("Grounded answer.", "groq-test-model", "groq", False)
    assert client.chat.completions.create.call_count == 1
    sleep.assert_not_called()


def test_rate_limit_then_success_retries_once() -> None:
    client = _client_with_side_effect(
        [ProviderHTTPError(429), _completion("Recovered answer.")]
    )
    service = _service()

    with (
        patch(
            "app.services.answer_generation_service.OpenAI",
            return_value=client,
        ),
        patch("app.services.answer_generation_service.time.sleep") as sleep,
    ):
        result = service.generate_answer("What is covered?", [_citation()])

    assert result[0] == "Recovered answer."
    assert client.chat.completions.create.call_count == 2
    sleep.assert_called_once_with(1.0)


def test_timeout_then_success_retries_once() -> None:
    client = _client_with_side_effect(
        [TimeoutError("temporary timeout"), _completion("Recovered answer.")]
    )
    service = _service()

    with (
        patch(
            "app.services.answer_generation_service.OpenAI",
            return_value=client,
        ),
        patch("app.services.answer_generation_service.time.sleep") as sleep,
    ):
        result = service.generate_answer("What is covered?", [_citation()])

    assert result[0] == "Recovered answer."
    assert client.chat.completions.create.call_count == 2
    sleep.assert_called_once_with(1.0)


def test_connection_failure_then_success_retries_once() -> None:
    client = _client_with_side_effect(
        [ConnectionError("temporary connection failure"), _completion()]
    )
    service = _service()

    with (
        patch(
            "app.services.answer_generation_service.OpenAI",
            return_value=client,
        ),
        patch("app.services.answer_generation_service.time.sleep") as sleep,
    ):
        result = service.generate_answer("What is covered?", [_citation()])

    assert result[0] == "Grounded answer."
    assert client.chat.completions.create.call_count == 2
    sleep.assert_called_once_with(1.0)


@pytest.mark.parametrize("status_code", [500, 502, 503, 504])
def test_transient_server_error_then_success_retries(status_code: int) -> None:
    client = _client_with_side_effect(
        [ProviderHTTPError(status_code), _completion("Recovered answer.")]
    )
    service = _service()

    with (
        patch(
            "app.services.answer_generation_service.OpenAI",
            return_value=client,
        ),
        patch("app.services.answer_generation_service.time.sleep") as sleep,
    ):
        result = service.generate_answer("What is covered?", [_citation()])

    assert result[0] == "Recovered answer."
    sleep.assert_called_once_with(1.0)


def test_retry_after_header_is_respected_and_capped() -> None:
    client = _client_with_side_effect(
        [
            ProviderHTTPError(429, headers={"Retry-After": "30"}),
            _completion("Recovered answer."),
        ]
    )
    service = _service(LLM_RETRY_MAX_DELAY_SECONDS=2.0)

    with (
        patch(
            "app.services.answer_generation_service.OpenAI",
            return_value=client,
        ),
        patch("app.services.answer_generation_service.time.sleep") as sleep,
    ):
        service.generate_answer("What is covered?", [_citation()])

    sleep.assert_called_once_with(2.0)


def test_maximum_retries_reaches_citation_only_fallback() -> None:
    client = _client_with_side_effect(
        [ProviderHTTPError(429), ProviderHTTPError(429), ProviderHTTPError(429)]
    )
    service = _service()

    with (
        patch(
            "app.services.answer_generation_service.OpenAI",
            return_value=client,
        ),
        patch("app.services.answer_generation_service.time.sleep") as sleep,
    ):
        answer, model, provider, fallback_used = service.generate_answer(
            "What is covered?",
            [_citation()],
        )

    assert "Review the citation evidence" in answer
    assert (model, provider, fallback_used) == (
        "groq-test-model",
        "groq",
        True,
    )
    assert client.chat.completions.create.call_count == 3
    assert [call.args[0] for call in sleep.call_args_list] == [1.0, 2.0]


@pytest.mark.parametrize("status_code", [400, 401])
def test_permanent_client_error_is_not_retried(status_code: int) -> None:
    client = _client_with_side_effect([ProviderHTTPError(status_code)])
    service = _service()

    with (
        patch(
            "app.services.answer_generation_service.OpenAI",
            return_value=client,
        ),
        patch("app.services.answer_generation_service.time.sleep") as sleep,
    ):
        result = service.generate_answer("What is covered?", [_citation()])

    assert result[3] is True
    assert client.chat.completions.create.call_count == 1
    sleep.assert_not_called()


def test_secondary_provider_succeeds_after_primary_retries_fail() -> None:
    primary_client = _client_with_side_effect(
        [ProviderHTTPError(429), ProviderHTTPError(429), ProviderHTTPError(429)]
    )
    secondary_client = _client_with_side_effect(
        [_completion("Secondary provider answer.")]
    )
    service = _service(OPENAI_API_KEY="openai-test-secret")

    with (
        patch(
            "app.services.answer_generation_service.OpenAI",
            side_effect=[primary_client, secondary_client],
        ),
        patch("app.services.answer_generation_service.time.sleep"),
    ):
        result = service.generate_answer("What is covered?", [_citation()])

    assert result == (
        "Secondary provider answer.",
        "openai-test-model",
        "openai",
        False,
    )
    assert primary_client.chat.completions.create.call_count == 3
    assert secondary_client.chat.completions.create.call_count == 1


def test_both_providers_fail_and_citation_only_fallback_remains() -> None:
    primary_client = _client_with_side_effect([ProviderHTTPError(401)])
    secondary_client = _client_with_side_effect([ProviderHTTPError(400)])
    service = _service(OPENAI_API_KEY="openai-test-secret")

    with (
        patch(
            "app.services.answer_generation_service.OpenAI",
            side_effect=[primary_client, secondary_client],
        ),
        patch("app.services.answer_generation_service.time.sleep") as sleep,
    ):
        answer, model, provider, fallback_used = service.generate_answer(
            "What is covered?",
            [_citation()],
        )

    assert "Review the citation evidence" in answer
    assert (model, provider, fallback_used) == (
        "openai-test-model",
        "openai",
        True,
    )
    sleep.assert_not_called()


def test_retry_logging_contains_only_safe_metadata() -> None:
    sensitive_error = ProviderHTTPError(
        429,
        headers={"Retry-After": "1.5"},
        message=(
            "GROQ_API_KEY=groq-test-secret system_prompt=hidden "
            "evidence_text=private complete request payload"
        ),
    )
    client = _client_with_side_effect(
        [sensitive_error, _completion("Recovered answer.")]
    )
    service = _service()

    with (
        patch(
            "app.services.answer_generation_service.OpenAI",
            return_value=client,
        ),
        patch("app.services.answer_generation_service.time.sleep"),
        patch(
            "app.services.answer_generation_service.logger.warning"
        ) as warning,
    ):
        service.generate_answer("What is covered?", [_citation()])

    _, log_fields = warning.call_args_list[0]
    assert log_fields == {
        "provider": "groq",
        "model_name": "groq-test-model",
        "attempt_number": 1,
        "max_attempts": 3,
        "error_type": "ProviderHTTPError",
        "status_code": 429,
        "retry_after_seconds": 1.5,
        "will_retry": True,
        "secondary_provider_attempted": False,
        "error_message": (
            "Provider request failed with HTTP 429 (ProviderHTTPError)."
        ),
    }
    serialized_logs = repr(warning.call_args_list).lower()
    for forbidden_value in (
        "groq-test-secret",
        "system_prompt",
        "evidence_text",
        "private policy evidence",
        "request payload",
    ):
        assert forbidden_value not in serialized_logs


@pytest.mark.parametrize(
    "overrides",
    [
        {"LLM_MAX_RETRIES": -1},
        {"LLM_MAX_RETRIES": 6},
        {"LLM_RETRY_BASE_DELAY_SECONDS": -0.1},
        {"LLM_RETRY_MAX_DELAY_SECONDS": -0.1},
        {
            "LLM_RETRY_BASE_DELAY_SECONDS": 2.0,
            "LLM_RETRY_MAX_DELAY_SECONDS": 1.0,
        },
    ],
)
def test_invalid_retry_configuration_is_rejected(
    overrides: dict[str, float | int],
) -> None:
    with pytest.raises(ValidationError):
        _settings(**overrides)
