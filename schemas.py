from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


CategoryCode = Literal[
    "COD",
    "DSA",
    "OOD",
    "APTI",
    "COMM",
    "AI",
    "CLOUD",
    "SQL",
    "SWE",
    "SYSD",
    "NETW",
    "OS",
    "OTHER",
]

ConfidenceLevel = Literal["high", "medium", "low"]


class Skill(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_name: str = Field(min_length=1)
    category_code: CategoryCode
    evidence: str = Field(min_length=1)
    confidence: ConfidenceLevel


class JobAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skills: list[Skill]