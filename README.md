# AI-Adaptive Onboarding Engine
> ARTPARK CodeForge Hackathon Submission

An AI-driven adaptive learning engine that parses a new hire's resume and a target Job Description, identifies skill gaps, and dynamically generates a personalised, prerequisite-aware training pathway to reach role-specific competency.

---

## Problem Statement
Corporate onboarding suffers from static "one-size-fits-all" curricula. Experienced hires waste time on known concepts; beginners get overwhelmed. This engine solves that by personalising every pathway to the individual.

---

## Architecture & Workflow
```
Resume (PDF/DOCX/TXT) ──┐
                         ├──► Skill Extractor ──► Gap Analyzer ──► Pathway Generator ──► JSON Response
Job Description          ┘    (spaCy NER +       (Semantic          (NetworkX DAG +
                               regex + freq       embeddings +       topological sort +
                               counting)          weighted scoring)  readiness score)
```

---

## Tech Stack

| Component | Library |
|---|---|
| API Framework | FastAPI 0.115 |
| NLP / NER | spaCy en_core_web_sm 3.8 |
| Semantic Embeddings | sentence-transformers all-MiniLM-L6-v2 |
| Prerequisite Graph | NetworkX 3.3 |
| PDF Parsing | pdfminer.six |
| DOCX Parsing | python-docx |
| Validation | Pydantic v2 |
| Persistence | SQLite (built-in) |
| Fuzzy Matching | rapidfuzz |

---

## Key Features
- **Intelligent Skill Extraction** — regex + spaCy NER + sentence-level context windows for accurate level inference
- **Frequency-Weighted Gap Scoring** — skills mentioned more in the JD get higher priority weights
- **Readiness Score (0-100)** — composite score combining coverage, gap severity, and skill confidence
- **Prerequisite-Aware DAG** — courses ordered via topological sort so no module is recommended before its dependencies
- **Time Saved Metric** — quantifies redundant training eliminated for already-competent skills
- **Explainable Gaps** — every gap includes a human-readable reasoning field
- **Multi-Candidate Ranking** — `/rank` endpoint compares multiple resumes against one JD
- **Cross-Domain** — 60+ courses across 7 domains: ML/AI, Web, DevOps, Data Engineering, Cloud, Operations, Soft Skills
- **Candidate History** — SQLite persistence with full session retrieval and analytics
- **Zero External API Calls** — fully local, no LLM dependencies, no hallucinations

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/v1/analyze/text | Analyse from plain text |
| POST | /api/v1/analyze/upload | Analyse from PDF/DOCX files |
| POST | /api/v1/rank | Rank multiple candidates against one JD |
| GET | /api/v1/sessions | List all past analyses |
| GET | /api/v1/sessions/{session_id} | Retrieve a past session by ID |
| GET | /api/v1/candidates/{name}/history | Full history for a candidate |
| GET | /api/v1/stats | Platform-wide aggregate stats |
| GET | /api/v1/catalog | List all courses in catalog |
| GET | /api/v1/skills/taxonomy | Full skills taxonomy |
| GET | /api/v1/health/detailed | Health + system info |

---

## Adaptive Pathing Algorithm
1. **Skill Extraction** — regex alias matching + spaCy NER across resume and JD; frequency counted per skill
2. **Gap Analysis** — semantic cosine similarity (all-MiniLM-L6-v2) matches resume skills to JD requirements; gap score = level delta weighted by JD frequency
3. **DAG Construction** — NetworkX directed graph built from course prerequisites; nodes added for all gap-covering courses plus their dependency chains
4. **Topological Sort** — optimal learning sequence guaranteed; no course appears before its prerequisites
5. **Readiness Score** — `(coverage × 0.6) + (avg_confidence × 20) - (critical_ratio × 30) - (high_ratio × 10)`
6. **Skip Logic** — courses skipped if candidate already meets or exceeds that skill level; saved hours reported

---

## Datasets Referenced
- O*NET Database — https://www.onetcenter.org/db_releases.html
- Kaggle Resume Dataset — https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset/data
- Kaggle Jobs Dataset — https://www.kaggle.com/datasets/kshitizregmi/jobs-and-job-description

---

## Setup
```bash
cd backend
python -m venv venv
source venv/Scripts/activate        # Windows Git Bash
# source venv/bin/activate          # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000/docs for Swagger UI.

## Docker
```bash
docker build -t adaptive-onboarding ./backend
docker run -p 8000:8000 adaptive-onboarding
```

---

## License
MIT
