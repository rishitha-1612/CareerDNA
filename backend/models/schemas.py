from pydantic import BaseModel, HttpUrl, Field
from typing import List, Dict, Optional

class SkillEntry(BaseModel):
    name: str
    level: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str
    frequency: int = 1
    context_snippet: Optional[str] = None
class ResourceLink(BaseModel):
    title: str
    url: str
    source: str

class SkillGap(BaseModel):
    skill: str
    required_level: str
    current_level: Optional[str]
    gap_score: float
    priority: str
    weight: float = 1.0
    reasoning: str = ""
    links: List[ResourceLink] = []

class LearningModule(BaseModel):
    module_id: str
    title: str
    description: str
    skill_covered: str
    duration_hours: float
    difficulty: str
    prerequisites: List[str]
    resources: List[Dict[str, str]]
    order: int
    priority_tag: Optional[str] = None

class LearningPathway(BaseModel):
    session_id: str
    candidate_name: Optional[str]
    target_role: str
    total_duration_hours: float
    estimated_weeks: int
    skill_coverage_percent: float
    readiness_score: float = 0.0
    time_saved_hours: float = 0.0
    modules: List[LearningModule]
    reasoning_trace: List[str]
    skill_gaps: List[SkillGap]
    resume_skills: List[SkillEntry]
    jd_skills: List[SkillEntry]
    domain: str = "general"
    strengths: List[str] = []
    critical_gaps: List[str] = []

class AnalysisRequest(BaseModel):
    resume_text: str
    jd_text: str
    target_role: Optional[str] = None
    candidate_name: Optional[str] = None

class AnalysisResponse(BaseModel):
    success: bool
    session_id: str
    pathway: LearningPathway
    message: str

class CandidateRankEntry(BaseModel):
    candidate_name: str
    session_id: str
    readiness_score: float
    skill_coverage_percent: float
    critical_gap_count: int
    total_training_hours: float
    top_strengths: List[str]
    top_gaps: List[str]
    pathway: LearningPathway

class RankResponse(BaseModel):
    success: bool
    target_role: str
    ranked_candidates: List[CandidateRankEntry]
    message: str
