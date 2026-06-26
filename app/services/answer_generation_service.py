from openai import OpenAI

from app.core.config import get_settings
from app.core.exceptions import ConfigurationException, ServiceException
from app.rag.prompts import RAG_SYSTEM_PROMPT, build_rag_user_prompt
from app.schemas.document import CitationCard


class AnswerGenerationService:
    """
    Generate final RAG answers using citation evidence only.

    Provider support:
    - groq: OpenAI-compatible API base URL
    - openai: OpenAI API
    - none: citation-only fallback mode
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_answer(
        self,
        question: str,
        citations: list[CitationCard],
    ) -> tuple[str, str | None, str, bool]:
        """
        Returns:
            answer, model_name, provider_name, fallback_used
        """

        fallback_answer = (
            "I could not find enough supporting evidence in the uploaded "
            "documents to answer this reliably."
        )

        if not citations:
            return fallback_answer, None, self.settings.llm_provider, True

        if not self.settings.enable_llm_answer or self.settings.llm_provider == "none":
            citation_only_answer = (
                "LLM answer generation is disabled. Review the citation evidence "
                "below for the most relevant policy information."
            )
            return citation_only_answer, None, "none", True

        evidence_context = self._build_evidence_context(citations)

        user_prompt = build_rag_user_prompt(
            question=question,
            evidence_context=evidence_context,
        )

        if self.settings.llm_provider == "groq":
            return self._generate_with_groq(user_prompt)

        if self.settings.llm_provider == "openai":
            return self._generate_with_openai(user_prompt)

        citation_only_answer = (
            "No supported LLM provider is configured. Review the citation evidence "
            "below for the most relevant policy information."
        )
        return citation_only_answer, None, "none", True

    def _generate_with_groq(self, user_prompt: str) -> tuple[str, str, str, bool]:
        if not self.settings.groq_api_key:
            citation_only_answer = (
                "Groq is selected, but GROQ_API_KEY is missing. Review the citation "
                "evidence below for the most relevant policy information."
            )
            return citation_only_answer, self.settings.groq_model_name, "groq", True

        client = OpenAI(
            api_key=self.settings.groq_api_key,
            base_url=self.settings.groq_base_url,
        )

        return self._call_chat_completion(
            client=client,
            model_name=self.settings.groq_model_name,
            provider_name="groq",
            user_prompt=user_prompt,
        )

    def _generate_with_openai(self, user_prompt: str) -> tuple[str, str, str, bool]:
        if not self.settings.openai_api_key:
            citation_only_answer = (
                "OpenAI is selected, but OPENAI_API_KEY is missing. Review the citation "
                "evidence below for the most relevant policy information."
            )
            return citation_only_answer, self.settings.openai_model_name, "openai", True

        client = OpenAI(api_key=self.settings.openai_api_key)

        return self._call_chat_completion(
            client=client,
            model_name=self.settings.openai_model_name,
            provider_name="openai",
            user_prompt=user_prompt,
        )

    def _call_chat_completion(
        self,
        client: OpenAI,
        model_name: str,
        provider_name: str,
        user_prompt: str,
    ) -> tuple[str, str, str, bool]:
        try:
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

            return answer.strip(), model_name, provider_name, False

        except ConfigurationException:
            raise
        except Exception as exc:
            raise ServiceException(
                f"Failed to generate answer with {provider_name}: {exc}"
            ) from exc

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