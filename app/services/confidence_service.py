from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "being",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "had",
    "has",
    "have",
    "how",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "may",
    "might",
    "of",
    "on",
    "or",
    "should",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "to",
    "under",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "whom",
    "why",
    "with",
    "would",
}
NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
EXTERNAL_AUTHORITY_PATTERNS = (
    re.compile(r"\b(?:does|what)\s+.+?\blaw\s+(?:require|say|mandate)\b"),
    re.compile(r"\brequired\s+by\s+law\b"),
    re.compile(r"\blegal(?:ly)?\s+(?:required|entitled|enforceable|obligated)\b"),
    re.compile(r"\blegal\s+requirement\b"),
    re.compile(r"\bstatutory\s+(?:requirement|entitlement|obligation)\b"),
    re.compile(r"\bregulation(?:s)?\s+(?:require|mandate|say)\b"),
    re.compile(r"\bcourt\s+(?:require|order|rule)"),
    re.compile(r"\bunder\s+.+?\blaw\b"),
    re.compile(r"\bseverance\b.+?\blaw\b"),
)
SCOPE_DISCLAIMER_MARKERS = (
    "not legal advice",
    "applicable law",
    "local law",
    "document limits",
    "not an employment contract",
    "does not guarantee",
    "written employment agreements take priority",
)
SCOPE_RISK_REASON = (
    "The question asks for an external legal requirement that is not directly "
    "established by the uploaded policy evidence."
)


@dataclass(frozen=True)
class ConfidenceConfig:
    candidate_retrieval_floor: float = 0.30
    direct_support_score_floor: float = 0.35
    direct_support_coverage_min: float = 0.60
    weak_confidence_threshold: float = 0.40
    moderate_confidence_threshold: float = 0.55
    strong_confidence_threshold: float = 0.75
    max_evidence_chunks: int = 3


@dataclass(frozen=True)
class EvidenceCandidate:
    text: str
    score: float


@dataclass(frozen=True)
class ConfidenceAssessment:
    answerability_score: float
    evidence_status: str
    answer_ready: bool
    top_retrieval_score: float
    average_retrieval_score: float
    retrieval_margin: float
    lexical_coverage: float
    top_chunk_lexical_coverage: float
    numeric_consistency: float | None
    numeric_mismatch: bool
    query_numeric_claims: list[str]
    evidence_numeric_claims: list[str]
    missing_numeric_claims: list[str]
    scope_risk: bool
    scope_risk_reason: str | None
    matched_query_terms: list[str]
    missing_query_terms: list[str]
    direct_support: bool
    decision_reasons: list[str]

    @property
    def public_confidence_score(self) -> float:
        if not self.answer_ready:
            return 0.0
        return self.answerability_score


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    characters = [
        character if character.isalnum() or character in {"%", "$"} else " "
        for character in normalized
    ]
    return " ".join("".join(characters).split())


def normalize_token(token: str) -> str:
    normalized = normalize_text(token).replace(" ", "")
    if not normalized or normalized.isnumeric():
        return normalized

    if len(normalized) > 4 and normalized.endswith("ies"):
        normalized = f"{normalized[:-3]}y"
    elif len(normalized) > 3 and normalized.endswith("s"):
        if not normalized.endswith(("ss", "us", "is")):
            normalized = normalized[:-1]

    if len(normalized) > 5 and normalized.endswith("ied"):
        return f"{normalized[:-3]}y"

    if len(normalized) > 4 and normalized.endswith("ed"):
        stem = normalized[:-2]
        if stem.endswith(("v", "z")) or stem in {
            "clos",
            "hir",
            "mov",
            "requir",
            "shar",
            "us",
        }:
            stem = f"{stem}e"
        return stem

    if len(normalized) > 5 and normalized.endswith("ing"):
        stem = normalized[:-3]
        if len(stem) > 2 and stem[-1] == stem[-2] and not stem.endswith("ss"):
            stem = stem[:-1]
        if stem.endswith(("v", "z")):
            stem = f"{stem}e"
        return stem

    if len(normalized) > 4 and normalized.endswith("ly"):
        return normalized[:-2]

    return normalized


def tokenize_significant_terms(value: str) -> list[str]:
    normalized = normalize_text(value)
    terms: set[str] = set()

    for raw_token in normalized.split():
        if raw_token in STOPWORDS:
            continue
        token = normalize_token(raw_token)
        if not token or token in STOPWORDS:
            continue
        if len(token) == 1 and not token.isnumeric():
            continue
        terms.add(token)

    return sorted(terms)


def calculate_lexical_coverage(
    query: str,
    evidence_text: str,
) -> tuple[float, list[str], list[str]]:
    query_terms = set(tokenize_significant_terms(query))
    if not query_terms:
        return 0.0, [], []

    evidence_terms = set(tokenize_significant_terms(evidence_text))
    matched_terms = sorted(query_terms & evidence_terms)
    missing_terms = sorted(query_terms - evidence_terms)
    coverage = round(len(matched_terms) / len(query_terms), 4)
    return coverage, matched_terms, missing_terms


def _normalize_number(value: str) -> str:
    try:
        number = Decimal(value.replace(",", ""))
    except InvalidOperation:
        return value

    normalized = format(number.normalize(), "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized


def extract_numeric_claims(value: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    claims: set[str] = set()
    consumed_spans: list[tuple[int, int]] = []

    currency_pattern = re.compile(
        r"\b(cad|usd|eur|gbp)\s*\$?\s*(\d[\d,]*(?:\.\d+)?)\b"
    )
    money_pattern = re.compile(r"\$\s*(\d[\d,]*(?:\.\d+)?)\b")
    percentage_pattern = re.compile(r"\b(\d[\d,]*(?:\.\d+)?)\s*%")

    for match in currency_pattern.finditer(normalized):
        claims.add(f"{match.group(1).upper()}:{_normalize_number(match.group(2))}")
        consumed_spans.append(match.span())

    for match in money_pattern.finditer(normalized):
        if any(start <= match.start() < end for start, end in consumed_spans):
            continue
        claims.add(f"MONEY:{_normalize_number(match.group(1))}")
        consumed_spans.append(match.span())

    for match in percentage_pattern.finditer(normalized):
        claims.add(f"PERCENT:{_normalize_number(match.group(1))}")
        consumed_spans.append(match.span())

    remaining_characters = list(normalized)
    for start, end in consumed_spans:
        remaining_characters[start:end] = " " * (end - start)
    remaining = "".join(remaining_characters)

    for match in re.finditer(r"\b\d[\d,]*(?:\.\d+)?\b", remaining):
        claims.add(_normalize_number(match.group(0)))

    normalized_words = normalize_text(remaining).split()
    for word in normalized_words:
        if word in NUMBER_WORDS:
            claims.add(str(NUMBER_WORDS[word]))

    return sorted(claims)


def calculate_numeric_consistency(
    query: str,
    evidence_text: str,
) -> tuple[float | None, bool, list[str], list[str], list[str]]:
    query_claims = extract_numeric_claims(query)
    evidence_claims = extract_numeric_claims(evidence_text)

    if not query_claims:
        return None, False, [], evidence_claims, []

    missing_claims = sorted(set(query_claims) - set(evidence_claims))
    if missing_claims:
        return 0.0, True, query_claims, evidence_claims, missing_claims

    return 1.0, False, query_claims, evidence_claims, []


def detect_external_authority_request(query: str) -> bool:
    normalized_query = normalize_text(query)
    return any(pattern.search(normalized_query) for pattern in EXTERNAL_AUTHORITY_PATTERNS)


def _requested_authority_terms(query: str) -> set[str]:
    normalized_query = normalize_text(query)
    authority_terms: set[str] = set()
    pattern = re.compile(r"\b([a-z][a-z0-9-]+)\s+(?:employment\s+)?law\b")

    for match in pattern.finditer(normalized_query):
        term = match.group(1)
        if term not in {"the", "what", "does", "under", "employment", "local"}:
            authority_terms.add(normalize_token(term))

    return authority_terms


def calculate_scope_risk(
    query: str,
    evidence_text: str,
) -> tuple[bool, str | None]:
    if not detect_external_authority_request(query):
        return False, None

    normalized_evidence = normalize_text(evidence_text)
    authority_terms = _requested_authority_terms(query)
    authority_supported = not authority_terms or authority_terms <= set(
        tokenize_significant_terms(evidence_text)
    )

    excluded_terms = {
        "law",
        "legal",
        "require",
        "statutory",
        "regulation",
        "court",
        *authority_terms,
    }
    obligation_terms = set(tokenize_significant_terms(query)) - excluded_terms
    evidence_terms = set(tokenize_significant_terms(evidence_text))
    obligation_coverage = (
        len(obligation_terms & evidence_terms) / len(obligation_terms)
        if obligation_terms
        else 0.0
    )
    explicit_rule = bool(
        re.search(
            r"\b(?:must|requires?|required|entitled|shall|mandated)\b",
            normalized_evidence,
        )
    )
    disclaimer_only = any(
        marker in normalized_evidence for marker in SCOPE_DISCLAIMER_MARKERS
    ) and not explicit_rule

    if (
        authority_supported
        and obligation_coverage >= 0.6
        and explicit_rule
        and not disclaimer_only
    ):
        return False, None

    return True, SCOPE_RISK_REASON


def normalize_retrieval_margin(
    top_score: float,
    second_score: float | None,
) -> float:
    """Normalize separation; a single candidate conservatively receives zero."""

    if second_score is None:
        return 0.0
    margin = max(top_score - second_score, 0.0)
    return round(min(margin / 0.15, 1.0), 4)


def calculate_answerability_score(
    top_retrieval_score: float,
    average_retrieval_score: float,
    lexical_coverage: float,
    normalized_retrieval_margin: float,
) -> float:
    score = (
        0.35 * top_retrieval_score
        + 0.15 * average_retrieval_score
        + 0.45 * lexical_coverage
        + 0.05 * normalized_retrieval_margin
    )
    return round(max(0.0, min(1.0, score)), 4)


def assess_confidence(
    query: str,
    candidates: list[EvidenceCandidate],
    config: ConfidenceConfig,
) -> ConfidenceAssessment:
    usable_candidates = sorted(
        (
            candidate
            for candidate in candidates
            if isinstance(candidate.text, str)
            and candidate.text.strip()
            and isinstance(candidate.score, (int, float))
            and not isinstance(candidate.score, bool)
            and math.isfinite(candidate.score)
            and config.candidate_retrieval_floor <= candidate.score <= 1.0
        ),
        key=lambda candidate: candidate.score,
        reverse=True,
    )[: config.max_evidence_chunks]

    combined_evidence = "\n".join(candidate.text for candidate in usable_candidates)
    top_evidence = usable_candidates[0].text if usable_candidates else ""
    top_score = usable_candidates[0].score if usable_candidates else 0.0
    average_score = (
        sum(candidate.score for candidate in usable_candidates)
        / len(usable_candidates)
        if usable_candidates
        else 0.0
    )
    second_score = usable_candidates[1].score if len(usable_candidates) > 1 else None
    retrieval_margin = normalize_retrieval_margin(top_score, second_score)

    lexical_coverage, matched_terms, missing_terms = calculate_lexical_coverage(
        query,
        combined_evidence,
    )
    top_chunk_coverage, _, _ = calculate_lexical_coverage(query, top_evidence)
    (
        numeric_consistency,
        numeric_mismatch,
        query_numeric_claims,
        evidence_numeric_claims,
        missing_numeric_claims,
    ) = calculate_numeric_consistency(query, combined_evidence)
    scope_risk, scope_risk_reason = calculate_scope_risk(query, combined_evidence)
    answerability_score = calculate_answerability_score(
        top_score,
        average_score,
        lexical_coverage,
        retrieval_margin,
    )
    direct_support = (
        bool(usable_candidates)
        and top_score >= config.direct_support_score_floor
        and top_chunk_coverage >= config.direct_support_coverage_min
        and not numeric_mismatch
        and not scope_risk
    )

    hard_rejection_reasons: list[str] = []
    if not usable_candidates:
        hard_rejection_reasons.append(
            "No usable evidence met the configured candidate retrieval floor."
        )
    if numeric_mismatch:
        hard_rejection_reasons.append(
            "A material numeric claim in the question was not supported by the evidence."
        )
    if scope_risk:
        hard_rejection_reasons.append(scope_risk_reason or SCOPE_RISK_REASON)

    decision_reasons: list[str] = hard_rejection_reasons
    if hard_rejection_reasons:
        evidence_status = "insufficient"
    elif (
        answerability_score >= config.strong_confidence_threshold
        and lexical_coverage >= 0.25
    ):
        evidence_status = "strong"
        decision_reasons.append(
            "The calibrated score and lexical support reached the strong range."
        )
    elif (
        answerability_score >= config.moderate_confidence_threshold
        or direct_support
    ):
        evidence_status = "moderate"
        if direct_support and answerability_score < config.moderate_confidence_threshold:
            decision_reasons.append(
                "The highest-ranked evidence met the direct-support rule."
            )
        else:
            decision_reasons.append(
                "The calibrated score reached the moderate range."
            )
    elif answerability_score >= config.weak_confidence_threshold:
        evidence_status = "weak"
        decision_reasons.append(
            "Some evidence support was found, but it did not meet the answer threshold."
        )
    else:
        evidence_status = "insufficient"
        decision_reasons.append(
            "The calibrated evidence score was below the weak threshold."
        )

    answer_ready = evidence_status in {"moderate", "strong"}
    return ConfidenceAssessment(
        answerability_score=answerability_score,
        evidence_status=evidence_status,
        answer_ready=answer_ready,
        top_retrieval_score=round(top_score, 4),
        average_retrieval_score=round(average_score, 4),
        retrieval_margin=retrieval_margin,
        lexical_coverage=lexical_coverage,
        top_chunk_lexical_coverage=top_chunk_coverage,
        numeric_consistency=numeric_consistency,
        numeric_mismatch=numeric_mismatch,
        query_numeric_claims=query_numeric_claims,
        evidence_numeric_claims=evidence_numeric_claims,
        missing_numeric_claims=missing_numeric_claims,
        scope_risk=scope_risk,
        scope_risk_reason=scope_risk_reason,
        matched_query_terms=matched_terms,
        missing_query_terms=missing_terms,
        direct_support=direct_support,
        decision_reasons=decision_reasons,
    )
