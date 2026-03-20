import json
import os

from part_1 import skills as skills_1
from part_2 import skills as skills_2
from part_3 import skills as skills_3
from gen_part2 import EXTRA_SKILLS as skills_4
from part_5 import skills as skills_5

# Build question db structure
questions_db = {
  "metadata": {
    "version": "1.0",
    "generated_date": "2024-01-15",
    "total_questions": 0,
    "skills_covered": 0,
    "difficulty_distribution": {
      "beginner": 0,
      "intermediate": 0,
      "advanced": 0
    }
  },
  "skills": []
}

all_skills = skills_1 + skills_2 + skills_3 + skills_4 + skills_5
questions_db["skills"] = all_skills

total_qs = 0
diff_dist = {"beginner": 0, "intermediate": 0, "advanced": 0}

for sk in all_skills:
    for lvl, qs in sk["levels"].items():
        count = len(qs)
        diff_dist[lvl] += count
        total_qs += count

questions_db["metadata"]["total_questions"] = total_qs
questions_db["metadata"]["skills_covered"] = len(all_skills)
questions_db["metadata"]["difficulty_distribution"] = diff_dist

print(f"Total skills: {len(all_skills)}")
print(f"Total questions: {total_qs}")
print(f"Distribution: {diff_dist}")

out_path = "assessment_questions.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(questions_db, f, indent=2, ensure_ascii=False)

print(f"Successfully generated {out_path} ({os.path.getsize(out_path) / 1024:.1f} KB)")
