import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Literal

import structlog
from openai import OpenAI

from app.core.config import get_settings
from app.core.exceptions import ServiceException
from app.rag.prompts import RAG_SYSTEM_PROMPT, build_rag_user_prompt
from app.schemas.document import CitationCard

logger = structlog.get_logger(__name__)

ProviderName = Literal["groq", "openai"]
_TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}
_TRANSIENT_ERROR_TYPES = {
    "APIConnectionError",
    "APITimeoutError",
    "ConnectError",
    "ConnectionError",
    "ReadTimeout",
    "TimeoutError",
    "TimeoutException",
}


class AnswerGenerationService:
    """
    Generate final RAG answers using citation evidence only.

    Transient provider errors receive bounded retries. If the configured primary
    provider still fails, a configured secondary provider is attempted once
    through the same bounded policy before citation-only fallback is returned.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_answer(
        self,
        question: str,
        citations: list[CitationCard],
    ) -> tuple[str, str | None, str, bool]:
        """Return answer, model name, provider name, and fallback status."""

        unsupported_answer = (
            "I could not find enough supporting evidence in the uploaded "
            "documents to answer this reliably."
        )

        if not citations:
            return unsupported_answer, None, self.settings.llm_provider, True

        if (
            not self.settings.enable_llm_answer
            or self.settings.llm_provider == "none"
        ):
            return self._citation_only_fallback(provider_name="none", model_name=None)

        evidence_context = self._build_evidence_context(citations)
        user_prompt = build_rag_user_prompt(
            question=question,
            evidence_context=evidence_context,
        )

        primary_provider: ProviderName = self.settings.llm_provider
        providers = self._provider_sequence(primary_provider)
        last_provider: str = primary_provider
        last_model: str | None = self._provider_model(primary_provider)

        for provider_index, provider_name in enumerate(providers):
            model_name = self._provider_model(provider_name)
            last_provider = provider_name
            last_model = model_name
            secondary_provider_attempted = provider_index > 0

            if not self._provider_is_configured(provider_name):
                self._log_unconfigured_provider(
                    provider_name=provider_name,
                    model_name=model_name,
                    secondary_provider_attempted=secondary_provider_attempted,
                )
                continue

            answer = self._generate_with_provider(
                provider_name=provider_name,
                model_name=model_name,
                user_prompt=user_prompt,
                secondary_provider_attempted=secondary_provider_attempted,
            )
            if answer is not None:
                return answer, model_name, provider_name, False

        return self._citation_only_fallback(
            provider_name=last_provider,
            model_name=last_model,
        )

    def _provider_sequence(
        self,
        primary_provider: ProviderName,
    ) -> list[ProviderName]:
        secondary_provider: ProviderName = (
            "openai" if primary_provider == "groq" else "groq"
        )
        providers = [primary_provider]
        if self._provider_is_configured(secondary_provider):
            providers.append(secondary_provider)
        return providers

    def _provider_is_configured(self, provider_name: ProviderName) -> bool:
        return bool(
            self._provider_api_key(provider_name)
            and self._provider_model(provider_name)
        )

    def _provider_api_key(self, provider_name: ProviderName) -> str | None:
        if provider_name == "groq":
            return self.settings.groq_api_key
        return self.settings.openai_api_key

    def _provider_model(self, provider_name: ProviderName) -> str:
        if provider_name == "groq":
            return self.settings.groq_model_name
        return self.settings.openai_model_name

    def _create_provider_client(self, provider_name: ProviderName) -> OpenAI:
        api_key = self._provider_api_key(provider_name)
        if provider_name == "groq":
            return OpenAI(
                api_key=api_key,
                base_url=self.settings.groq_base_url,
            )
        return OpenAI(api_key=api_key)

    def _generate_with_provider(
        self,
        *,
        provider_name: ProviderName,
        model_name: str,
        user_prompt: str,
        secondary_provider_attempted: bool,
    ) -> str | None:
        max_attempts = self.settings.llm_max_retries + 1
        client: OpenAI | None = None

        for attempt_number in range(1, max_attempts + 1):
            try:
                if client is None:
                    client = self._create_provider_client(provider_name)

                completion = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": RAG_SYSTEM_PROMPT,
                        },
                        {
                            "role": "user",
                            "content": user_prompt,
                        },
                    ],
                    temperature=self.settings.llm_temperature,
                    max_tokens=self.settings.llm_max_output_tokens,
                )

                answer = completion.choices[0].message.content
                if not answer or not answer.strip():
                    raise ServiceException("The LLM returned an empty answer.")
                return answer.strip()
            except Exception as exc:
                status_code = self._status_code(exc)
                retry_after_seconds = self._retry_after_seconds(exc)
                transient = self._is_transient_error(exc, status_code)
                will_retry = transient and attempt_number < max_attempts

                logger.warning(
                    "llm_provider_attempt_failed",
                    provider=provider_name,
                    model_name=model_name,
                    attempt_number=attempt_number,
                    max_attempts=max_attempts,
                    error_type=type(exc).__name__[:100],
                    status_code=status_code,
                    retry_after_seconds=retry_after_seconds,
                    will_retry=will_retry,
                    secondary_provider_attempted=secondary_provider_attempted,
                    error_message=self._safe_error_message(exc, status_code),
                )

                if not will_retry:
                    return None

                retry_delay = self._retry_delay_seconds(
                    failed_attempt_number=attempt_number,
                    retry_after_seconds=retry_after_seconds,
                )
                if retry_delay > 0:
                    time.sleep(retry_delay)

        return None

    def _is_transient_error(
        self,
        exc: Exception,
        status_code: int | None,
    ) -> bool:
        if status_code is not None:
            return status_code in _TRANSIENT_STATUS_CODES
        return (
            isinstance(exc, (TimeoutError, ConnectionError))
            or type(exc).__name__ in _TRANSIENT_ERROR_TYPES
        )

    def _status_code(self, exc: Exception) -> int | None:
        status_code = getattr(exc, "status_code", None)
        if status_code is None:
            response = getattr(exc, "response", None)
            status_code = getattr(response, "status_code", None)
        if isinstance(status_code, int) and not isinstance(status_code, bool):
            return status_code
        return None

    def _retry_after_seconds(self, exc: Exception) -> float | None:
        response = getattr(exc, "response", None)
        headers = getattr(response, "headers", None)
        if headers is None:
            return None

        try:
            raw_value = headers.get("Retry-After")
        except (AttributeError, TypeError):
            return None
        if raw_value is None:
            return None

        try:
            delay = max(float(raw_value), 0.0)
        except (TypeError, ValueError):
            try:
                retry_at = parsedate_to_datetime(str(raw_value))
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=timezone.utc)
                delay = max(
                    (retry_at - datetime.now(timezone.utc)).total_seconds(),
                    0.0,
                )
            except (TypeError, ValueError, OverflowError):
                return None

        return round(
            min(delay, self.settings.llm_retry_max_delay_seconds),
            3,
        )

    def _retry_delay_seconds(
        self,
        *,
        failed_attempt_number: int,
        retry_after_seconds: float | None,
    ) -> float:
        exponential_delay = (
            self.settings.llm_retry_base_delay_seconds
            * (2 ** (failed_attempt_number - 1))
        )
        requested_delay = retry_after_seconds or 0.0
        return min(
            max(exponential_delay, requested_delay),
            self.settings.llm_retry_max_delay_seconds,
        )

    def _safe_error_message(
        self,
        exc: Exception,
        status_code: int | None,
    ) -> str:
        error_type = type(exc).__name__[:100]
        if status_code is not None:
            message = (
                f"Provider request failed with HTTP {status_code} "
                f"({error_type})."
            )
        else:
            message = f"Provider request failed ({error_type})."
        return message[:300]

    def _log_unconfigured_provider(
        self,
        *,
        provider_name: ProviderName,
        model_name: str,
        secondary_provider_attempted: bool,
    ) -> None:
        logger.warning(
            "llm_provider_not_configured",
            provider=provider_name,
            model_name=model_name,
            attempt_number=0,
            max_attempts=self.settings.llm_max_retries + 1,
            error_type="MissingProviderConfiguration",
            status_code=None,
            retry_after_seconds=None,
            will_retry=False,
            secondary_provider_attempted=secondary_provider_attempted,
            error_message="Provider API key or model is not configured.",
        )

    def _citation_only_fallback(
        self,
        provider_name: str,
        model_name: str | None,
    ) -> tuple[str, str | None, str, bool]:
        answer = (
            "I found supporting citation evidence, but LLM answer generation is "
            "not available right now. Review the citation evidence below for the "
            "most relevant policy information."
        )
        return answer, model_name, provider_name, True

    def _build_evidence_context(self, citations: list[CitationCard]) -> str:
        evidence_blocks: list[str] = []

        for index, citation in enumerate(citations, start=1):
            section = citation.section_title or "Unknown section"
            evidence_blocks.append(
                "\n".join(
                    [
                        f"[Evidence {index}]",
                        f"Document: {citation.filename}",
                        f"Page: {citation.page_number}",
                        f"Section: {section}",
                        f"Retrieval score: {citation.retrieval_score}",
                        f"Evidence text: {citation.evidence_text}",
                    ]
                )
            )

        return "\n\n".join(evidence_blocks)
