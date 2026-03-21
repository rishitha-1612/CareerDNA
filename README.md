# AI-Adaptive Onboarding Engine (Resume Analyser)

An AI-driven adaptive learning engine that parses a new hire's resume and a target Job Description, identifies skill gaps, and dynamically generates a personalised, prerequisite-aware training pathway to reach role-specific competency.

---

## Features

- **Full-Stack Application** — Seamless integration of a robust FastAPI backend with a responsive React (Vite) frontend.
- **Intelligent Skill Extraction** — Regex + spaCy NER + sentence-level context windows for accurate skill and experience level inference.
- **Comprehensive Gap Analysis** — Analyzes the resume against the Job Description, finding missed critical skills and weighting them appropriately.
- **Dynamic Learning Resources** — Automatically generates curated learning resources (freeCodeCamp, GeeksforGeeks, Medium, YouTube) for identified skill gaps using instant search URLs.
- **Interactive UI/UX** — Modern React frontend with a dedicated Splash Screen, progress tracking, and intuitive dashboard for entering Data.
- **Readiness Score (0-100)** — Composite score combining coverage, gap severity, and skill confidence.
- **Zero External LLM API Calls** — Fully local processing with `sentence-transformers` models preventing hallucinations and reducing costs.
- **Multi-Candidate Ranking** — API capability to rank multiple resumes against one JD.

---

##  Tech Stack

### Backend
- **Framework**: FastAPI 0.115
- **NLP / NER**: spaCy (en_core_web_sm), sentence-transformers (all-MiniLM-L6-v2)
- **Data Parsing**: pdfminer.six (PDF), python-docx (DOCX)
- **Database**: SQLite (built-in)

### Frontend
- **Framework**: React / Vite
- **Styling**: Modern CSS / Tailwind (if applicable)
- **Build Tool**: Node.js & npm

---

##  Architecture & Workflow
```
Resume (PDF/DOCX/TXT) ──┐
                         ├──► Skill Extractor ──► Gap Analyzer ──► JSON Response & 
Job Description          ┘    (spaCy NER +       (Semantic          Learning Resources
                               regex)             embeddings)
```

---

##  Setup & Installation

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Activate the virtual environment:
source venv/Scripts/activate        # Windows Git Bash
# source venv/bin/activate          # Linux/Mac

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
*The backend API will be available at http://localhost:8000. Open http://localhost:8000/docs for the Swagger UI.*

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*The frontend application will typically be available at http://localhost:5173.*

---

##  Deployment

This application is configured for deployment on render.com or via Docker:

### Render
A `render.yaml` template is included to quickly spin up the web services for both the frontend (Node/Static) and backend (Python/FastAPI). 
The app includes a custom splash screen logic to load smoothly during initial cold starts.

### Docker
```bash
docker-compose up --build
```
Or build the backend separately:
```bash
docker build -t adaptive-onboarding ./backend
docker run -p 8000:8000 adaptive-onboarding
```

---

##  Datasets Referenced
- O*NET Database — https://www.onetcenter.org/db_releases.html
- Kaggle Resume Dataset — https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset/data
- Kaggle Jobs Dataset — https://www.kaggle.com/datasets/kshitizregmi/jobs-and-job-description

---