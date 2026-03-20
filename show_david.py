import json

sys = __import__("assessment_system").AdvancedAssessmentSystem()
mods = sys.generate_assessment("Senior AI Engineer needing Deep Learning, Python, and AWS.", "advanced", 2)

print("### DYNAMIC TEST FOR DAVID (ADVANCED) ###\n")
for m in mods:
    print(f"--- SKILL: {m['skill_name']} ---")
    for q in m['questions']:
        print(f"Q: {q['question']}")
        if 'options' in q:
            print(f"Options: {', '.join(q['options'])}")
        print(f"Correct: {q['explanation']}\n")
