from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class MatchCategory(str, Enum):
    SKILL = "skill_match"
    EXPERIENCE = "experience_match"
    CULTURE = "culture_fit"

class InterviewStage(str, Enum):
    SCREENING = "screening"
    ROLE_SPECIFIC = "role_specific"
    BEHAVIORAL_STAR = "behavioral_star"
    CURVEBALL = "curveball_stress"
    SALARY_NEGOTIATION = "salary_negotiation"
    CLOSING = "closing"

@dataclass
class JobPosting:
    job_id: str
    title: str
    company: str
    description: str          # raw text
    requirements: str         # raw text
    industry_sector: str
    seniority_level: str
    location: str
    salary_range: Optional[str] = None
    posted_date: Optional[str] = None
    source_url: Optional[str] = None
    semiotic_tags: Optional[dict] = field(default_factory=dict)  # hasil analisis semiotik

@dataclass
class CandidateProfile:
    user_id: str
    raw_cv_text: str
    skills: list[str] = field(default_factory=list)
    experience_years: Optional[float] = None
    preferences: dict = field(default_factory=dict)  # e.g. {"work_culture": "santai"}
