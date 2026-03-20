import json
import re
import random
import time
import os
import matplotlib.pyplot as plt
import argparse

DB_PATH = "assessment_questions.json"
RECORDS_PATH = "candidate_records.json"

class AdvancedAssessmentSystem:
    def __init__(self):
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                self.db = json.load(f)
        except Exception:
            raise RuntimeError(f"Question bank not found at {DB_PATH}. Must run merge.py first.")
            
        self.skills_map = {s["skill_id"]: s for s in self.db["skills"]}
        
        # Load or create candidate tracking records
        if os.path.exists(RECORDS_PATH):
            with open(RECORDS_PATH, "r", encoding="utf-8") as f:
                self.records = json.load(f)
        else:
            self.records = {}
            
        self.keyword_matrix = {
            "python_programming": [r"\bpython\b", r"\bdjango\b", r"\bfastapi\b"],
            "js_node_js": [r"\bnode\.?js\b", r"\bexpress\.?js\b"],
            "sql": [r"\bsql\b", r"\bpostgresql\b", r"\bmysql\b"],
            "rest_apis": [r"\brest\b", r"\bapi\b", r"\bmicroservices\b"],
            "html_css": [r"\bhtml5?\b", r"\bcss3?\b", r"\bui\b"],
            "javascript_frontend": [r"\bjavascript\b", r"\bfrontend\b", r"\bes6\b"],
            "react": [r"\breact\b", r"\bnext\.?js\b"],
            "typescript": [r"\btypescript\b", r"\bts\b"],
            "data_pipelines_etl": [r"\betl\b", r"\bairflow\b"],
            "apache_spark": [r"\bspark\b", r"\bpyspark\b"],
            "data_warehousing": [r"\bdata warehouse\b", r"\bsnowflake\b"],
            "pandas_numpy": [r"\bpandas\b", r"\bnumpy\b"],
            "docker": [r"\bdocker\b", r"\bcontainer\b"],
            "kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
            "aws_cloud": [r"\baws\b", r"\bcloud\b"],
            "ml_fundamentals": [r"\bmachine learning\b", r"\bml\b"],
            "deep_learning": [r"\bdeep learning\b", r"\bpytorch\b"],
            "java": [r"\bjava\b"],
            "golang": [r"\bgo\b", r"\bgolang\b"],
            "rust": [r"\brust\b"]
        }
        self.compiled_regexes = {k: [re.compile(p, re.IGNORECASE) for p in v] for k, v in self.keyword_matrix.items()}

    def extract_skills(self, text: str):
        detected = []
        for skill_id, regexes in self.compiled_regexes.items():
            if any(r.search(text) for r in regexes):
                detected.append(skill_id)
        if len(detected) < 3:
            detected.extend(["python_programming", "sql", "aws_cloud"][:3-len(detected)])
        return detected

    def generate_assessment(self, jd_text: str, candidate_level: str, num_q: int = 4):
        jd_skills = self.extract_skills(jd_text)
        modules = []
        for skill_id in jd_skills:
            if skill_id not in self.skills_map: continue
            
            levels_dict = self.skills_map[skill_id].get("levels", {})
            # STRICTLY filter by the candidate's requested level
            level_questions = levels_dict.get(candidate_level, [])
            
            # Fallback if the skill has no questions exactly at this level (e.g. Java only has intermediate)
            if not level_questions:
                # Get any available level
                available_levels = list(levels_dict.values())
                if available_levels:
                    level_questions = available_levels[0]

            qty = min(num_q, len(level_questions))
            if qty > 0:
                selected = random.sample(level_questions, qty)
                modules.append({
                    "skill_id": skill_id,
                    "skill_name": self.skills_map[skill_id]["skill_name"],
                    "questions": selected
                })
        return modules

    def simulate_test_and_score(self, candidate_name: str, level: str, modules: list):
        """Randomly 'answers' the test to generate a score, mocking a real candidate evaluation."""
        total_score = 0
        total_possible = 0
        
        skill_scores = {}
        for mod in modules:
            skill = mod["skill_name"]
            correct = 0
            count = len(mod["questions"])
            
            for q in mod["questions"]:
                # Simulation probabilities: Advanced candidates score higher on avg.
                probability = {"beginner": 0.6, "intermediate": 0.75, "advanced": 0.9}.get(level, 0.5)
                if random.random() < probability:
                    correct += 1
                    
            pct = (correct / count) * 100 if count > 0 else 0
            skill_scores[skill] = pct
            
            total_score += correct
            total_possible += count

        overall_pct = (total_score / total_possible) * 100 if total_possible > 0 else 0
        
        # Save to records
        if candidate_name not in self.records:
            self.records[candidate_name] = {"history": []}
            
        self.records[candidate_name]["history"].append({
            "timestamp": time.time(),
            "level_tested": level,
            "overall_score": round(overall_pct, 2),
            "skill_breakdown": skill_scores
        })
        
        with open(RECORDS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.records, f, indent=2)
            
        print(f"\n[+] Simulated test completed for {candidate_name} ({level}). Overall: {overall_pct:.1f}%")
        return skill_scores

    def plot_performance(self, candidate_name: str):
        if candidate_name not in self.records or not self.records[candidate_name]["history"]:
            print(f"No records found for {candidate_name}")
            return
            
        # Get the latest test iteration
        latest = self.records[candidate_name]["history"][-1]
        breakdown = latest["skill_breakdown"]
        
        skills = list(breakdown.keys())
        scores = list(breakdown.values())
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(skills, scores, color=['#4C51BF', '#48BB78', '#ED8936', '#E53E3E', '#3182CE', '#D53F8C'][:len(skills)])
        plt.ylim(0, 110)
        plt.ylabel('Score (%)', fontsize=12)
        plt.title(f'Performance Analysis: {candidate_name} ({latest["level_tested"].upper()})', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        
        # Add labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 2,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontweight='bold')
                    
        plt.tight_layout()
        filename = f"{candidate_name.replace(' ', '_').lower()}_performance.png"
        plt.savefig(filename, dpi=300)
        print(f"[+] Performance plot saved to {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=str, required=True)
    parser.add_argument("--level", type=str, choices=["beginner", "intermediate", "advanced"], required=True)
    parser.add_argument("--jd", type=str, required=True)
    args = parser.parse_args()
    
    sys = AdvancedAssessmentSystem()
    print(f"--- Dynamically scaling assessment for {args.candidate} at {args.level.upper()} level ---")
    
    # 1. Generate strictly from candidate level dynamically (no hardcoding)
    modules = sys.generate_assessment(args.jd, args.level, num_q=5)
    
    # 2. Track & Score
    scores = sys.simulate_test_and_score(args.candidate, args.level, modules)
    
    # 3. Plot
    sys.plot_performance(args.candidate)
