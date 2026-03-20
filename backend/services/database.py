import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

_DB_PATH = Path(__file__).parent.parent / "data" / "onboarding.db"

def get_conn():
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                candidate_name TEXT,
                target_role TEXT,
                domain TEXT,
                readiness_score REAL,
                skill_coverage_percent REAL,
                total_duration_hours REAL,
                time_saved_hours REAL,
                critical_gap_count INTEGER,
                strength_count INTEGER,
                created_at TEXT,
                pathway_json TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_candidate 
            ON sessions(candidate_name)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_role 
            ON sessions(target_role)
        """)
        conn.commit()

def save_session(pathway) -> bool:
    try:
        with get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sessions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                pathway.session_id,
                pathway.candidate_name,
                pathway.target_role,
                pathway.domain,
                pathway.readiness_score,
                pathway.skill_coverage_percent,
                pathway.total_duration_hours,
                pathway.time_saved_hours,
                len([g for g in pathway.skill_gaps if g.priority == "critical"]),
                len(pathway.strengths),
                datetime.utcnow().isoformat(),
                pathway.model_dump_json()
            ))
            conn.commit()
        return True
    except Exception as e:
        return False

def get_session(session_id: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
    if not row:
        return None
    return json.loads(row["pathway_json"])

def get_candidate_history(candidate_name: str):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT session_id, candidate_name, target_role, domain,
                   readiness_score, skill_coverage_percent,
                   total_duration_hours, time_saved_hours,
                   critical_gap_count, strength_count, created_at
            FROM sessions WHERE candidate_name LIKE ?
            ORDER BY created_at DESC
        """, (f"%{candidate_name}%",)).fetchall()
    return [dict(r) for r in rows]

def get_all_sessions(limit: int = 50):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT session_id, candidate_name, target_role, domain,
                   readiness_score, skill_coverage_percent,
                   total_duration_hours, time_saved_hours,
                   critical_gap_count, strength_count, created_at
            FROM sessions ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]

def get_stats():
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        avg_readiness = conn.execute(
            "SELECT AVG(readiness_score) FROM sessions"
        ).fetchone()[0]
        avg_coverage = conn.execute(
            "SELECT AVG(skill_coverage_percent) FROM sessions"
        ).fetchone()[0]
        top_roles = conn.execute("""
            SELECT target_role, COUNT(*) as count 
            FROM sessions GROUP BY target_role 
            ORDER BY count DESC LIMIT 5
        """).fetchall()
    return {
        "total_analyses": total,
        "avg_readiness_score": round(avg_readiness or 0, 1),
        "avg_skill_coverage": round(avg_coverage or 0, 1),
        "top_target_roles": [dict(r) for r in top_roles]
    }
