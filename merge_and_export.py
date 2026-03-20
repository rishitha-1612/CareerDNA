"""
Merger: combines generate_questions.py (parts 1-5 skills) with gen_part2.py (DevOps & ML skills)
and writes the final assessment_questions.json.
"""
import json, sys, os

# ── Load Part 1 (all skills up to Pandas/NumPy) ──────────────────────────
exec(open(r"generate_questions.py", encoding="utf-8").read(), globals())

# ── Load Part 2 (DevOps + ML skills) ─────────────────────────────────────
exec(open(r"gen_part2.py", encoding="utf-8").read(), globals())

# Append Part 2 skills
for sk in EXTRA_SKILLS:
    questions_db["skills"].append(sk)

# ── Validation ───────────────────────────────────────────────────────────
total_q = 0
for sk in questions_db["skills"]:
    cnt = sum(len(v) for v in sk["levels"].values())
    print(f"  {sk['skill_name']}: {cnt} questions")
    total_q += cnt

print(f"\nTotal questions: {total_q}")
print(f"Total skills: {len(questions_db['skills'])}")

# Update metadata
questions_db["metadata"]["total_questions"] = total_q
questions_db["metadata"]["skills_covered"] = len(questions_db["skills"])

# Collect all IDs for cross-check
all_ids = set()
dup_ids = []
for sk in questions_db["skills"]:
    for level_qs in sk["levels"].values():
        for q in level_qs:
            qid = q["question_id"]
            if qid in all_ids:
                dup_ids.append(qid)
            all_ids.add(qid)

if dup_ids:
    print(f"WARNING: Duplicate IDs found: {dup_ids}")
else:
    print("No duplicate IDs found.")

# ── Write final JSON ─────────────────────────────────────────────────────
out_path = r"assessment_questions.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(questions_db, f, indent=2, ensure_ascii=False)

size_kb = os.path.getsize(out_path) / 1024
print(f"\nWritten: {out_path}  ({size_kb:.1f} KB)")
