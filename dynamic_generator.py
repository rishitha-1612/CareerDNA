import json
import re
import random
import time
import argparse
from typing import List, Dict, Any

class DynamicAssessmentGenerator:
    def __init__(self, db_path: str = "assessment_questions.json"):
        """Loads the massive 200-question JSON bank off the disk."""
        start_time = time.time()
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                self.db = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load question bank at {db_path}. Run merge.py first. Error: {e}")
            
        # Extract skills into a quick lookup dictionary: {skill_id: skill_data}
        self.skills_map = {s["skill_id"]: s for s in self.db["skills"]}
        
        # Keyword mapping for NLP extraction without API
        self.keyword_matrix = {
            "python_programming": [r"\bpython\b", r"\bflask\b", r"\bdjango\b", r"\bfastapi\b"],
            "js_node_js": [r"\bnode\.?js\b", r"\bexpress\.?js\b", r"\bbackend javascript\b"],
            "sql": [r"\bsql\b", r"\bmysql\b", r"\bpostgresql\b", r"\brdbms\b", r"\boracle\b", r"\bpostgres\b"],
            "rest_apis": [r"\brest(ful)?\b", r"\bapi(s)?\b", r"\bmicroservices\b"],
            "html_css": [r"\bhtml5?\b", r"\bcss3?\b", r"\btailwind\b", r"\bui\b", r"\bbootstrap\b"],
            "javascript_frontend": [r"\bjavascript\b", r"\bjs\b", r"\bes6\b", r"\bvanilla js\b", r"\bfrontend\b"],
            "react": [r"\breact(\.?js)?\b", r"\bnext\.?js\b", r"\bhooks\b"],
            "typescript": [r"\btypescript\b", r"\bts\b"],
            "data_pipelines_etl": [r"\betl\b", r"\belt\b", r"\bairflow\b", r"\bpipelines\b", r"\bdata engineering\b", r"\bdata pipelines\b"],
            "apache_spark": [r"\bspark\b", r"\bpyspark\b", r"\bhadoop\b", r"\bbig data\b"],
            "data_warehousing": [r"\bdata warehouse\b", r"\bsnowflake\b", r"\bbigquery\b", r"\bredshift\b", r"\bdbt\b"],
            "pandas_numpy": [r"\bpandas\b", r"\bnumpy\b", r"\bdata-?frame(s)?\b", r"\bdata analysis\b"],
            "docker": [r"\bdocker\b", r"\bcontainer(ization|isation)?\b"],
            "kubernetes": [r"\bkubernetes\b", r"\bk8s\b", r"\bhelm\b"],
            "aws_cloud": [r"\baws\b", r"\bamazon web services\b", r"\bcloud\b", r"\bec2\b", r"\bs3\b", r"\blambda\b"],
            "ml_fundamentals": [r"\bmachine learning\b", r"\bml\b", r"\bscikit-learn\b", r"\bpredictive modeling\b", r"\bxgboost\b"],
            "deep_learning": [r"\bdeep learning\b", r"\bdl\b", r"\btensorflow\b", r"\bpytorch\b", r"\bneural networks\b", r"\bllms?\b", r"\btransformer\b"],
            "java": [r"\bjava\b", r"\bspring(boot)?\b", r"\bjvm\b", r"\bmaven\b"],
            "golang": [r"\bgo\b", r"\bgolang\b", r"\bgoroutines\b"],
            "rust": [r"\brust\b", r"\bcargo\b", r"\bborrow checker\b"]
        }
        
        # Precompile Regex for speed
        self._compiled_regexes = {
            skill_id: [re.compile(p, re.IGNORECASE) for p in patterns]
            for skill_id, patterns in self.keyword_matrix.items()
        }
        self.load_time = time.time() - start_time
        
    def _extract_skills_from_jd(self, jd_text: str) -> List[str]:
        """Scans the JD text using regex to find required foundational skills in O(1) time."""
        detected_skills = []
        for skill_id, regexes in self._compiled_regexes.items():
            for r in regexes:
                if r.search(jd_text):
                    detected_skills.append(skill_id)
                    break # Stop checking this skill if we already found a match
        return detected_skills

    def generate_assessment(self, jd_text: str, num_questions_per_skill: int = 3, force_minimum_skills: int = 3) -> Dict[str, Any]:
        """
        Dynamically builds a tailored JSON assessment test based on the JD text.
        Sub-second response time via regex parsing and purely local JSON structure reads.
        """
        start_time = time.time()
        jd_skills = self._extract_skills_from_jd(jd_text)
        
        # Fallback if JD is too vague or generic
        if len(jd_skills) < force_minimum_skills:
            print("JD contains too few specific keywords. Padding with core fundamentals...")
            core = ["python_programming", "sql", "javascript_frontend", "aws_cloud"]
            for c in core:
                if c not in jd_skills and len(jd_skills) < force_minimum_skills:
                    jd_skills.append(c)
        
        # Now construct the assessment
        custom_assessment = {
            "metadata": {
                "jd_analysis_time_ms": 0,
                "dynamic_match_mode": "keyword_heuristic",
                "skills_detected": len(jd_skills),
                "total_questions": 0,
            },
            "assessment_modules": []
        }
        
        total_q = 0
        for skill_id in jd_skills:
            if skill_id not in self.skills_map:
                continue
                
            skill_def = self.skills_map[skill_id]
            levels = skill_def.get("levels", {})
            
            # Gather all questions for this skill
            all_skill_qs = []
            for lvl, qs in levels.items():
                all_skill_qs.extend(qs)
                
            # Randomly sample the desired amount (cap at max available)
            qty_to_pick = min(num_questions_per_skill, len(all_skill_qs))
            selected_qs = random.sample(all_skill_qs, qty_to_pick) if qty_to_pick > 0 else []
            
            if selected_qs:
                total_q += len(selected_qs)
                custom_assessment["assessment_modules"].append({
                    "skill_id": skill_def["skill_id"],
                    "skill_name": skill_def["skill_name"],
                    "questions": selected_qs
                })
                
        time_taken_ms = round((time.time() - start_time) * 1000, 2)
        custom_assessment["metadata"]["jd_analysis_time_ms"] = time_taken_ms
        custom_assessment["metadata"]["total_questions"] = total_q
        
        print(f"Generated {total_q} questions across {len(jd_skills)} dynamic modules in {time_taken_ms}ms")
        return custom_assessment

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate dynamic assessment from JD")
    parser.add_argument("--jd", type=str, required=True, help="Path to JD txt file or just a string snippet")
    parser.add_argument("--output", type=str, default="dynamic_assessment.json", help="Output file")
    
    args = parser.parse_args()
    
    # Try reading JD as a file; if it fails, treat it as raw text
    try:
        with open(args.jd, 'r', encoding='utf-8') as f:
            jd_text = f.read()
    except FileNotFoundError:
        jd_text = args.jd
    
    generator = DynamicAssessmentGenerator(db_path="assessment_questions.json")
    print(f"Question bank loaded in {generator.load_time*1000:.2f}ms")
    
    assessment = generator.generate_assessment(jd_text, num_questions_per_skill=4)
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(assessment, f, indent=2, ensure_ascii=False)
        
    print(f"Dynamic assessment successfully written to {args.output}")
