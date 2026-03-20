import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import analyze
from services.database import init_db
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

app = FastAPI(
    title="AI-Adaptive Onboarding Engine",
    description="Parses resumes & JDs, extracts skills, computes weighted gap analysis, generates prerequisite-aware personalised learning pathways. Zero external API calls.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(analyze.router, prefix="/api/v1", tags=["Analysis"])

@app.get("/")
def root():
    return {"status": "running", "version": "2.0.0",
            "message": "AI-Adaptive Onboarding Engine is live.", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy", "version": "2.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
