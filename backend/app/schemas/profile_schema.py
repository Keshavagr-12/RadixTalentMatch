
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


CategoryCode = Literal[
    "COD", "DSA", "OOD", "APTI", "COMM", "AI",
    "CLOUD", "SQL", "SWE", "SYSD", "NETW", "OS", "OTHER"
]

Confidence = Literal["high", "medium", "low"]


class Education(BaseModel):
    degree: str
    institution: str
    graduation_year: int | None = None
    field_of_study: str | None = None


class Skill(BaseModel):
    skill_name: str = Field(min_length=1, max_length=100)
    category_code: CategoryCode
    evidence: str = ""
    confidence: Confidence = "medium"


class Hackathon(BaseModel):
    name: str
    achievement: str | None = None
    year: int | None = None


class Internship(BaseModel):
    company: str
    role: str
    description: str = ""
    duration: str | None = None


class Certification(BaseModel):
    name: str
    issuer: str | None = None
    year: int | None = None


class ProfileCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    education: list[Education] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    hackathons: list[Hackathon] = Field(default_factory=list)
    internships: list[Internship] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    preferred_roles: list[str] = Field(default_factory=list)
    cv_file: str | None = None


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    education: list[Education] | None = None
    skills: list[Skill] | None = None
    hackathons: list[Hackathon] | None = None
    internships: list[Internship] | None = None
    certifications: list[Certification] | None = None
    preferred_roles: list[str] | None = None
    cv_file: str | None = None


class ProfileResponse(ProfileCreate):
    id: str
