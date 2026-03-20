import asyncio
import re
import logging
import hashlib
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from models.schemas import AnalysisRequest, AnalysisResponse, RankResponse, CandidateRankEntry
from services.document_parser import detect_and_extract
from services.skill_extractor import extract_skills
from services.gap_analyzer import compute_gap
from services.pathway_generator import generate_pathway
from services.scraper import fetch_resources_for_skills
from services import database

logger = logging.getLogger("uvicorn.error")
router = APIRouter()

_CACHE: dict = {}

def _cache_key(resume_text: str, jd_text: str) -> str:
    return hashlib.md5((resume_text + jd_text).encode()).hexdigest()

def _infer_role(jd_text: str) -> str:
    for pattern in [
        r"(?:job title|position|role|title)[\:\s]+([A-Z][A-Za-z\s]{3,50})(?:\n|,|\.|;)",
        r"(?:looking for|hiring|seeking)[\:\s]+(?:a |an )?([A-Z][A-Za-z\s]{3,50})(?:\n|,|\.|;)",
    ]:
        m = re.search(pattern, jd_text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).strip()
    for line in jd_text.split("\n"):
        line = line.strip()
        if 3 < len(line) < 60 and line[0].isupper():
            return line
    return "Target Role"

async def _run_pipeline(resume_text: str, jd_text: str,
                  target_role: Optional[str] = None,
                  candidate_name: Optional[str] = None):
    if not resume_text.strip():
        raise HTTPException(status_code=422, detail="Resume text is empty.")
    if not jd_text.strip():
        raise HTTPException(status_code=422, detail="Job description text is empty.")

    key = _cache_key(resume_text, jd_text)
    if key in _CACHE:
        logger.info(f"Cache hit [{key[:8]}]")
        return _CACHE[key]

    resume_skills = extract_skills(resume_text, source="resume")
    jd_skills = extract_skills(jd_text, source="jd")

    if not jd_skills:
        raise HTTPException(status_code=422, detail="Could not extract skills from Job Description.")

    role = target_role or _infer_role(jd_text)
    gaps, coverage = compute_gap(resume_skills, jd_skills)
    
    # --- Build instant resource links for skill gaps ---
    gap_skills = [g.skill for g in gaps]
    if gap_skills:
        try:
            resource_map = await fetch_resources_for_skills(gap_skills)
            for gap in gaps:
                gap.links = resource_map.get(gap.skill.lower().strip(), [])
        except Exception as e:
            logger.error(f"Failed to build resource links: {e}")
    # ---------------------------------------------------
            
    pathway = generate_pathway(resume_skills, jd_skills, gaps, coverage, role, candidate_name)

    _CACHE[key] = pathway
    database.save_session(pathway)
    logger.info(f"Analysis done | role={role} | coverage={coverage}% | gaps={len(gaps)} | readiness={pathway.readiness_score}")
    return pathway

@router.post("/analyze/text", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest):
    pathway = await _run_pipeline(request.resume_text, request.jd_text,
                                  request.target_role, request.candidate_name)
    return AnalysisResponse(success=True, session_id=pathway.session_id,
                            pathway=pathway,
                            message=f"Pathway generated. Readiness: {pathway.readiness_score}/100")

@router.post("/analyze/upload")
async def analyze_upload(
    resume: UploadFile = File(...),
    jd: UploadFile = File(...),
    target_role: Optional[str] = Form(None),
    candidate_name: Optional[str] = Form(None),
):
    allowed = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    }
    for upload in (resume, jd):
        if upload.content_type not in allowed:
            raise HTTPException(status_code=415, detail=f"Unsupported file: {upload.filename}")
    try:
        resume_text = detect_and_extract(await resume.read(), resume.filename)
        jd_text = detect_and_extract(await jd.read(), jd.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    pathway = await _run_pipeline(resume_text, jd_text, target_role, candidate_name)
    return JSONResponse(content={
        "success": True,
        "session_id": pathway.session_id,
        "pathway": pathway.model_dump(),
        "message": f"Pathway generated. Readiness: {pathway.readiness_score}/100"
    })

@router.post("/rank", response_model=RankResponse)
async def rank_candidates(
    jd: UploadFile = File(...),
    resumes: List[UploadFile] = File(...),
    target_role: Optional[str] = Form(None),
):
    """Rank multiple candidates against one JD — returns sorted by readiness score."""
    allowed = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    }
    if jd.content_type not in allowed:
        raise HTTPException(status_code=415, detail="Unsupported JD file type.")
    jd_text = detect_and_extract(await jd.read(), jd.filename)
    role = target_role or _infer_role(jd_text)

    ranked = []
    for resume_file in resumes:
        if resume_file.content_type not in allowed:
            continue
        try:
            resume_text = detect_and_extract(await resume_file.read(), resume_file.filename)
            name = resume_file.filename.rsplit(".", 1)[0]
            pathway = await _run_pipeline(resume_text, jd_text, role, name)
            ranked.append(CandidateRankEntry(
                candidate_name=name,
                session_id=pathway.session_id,
                readiness_score=pathway.readiness_score,
                skill_coverage_percent=pathway.skill_coverage_percent,
                critical_gap_count=len([g for g in pathway.skill_gaps if g.priority == "critical"]),
                total_training_hours=pathway.total_duration_hours,
                top_strengths=pathway.strengths[:3],
                top_gaps=pathway.critical_gaps[:3],
                pathway=pathway
            ))
        except Exception as e:
            logger.warning(f"Skipped {resume_file.filename}: {e}")

    ranked.sort(key=lambda x: (-x.readiness_score, x.total_training_hours))
    return RankResponse(success=True, target_role=role, ranked_candidates=ranked,
                        message=f"Ranked {len(ranked)} candidates for '{role}'")

@router.get("/sessions")
def list_sessions(limit: int = 50):
    """List all past analyses - most recent first."""
    return {"sessions": database.get_all_sessions(limit)}

@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    """Retrieve full pathway for a past session by ID."""
    from fastapi import HTTPException
    result = database.get_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"success": True, "pathway": result}

@router.get("/candidates/{candidate_name}/history")
def candidate_history(candidate_name: str):
    """Get all past analyses for a candidate by name."""
    history = database.get_candidate_history(candidate_name)
    return {"candidate": candidate_name, "total": len(history), "history": history}

@router.get("/stats")
def platform_stats():
    """Aggregate stats across all analyses � useful for demo."""
    return database.get_stats()

@router.get("/catalog")
def get_catalog():
    import json
    from pathlib import Path
    with open(Path(__file__).parent.parent / "data" / "skills_catalog.json") as f:
        data = json.load(f)
    courses = data.get("course_catalog", {})
    return {"total_courses": len(courses), "courses": list(courses.values())}

@router.get("/skills/taxonomy")
def get_taxonomy():
    import json
    from pathlib import Path
    with open(Path(__file__).parent.parent / "data" / "skills_catalog.json") as f:
        data = json.load(f)
    return data.get("skills_taxonomy", {})

@router.get("/health/detailed")
def health_detailed():
    import json
    from pathlib import Path
    total = len(json.load(open(
        Path(__file__).parent.parent / "data" / "skills_catalog.json"
    )).get("course_catalog", {}))
    return {
        "status": "healthy",
        "version": "2.0.0",
        "cache_entries": len(_CACHE),
        "catalog_courses": total
    }
