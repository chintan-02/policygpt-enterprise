from app.rag.prompts import RAG_SYSTEM_PROMPT, build_rag_user_prompt


def _normalized_system_prompt() -> str:
    return " ".join(RAG_SYSTEM_PROMPT.lower().split())


def test_prompt_requires_every_part_of_multi_part_questions() -> None:
    prompt = _normalized_system_prompt()

    assert "multi-part questions" in prompt
    assert "explicitly answer every distinct part" in prompt


def test_prompt_preserves_frequency_qualifiers() -> None:
    prompt = _normalized_system_prompt()

    assert "one-time versus recurring frequency" in prompt
    assert "never omit a qualifier" in prompt


def test_prompt_preserves_limits_and_deadlines() -> None:
    prompt = _normalized_system_prompt()

    assert "maximum or minimum amounts" in prompt
    assert "deadlines and time limits" in prompt


def test_prompt_preserves_approvals_exceptions_and_conditions() -> None:
    prompt = _normalized_system_prompt()

    assert "prerequisites and approvals" in prompt
    assert "exceptions" in prompt
    assert "conditions" in prompt


def test_prompt_preserves_negative_limits_and_unacceptable_substitutes() -> None:
    prompt = _normalized_system_prompt()

    assert "prohibited or unacceptable substitutes" in prompt
    assert "state relevant negative limitations" in prompt


def test_prompt_remains_concise_and_evidence_only() -> None:
    prompt = _normalized_system_prompt()
    user_prompt = build_rag_user_prompt(
        question="What is required, and when?",
        evidence_context="Supplied policy evidence.",
    ).lower()

    assert "only from the provided citation evidence" in prompt
    assert "do not copy irrelevant evidence" in prompt
    assert "using only the citation evidence above" in user_prompt
    assert "if the evidence is insufficient" in user_prompt


def test_user_prompt_includes_a_final_completeness_check() -> None:
    user_prompt = " ".join(
        build_rag_user_prompt(
            question="What is required, and when?",
            evidence_context="Supplied policy evidence.",
        )
        .lower()
        .split()
    )

    assert "for each distinct part of the question" in user_prompt
    assert "state the complete applicable rule" in user_prompt
    assert "prohibited and unacceptable substitutes" in user_prompt
    assert "state relevant negative limitations explicitly" in user_prompt
    assert (
        "check that no such qualifier or question part was omitted" in user_prompt
    )
