import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from models.schemas import SkillEntry

_CATALOG_PATH = Path(__file__).parent.parent / "data" / "skills_catalog.json"
with open(_CATALOG_PATH, "r") as f:
    _CATALOG = json.load(f)

_TAXONOMY = _CATALOG["skills_taxonomy"]
_LEVEL_INDICATORS = _CATALOG["level_indicators"]

_ALIAS_MAP: Dict[str, str] = {}
for _cat in _TAXONOMY.values():
    for _skill_name, _skill_data in _cat.items():
        _ALIAS_MAP[_skill_name.lower()] = _skill_name
        for _alias in _skill_data.get("aliases", []):
            _ALIAS_MAP[_alias.lower()] = _skill_name

_NLP = None

def _get_nlp():
    global _NLP
    if _NLP is None:
        try:
            import spacy
            try:
                _NLP = spacy.load("en_core_web_sm")
            except OSError:
                from spacy.cli import download
                download("en_core_web_sm")
                _NLP = spacy.load("en_core_web_sm")
        except ImportError:
            pass
    return _NLP

def _get_sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r'(?<=[.!\n])\s+', text) if s.strip()]

def _get_context_for_skill(text: str, skill: str) -> Tuple[str, str]:
    skill_lower = skill.lower()
    sentences = _get_sentences(text)
    for i, sent in enumerate(sentences):
        if skill_lower in sent.lower():
            start = max(0, i - 1)
            end = min(len(sentences), i + 2)
            context = " ".join(sentences[start:end]).lower()
            return context, sentences[i][:120]
    for alias, canonical in _ALIAS_MAP.items():
        if canonical.lower() == skill_lower:
            for i, sent in enumerate(sentences):
                if alias in sent.lower():
                    start = max(0, i - 1)
                    end = min(len(sentences), i + 2)
                    return " ".join(sentences[start:end]).lower(), sentences[i][:120]
    return text[:300].lower(), ""

def _infer_level(text: str, skill: str) -> Tuple[str, float]:
    context, _ = _get_context_for_skill(text, skill)
    scores = {"advanced": 0, "intermediate": 0, "beginner": 0}
    for level, indicators in _LEVEL_INDICATORS.items():
        for indicator in indicators:
            if indicator in context:
                scores[level] += 1
    year_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", context)
    if year_match:
        yrs = int(year_match.group(1))
        if yrs >= 5:
            scores["advanced"] += 3
        elif yrs >= 2:
            scores["intermediate"] += 3
        else:
            scores["beginner"] += 3
    best_level = max(scores, key=scores.get)
    best_score = scores[best_level]
    total = sum(scores.values()) or 1
    confidence = round(min(best_score / total + 0.4, 1.0), 2) if best_score > 0 else 0.5
    return best_level, confidence

def _count_frequency(text_lower: str, skill: str) -> int:
    count = 0
    skill_lower = skill.lower()
    pattern = r"(?<![a-zA-Z0-9_/\-])" + re.escape(skill_lower) + r"(?![a-zA-Z0-9_/\-])"
    count += len(re.findall(pattern, text_lower))
    for alias, canonical in _ALIAS_MAP.items():
        if canonical.lower() == skill_lower and alias != skill_lower:
            ap = r"(?<![a-zA-Z0-9_/\-])" + re.escape(alias) + r"(?![a-zA-Z0-9_/\-])"
            count += len(re.findall(ap, text_lower))
    return max(count, 1)

def extract_skills(text: str, source: str = "resume") -> List[SkillEntry]:
    found: Dict[str, SkillEntry] = {}
    text_lower = text.lower()

    for alias, canonical in _ALIAS_MAP.items():
        pattern = r"(?<![a-zA-Z0-9_/\-])" + re.escape(alias) + r"(?![a-zA-Z0-9_/\-])"
        if re.search(pattern, text_lower):
            if canonical not in found:
                level, conf = _infer_level(text, canonical)
                _, snippet = _get_context_for_skill(text, canonical)
                freq = _count_frequency(text_lower, canonical)
                found[canonical] = SkillEntry(
                    name=canonical, level=level, confidence=conf,
                    source=source, frequency=freq,
                    context_snippet=snippet if source == "resume" else None
                )
            else:
                found[canonical].frequency = _count_frequency(text_lower, canonical)

    nlp = _get_nlp()
    if nlp:
        doc = nlp(text[:100000])
        for ent in doc.ents:
            if ent.label_ in ("ORG", "PRODUCT", "GPE"):
                ent_lower = ent.text.lower().strip()
                if ent_lower in _ALIAS_MAP:
                    canonical = _ALIAS_MAP[ent_lower]
                    if canonical not in found:
                        level, conf = _infer_level(text, canonical)
                        _, snippet = _get_context_for_skill(text, canonical)
                        freq = _count_frequency(text_lower, canonical)
                        found[canonical] = SkillEntry(
                            name=canonical, level=level, confidence=conf,
                            source=source, frequency=freq,
                            context_snippet=snippet if source == "resume" else None
                        )

    results = [s for s in found.values() if s.confidence >= 0.3]
    results.sort(key=lambda x: (x.frequency, x.confidence), reverse=True)
    return results
