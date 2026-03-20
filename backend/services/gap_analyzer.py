from typing import List, Tuple
from models.schemas import SkillEntry, SkillGap

_LEVEL_SCORE = {"beginner": 1, "intermediate": 2, "advanced": 3}

_EMBEDDER = None
_CATALOG_SKILL_KEYS: list = []
_CATALOG_SKILL_VECS = None

def _get_embedder():
    global _EMBEDDER, _CATALOG_SKILL_KEYS, _CATALOG_SKILL_VECS
    if _EMBEDDER is None:
        try:
            from sentence_transformers import SentenceTransformer
            import json
            from pathlib import Path
            _EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")
            catalog_path = Path(__file__).parent.parent / "data" / "skills_catalog.json"
            with open(catalog_path) as f:
                catalog = json.load(f)
            _CATALOG_SKILL_KEYS = list({
                v["skill"] for v in catalog.get("course_catalog", {}).values()
            })
            if _CATALOG_SKILL_KEYS:
                _CATALOG_SKILL_VECS = _EMBEDDER.encode(
                    _CATALOG_SKILL_KEYS, convert_to_numpy=True
                )
        except ImportError:
            pass
    return _EMBEDDER

def _cosine_similarity(a, b) -> float:
    import numpy as np
    a, b = np.array(a), np.array(b)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom > 0 else 0.0

def _semantic_match(jd_skill: str, resume_skills: List[SkillEntry], embedder, threshold: float = 0.70):
    for rs in resume_skills:
        if rs.name.lower() == jd_skill.lower():
            return rs, 1.0
    if not embedder or not resume_skills:
        return None, 0.0
    try:
        jd_vec = embedder.encode(jd_skill, convert_to_numpy=True)
        resume_vecs = embedder.encode([rs.name for rs in resume_skills], convert_to_numpy=True)
        best_idx, best_sim = -1, 0.0
        for i, rvec in enumerate(resume_vecs):
            sim = _cosine_similarity(jd_vec, rvec)
            if sim > best_sim:
                best_sim, best_idx = sim, i
        if best_sim >= threshold:
            return resume_skills[best_idx], best_sim
    except Exception:
        pass
    return None, 0.0

def _build_reasoning(skill: str, required_level: str, current_level,
                     gap_score: float, priority: str, jd_freq: int) -> str:
    freq_note = f"mentioned {jd_freq}x in JD" if jd_freq > 1 else "mentioned in JD"
    if current_level is None:
        return (f"Not found in resume ({freq_note}). "
                f"Required at {required_level} level — full acquisition needed. "
                f"Priority: {priority.upper()} (gap score: {gap_score:.2f}).")
    return (f"Resume shows {current_level} level; JD requires {required_level} ({freq_note}). "
            f"Level uplift needed: {current_level} → {required_level}. "
            f"Priority: {priority.upper()} (gap score: {gap_score:.2f}).")

def compute_gap(resume_skills: List[SkillEntry], jd_skills: List[SkillEntry]):
    embedder = _get_embedder()
    gaps: List[SkillGap] = []
    total_weighted_gap = 0.0
    total_weight = 0.0

    for jd_skill in jd_skills:
        weight = min(1.0 + (jd_skill.frequency - 1) * 0.15, 2.0)
        matched, _ = _semantic_match(jd_skill.name, resume_skills, embedder)

        if matched:
            delta = max(0, _LEVEL_SCORE.get(jd_skill.level, 2) - _LEVEL_SCORE.get(matched.level, 1))
            gap_score = round(delta / 2, 2)
            current_level = matched.level
        else:
            gap_score = 1.0
            current_level = None

        total_weighted_gap += gap_score * weight
        total_weight += weight

        if gap_score >= 0.75:
            priority = "critical"
        elif gap_score >= 0.50:
            priority = "high"
        elif gap_score >= 0.25:
            priority = "medium"
        else:
            priority = "low"

        if gap_score > 0:
            gaps.append(SkillGap(
                skill=jd_skill.name,
                required_level=jd_skill.level,
                current_level=current_level,
                gap_score=gap_score,
                priority=priority,
                weight=round(weight, 2),
                reasoning=_build_reasoning(
                    jd_skill.name, jd_skill.level, current_level,
                    gap_score, priority, jd_skill.frequency
                )
            ))

    avg_gap = total_weighted_gap / total_weight if total_weight > 0 else 0
    coverage = round(max(0.0, min(100.0, 100 * (1 - avg_gap))), 1)
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    gaps.sort(key=lambda g: (priority_order[g.priority], -g.gap_score * g.weight))
    return gaps, coverage
