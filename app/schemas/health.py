from typing import Literal

from pydantic import BaseModel


class LivenessResponse(BaseModel):
    status: Literal["operational"] = "operational"
    service: str
    version: str
    environment: str


class DependencyCheck(BaseModel):
    status: Literal["ready", "unavailable"]


class ReadinessChecks(BaseModel):
    database: DependencyCheck
    vector_store: DependencyCheck


class ProviderMode(BaseModel):
    status: Literal["configured", "citation_only_fallback"]
    provider: Literal["groq", "openai", "none"]


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    checks: ReadinessChecks
    answer_generation: ProviderMode
