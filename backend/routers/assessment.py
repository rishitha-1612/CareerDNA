from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from services.assessment_engine import ProceduralAssessmentEngine
import random

router = APIRouter(prefix="/assessment")
engine = ProceduralAssessmentEngine()

class GenerateRequest(BaseModel):
    jd_text: str
    level: str = "intermediate"

class SubmitRequest(BaseModel):
    modules: List[Dict[str, Any]]
    candidate_answers: Dict[str, str]

class InterviewQRequest(BaseModel):
    gaps: List[str]
    strengths: List[str]
    readiness_score: float

class HireRecommendRequest(BaseModel):
    readiness_score: float
    skill_coverage_percent: float
    critical_gap_count: int
    total_duration_hours: float

@router.post("/generate")
def generate_assessment(req: GenerateRequest):
    return engine.generate_assessment(req.jd_text, req.level.lower())

@router.post("/submit")
def submit_assessment(req: SubmitRequest):
    return engine.score_assessment({
        "modules": req.modules,
        "candidate_answers": req.candidate_answers
    })

@router.post("/interview-questions")
def generate_interview_questions(req: InterviewQRequest):
    """Procedurally generate targeted interview questions based on skill gaps."""
    QUESTION_BANK = {
        "python": [
            "Explain the difference between a list and a tuple in Python and when you would use each.",
            "How does Python's GIL affect multi-threading? When would you use multiprocessing instead?",
            "Walk me through how you would optimize a slow Python function. What tools would you use?",
            "What are Python decorators and can you write one that logs execution time?",
            "Explain generators and how they differ from regular functions returning lists.",
        ],
        "sql": [
            "Explain the difference between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN with examples.",
            "How would you find the second highest salary from an employees table?",
            "What is query optimization and what techniques do you use to speed up slow queries?",
            "Explain database normalization — 1NF, 2NF, 3NF — with a real-world example.",
            "When would you use a subquery vs a CTE (Common Table Expression)?",
        ],
        "javascript": [
            "Explain the event loop in JavaScript and how it handles asynchronous operations.",
            "What is the difference between `var`, `let`, and `const`? When should each be used?",
            "Explain closures in JavaScript with a practical use case.",
            "What is Promise chaining and how does `async/await` improve upon it?",
            "How does the `this` keyword work differently in arrow functions vs regular functions?",
        ],
        "react": [
            "Explain the React component lifecycle — how does it map to hooks?",
            "When would you use `useCallback` vs `useMemo`? Explain the trade-offs.",
            "How do you manage global state in a large React app without external libraries?",
            "Explain the virtual DOM and how React's reconciliation algorithm works.",
            "What are React Suspense and concurrent features, and when would you use them?",
        ],
        "aws": [
            "Explain the difference between EC2, Lambda, and ECS — when would you choose each?",
            "How would you design a highly available architecture for a web app on AWS?",
            "What is IAM and how do you handle least-privilege access in a production environment?",
            "Explain S3 storage classes and how you would choose between them for cost optimization.",
            "How would you monitor and alert on performance issues in an AWS-based application?",
        ],
        "machine learning": [
            "Explain the bias-variance trade-off and how you address it in model training.",
            "How do you handle class imbalance in a training dataset?",
            "Walk me through how you would validate a model beyond just training accuracy.",
            "What is gradient descent and how does the learning rate affect convergence?",
            "When would you use cross-validation, and what are its limitations?",
        ],
        "data": [
            "How do you handle missing data in a real-world dataset?",
            "Explain the difference between structured and unstructured data processing pipelines.",
            "What metrics do you use to evaluate the quality of a data pipeline?",
            "How would you design a data warehouse schema for an e-commerce platform?",
            "Explain what ETL is and how you would design a fault-tolerant ETL pipeline.",
        ],
    }
    
    questions = []
    generic_bank = [
        "Describe a challenging technical problem you solved and your approach.",
        "How do you keep up with rapidly evolving technologies in your field?",
        "Explain a situation where you had to balance technical debt vs delivery speed.",
        "Tell me about a time you had to learn a new technology quickly for a project.",
        "How do you approach code reviews both as a reviewer and the person being reviewed?",
    ]
    
    # Match gaps to question bank
    for gap in req.gaps[:4]:  # Max 4 gap skills
        gap_lower = gap.lower()
        matched = False
        for keyword, bank in QUESTION_BANK.items():
            if keyword in gap_lower or gap_lower in keyword:
                questions.append({
                    "skill": gap,
                    "type": "gap",
                    "question": random.choice(bank)
                })
                matched = True
                break
        if not matched:
            questions.append({
                "skill": gap,
                "type": "gap",
                "question": f"Can you walk me through your experience with {gap} and a project where you applied it?"
            })
    
    # Add 2 behavioral based on readiness
    if req.readiness_score < 60:
        questions.append({"skill": "Behavioral", "type": "behavioral", "question": "Tell me about a time you had to quickly ramp up on a technology you weren't familiar with."})
    else:
        questions.append({"skill": "Behavioral", "type": "behavioral", "question": "How do you mentor junior engineers or share knowledge on your team?"})
    
    questions.append({"skill": "General", "type": "situational", "question": random.choice(generic_bank)})
    
    return {"interview_questions": questions, "total": len(questions)}


@router.post("/hire-recommendation")
def hire_recommendation(req: HireRecommendRequest):
    """Generate an AI hire recommendation based on objective metrics."""
    score = req.readiness_score
    coverage = req.skill_coverage_percent
    gaps = req.critical_gap_count
    hours = req.total_duration_hours

    if score >= 80 and gaps <= 1:
        tier = "STRONG HIRE"
        color = "green"
        badge = "🟢"
        summary = f"Outstanding candidate. {coverage:.0f}% skill coverage with only {gaps} critical gap(s). Ready to contribute from Day 1."
        action = "Proceed to final round. Recommend immediate offer."
    elif score >= 65 and gaps <= 3:
        tier = "HIRE"
        color = "teal"
        badge = "🔵"
        summary = f"Solid candidate. {coverage:.0f}% skill match with {gaps} gap(s) bridgeable in ~{hours:.0f}h of targeted training."
        action = f"Recommend offer with {hours:.0f}h structured onboarding plan."
    elif score >= 50 and gaps <= 5:
        tier = "HIRE WITH DEVELOPMENT"
        color = "amber"
        badge = "🟡"
        summary = f"Promising candidate with {coverage:.0f}% coverage. {gaps} critical gaps require {hours:.0f}h of upskilling."
        action = f"Offer conditional on completing a {hours:.0f}h training pathway within 90 days."
    elif score >= 35:
        tier = "HOLD"
        color = "orange"
        badge = "🟠"
        summary = f"Below threshold at {score:.0f} readiness. Significant gaps ({gaps}) with {hours:.0f}h required upskilling."
        action = "Re-evaluate after candidate completes recommended learning pathway."
    else:
        tier = "DO NOT HIRE"
        color = "red"
        badge = "🔴"
        summary = f"Critical skill mismatch. Only {coverage:.0f}% coverage with {gaps} blocking gaps."
        action = "Role requires significantly more experience. Consider more senior candidates."

    return {
        "tier": tier,
        "badge": badge,
        "color": color,
        "summary": summary,
        "action": action,
        "readiness_score": score
    }

