import json
import uuid
from pathlib import Path
from typing import List, Dict
import networkx as nx
from models.schemas import LearningModule, LearningPathway, SkillGap, SkillEntry

_CATALOG_PATH = Path(__file__).parent.parent / "data" / "skills_catalog.json"
with open(_CATALOG_PATH) as f:
    _CATALOG = json.load(f)

_COURSE_CATALOG: Dict = _CATALOG["course_catalog"]
_SKILL_TO_COURSES: Dict[str, List[str]] = {}
for _ck, _cd in _COURSE_CATALOG.items():
    _SKILL_TO_COURSES.setdefault(_cd["skill"].lower(), []).append(_ck)

def _detect_domain(jd_skills: List[SkillEntry]) -> str:
    skill_names = {s.name.lower() for s in jd_skills}
    domain_signals = {
        "ml_ai":           {"machine learning","deep learning","nlp","pytorch","tensorflow","mlops","transformers"},
        "web_development": {"react","angular","vue","django","flask","fastapi","graphql"},
        "data_engineering":{"spark","kafka","airflow","data pipelines","snowflake","bigquery","dbt"},
        "cloud_devops":    {"aws","azure","gcp","docker","kubernetes","terraform","ci/cd"},
        "operations":      {"project management","excel","power bi","tableau","quality assurance"},
    }
    scores = {d: len(s & skill_names) for d, s in domain_signals.items()}
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "general"

def _find_courses(skill_name: str, required_level: str, current_level: str = None) -> List[str]:
    level_map = {"beginner": 0, "intermediate": 1, "advanced": 2}
    req = level_map.get(required_level, 1)
    cur = level_map.get(current_level, -1) if current_level else -1
    candidates = _SKILL_TO_COURSES.get(skill_name.lower(), [])
    if not candidates:
        for key in _SKILL_TO_COURSES:
            if key in skill_name.lower() or skill_name.lower() in key:
                candidates = _SKILL_TO_COURSES[key]
                break
    filtered = [
        c for c in candidates
        if cur < level_map.get(_COURSE_CATALOG[c].get("difficulty", "beginner"), 0) <= req
    ]
    return filtered or candidates

def _build_dag(course_keys: List[str]) -> nx.DiGraph:
    G = nx.DiGraph()
    to_process, visited = list(set(course_keys)), set()
    while to_process:
        ck = to_process.pop()
        if ck not in _COURSE_CATALOG or ck in visited:
            continue
        visited.add(ck)
        G.add_node(ck)
        for prereq in _COURSE_CATALOG[ck].get("prerequisites", []):
            if prereq in _COURSE_CATALOG:
                G.add_edge(prereq, ck)
                if prereq not in visited:
                    to_process.append(prereq)
    return G

def _compute_readiness(coverage: float, gaps: List[SkillGap], resume_skills: List[SkillEntry]) -> float:
    total = len(gaps) or 1
    critical_ratio = sum(1 for g in gaps if g.priority == "critical") / total
    high_ratio = sum(1 for g in gaps if g.priority == "high") / total
    avg_confidence = sum(s.confidence for s in resume_skills) / len(resume_skills) if resume_skills else 0
    score = (coverage * 0.6) + (avg_confidence * 20) - (critical_ratio * 30) - (high_ratio * 10)
    return round(max(0.0, min(100.0, score)), 1)

def generate_pathway(
    resume_skills: List[SkillEntry],
    jd_skills: List[SkillEntry],
    gaps: List[SkillGap],
    coverage_percent: float,
    target_role: str,
    candidate_name: str = None
) -> LearningPathway:

    domain = _detect_domain(jd_skills)
    trace = [
        f"[INIT] Target role: '{target_role}' | Domain: {domain.upper()}",
        f"[PROFILE] Resume skills: {len(resume_skills)} | JD requirements: {len(jd_skills)} | Gaps: {len(gaps)}",
        f"[COVERAGE] Initial skill coverage: {coverage_percent}%",
    ]

    jd_skill_names = {s.name.lower() for s in jd_skills}
    strengths = [s.name for s in resume_skills if s.name.lower() in jd_skill_names and s.confidence >= 0.6]
    critical_gap_names = [g.skill for g in gaps if g.priority == "critical"]

    trace.append(f"[STRENGTHS] Confirmed competencies: {strengths[:5]}")
    trace.append(f"[CRITICAL GAPS] Immediate focus areas: {critical_gap_names[:5]}")

    # Only build learning modules for CRITICAL priority gaps
    critical_gaps = [g for g in gaps if g.priority == "critical"]
    needed_keys = []
    for gap in critical_gaps:
        courses = _find_courses(gap.skill, gap.required_level, gap.current_level)
        needed_keys.extend(courses)
        titles = [_COURSE_CATALOG[c]["title"] for c in courses if c in _COURSE_CATALOG]
        if titles:
            trace.append(f"[GAP->COURSES] '{gap.skill}' ({gap.priority.upper()}, score:{gap.gap_score}, weight:{gap.weight}) → {titles}")
        else:
            trace.append(f"[WARNING] No catalog entry found for gap: '{gap.skill}'")

    needed_keys = list(dict.fromkeys(needed_keys))
    G = _build_dag(needed_keys)
    trace.append(f"[DAG] Prerequisite graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    try:
        order = list(nx.topological_sort(G))
        trace.append("[DAG] Topological sort successful — optimal sequence determined")
    except nx.NetworkXUnfeasible:
        trace.append("[WARNING] Cycle detected — using fallback ordering")
        order = list(G.nodes())

    resume_levels = {s.name.lower(): s.level for s in resume_skills}
    level_map = {"beginner": 0, "intermediate": 1, "advanced": 2}
    modules: List[LearningModule] = []
    skipped_hours = 0.0

    for ck in order:
        if ck not in _COURSE_CATALOG:
            continue
        c = _COURSE_CATALOG[ck]
        skill = c["skill"].lower()
        if skill in resume_levels:
            if level_map.get(resume_levels[skill], 0) >= level_map.get(c.get("difficulty", "beginner"), 0):
                skipped_hours += c["duration_hours"]
                trace.append(f"[SKIP] '{c['title']}' — already at {resume_levels[skill]} (saves {c['duration_hours']}h)")
                continue
        gap_info = next((g for g in gaps if g.skill.lower() == skill), None)
        priority_tag = gap_info.priority.upper() if gap_info else None
        trace.append(f"[ADD] '{c['title']}' [{priority_tag or 'PREREQ'}] — {c['duration_hours']}h")
        modules.append(LearningModule(
            module_id=c["id"], title=c["title"], description=c["description"],
            skill_covered=c["skill"], duration_hours=c["duration_hours"],
            difficulty=c.get("difficulty", "intermediate"),
            prerequisites=c.get("prerequisites", []),
            resources=c.get("resources", []),
            order=len(modules) + 1,
            priority_tag=priority_tag
        ))

    total_hours = sum(m.duration_hours for m in modules)
    estimated_weeks = max(1, round(total_hours / 10))
    readiness = _compute_readiness(coverage_percent, gaps, resume_skills)

    trace.append(f"[RESULT] Modules: {len(modules)} | Total: {total_hours}h (~{estimated_weeks} weeks @ 10h/week)")
    trace.append(f"[RESULT] Time saved (pre-competent skills): {skipped_hours}h")
    trace.append(f"[RESULT] Readiness score: {readiness}/100 | Coverage: {coverage_percent}%")
    trace.append(f"[ADAPTIVE] Pathway personalised for '{candidate_name or 'candidate'}' targeting '{target_role}'")

    return LearningPathway(
        session_id=str(uuid.uuid4()),
        candidate_name=candidate_name,
        target_role=target_role,
        total_duration_hours=total_hours,
        estimated_weeks=estimated_weeks,
        skill_coverage_percent=coverage_percent,
        readiness_score=readiness,
        time_saved_hours=skipped_hours,
        modules=modules,
        reasoning_trace=trace,
        skill_gaps=gaps,
        resume_skills=resume_skills,
        jd_skills=jd_skills,
        domain=domain,
        strengths=strengths[:8],
        critical_gaps=critical_gap_names[:5]
    )
