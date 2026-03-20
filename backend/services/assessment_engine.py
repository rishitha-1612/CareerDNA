import random
import re
import uuid

class ProceduralAssessmentEngine:
    def __init__(self):
        # NLP Keywords to map JD to our procedural generators
        self.skill_map = {
            "python": [r"\bpython\b", r"\bdjango\b", r"\bfastapi\b", r"\bflask\b"],
            "sql": [r"\bsql\b", r"\bpostgresql\b", r"\bmysql\b", r"\brdbms\b"],
            "javascript": [r"\bjavascript\b", r"\bjs\b", r"\bfrontend\b", r"\breact\b", r"\bnode\.?js\b"],
            "aws": [r"\baws\b", r"\bcloud\b", r"\bec2\b", r"\bs3\b"]
        }
        self.compiled_regexes = {k: [re.compile(p, re.IGNORECASE) for p in v] for k, v in self.skill_map.items()}

    def _extract_skills(self, text: str):
        detected = []
        for skill_id, regexes in self.compiled_regexes.items():
            if any(r.search(text) for r in regexes):
                detected.append(skill_id)
        if len(detected) < 2:
            defaults = ["python", "sql", "javascript"]
            for d in defaults:
                if d not in detected and len(detected) < 2:
                    detected.append(d)
        return detected

    def _generate_python_question(self, level: str):
        if level == "beginner":
            vars_names = ["a", "b", "x", "y", "count", "total"]
            v1, v2 = random.sample(vars_names, 2)
            n1, n2 = random.randint(1, 10), random.randint(1, 10)
            op = random.choice(["+", "-", "*"])
            q_text = f"What is the output of the following Python code?\n\n```python\n{v1} = {n1}\n{v2} = {n2}\nprint({v1} {op} {v2})\n```"
            ans = eval(f"{n1} {op} {n2}")
            options = [str(ans), str(ans + 1), str(ans - 1), str(n1) + str(n2)]
            random.shuffle(options)
            return {"id": str(uuid.uuid4()), "skill": "Python", "question": q_text, "options": options, "correct": str(ans)}
            
        elif level == "intermediate":
            structs = [
                ("[1, 2, 3, 4, 5]", "len"),
                ("{'a': 1, 'b': 2}", "len"),
                ("set([1, 1, 2, 3])", "len"),
                ("'hello'", "len")
            ]
            s, func = random.choice(structs)
            q_text = f"What is the output of `{func}({s})` in Python?"
            ans = eval(f"{func}({s})")
            options = [str(ans), str(ans + 1), str(ans - 1), "Error"]
            random.shuffle(options)
            return {"id": str(uuid.uuid4()), "skill": "Python", "question": q_text, "options": options, "correct": str(ans)}
            
        else: # advanced
            # Slicing or list comp
            arr = [random.randint(1, 10) for _ in range(5)]
            start = random.randint(0, 2)
            end = random.randint(3, 4)
            q_text = f"Given `arr = {arr}`, what does `arr[{start}:{end}]` evaluate to?"
            ans = str(arr[start:end])
            options = [ans, str(arr[start:end+1]), str(arr[start-1:end]), "IndexError"]
            random.shuffle(options)
            return {"id": str(uuid.uuid4()), "skill": "Python", "question": q_text, "options": options, "correct": ans}

    def _generate_sql_question(self, level: str):
        tables = ["users", "orders", "products", "employees"]
        cols = ["id", "name", "created_at", "status", "price", "department"]
        t = random.choice(tables)
        
        if level == "beginner":
            c = random.choice(cols)
            q_text = f"Which SQL statement correctly selects all {c} from the {t} table?"
            ans = f"SELECT {c} FROM {t};"
            options = [ans, f"EXTRACT {c} FROM {t};", f"GET {c} IN {t};", f"SELECT FROM {t} WHERE {c};"]
            random.shuffle(options)
            return {"id": str(uuid.uuid4()), "skill": "SQL", "question": q_text, "options": options, "correct": ans}
        elif level == "intermediate":
            q_text = f"How do you count the total number of records in the `{t}` table?"
            ans = f"SELECT COUNT(*) FROM {t};"
            options = [ans, f"SELECT TOTAL() FROM {t};", f"COUNT {t};", f"SELECT SUM(records) FROM {t};"]
            random.shuffle(options)
            return {"id": str(uuid.uuid4()), "skill": "SQL", "question": q_text, "options": options, "correct": ans}
        else:
            q_text = f"Which clause is used to filter the results of an aggregate function like `COUNT` on the `{t}` table?"
            ans = "HAVING"
            options = [ans, "WHERE", "FILTER", "GROUP BY"]
            random.shuffle(options)
            return {"id": str(uuid.uuid4()), "skill": "SQL", "question": q_text, "options": options, "correct": ans}

    def _generate_js_question(self, level: str):
        if level == "beginner":
            q_text = "Which keyword is used to declare a block-scoped variable in modern JavaScript?"
            ans = random.choice(["let", "const"])
            options = ["let", "var", "int", "def"] if ans == "let" else ["const", "var", "final", "static"]
            random.shuffle(options)
            return {"id": str(uuid.uuid4()), "skill": "JavaScript", "question": q_text, "options": options, "correct": ans}
        else:
            arr = [random.randint(1, 5) for _ in range(3)]
            mult = random.randint(2, 4)
            q_text = f"What does `[{', '.join(map(str, arr))}].map(x => x * {mult})` return?"
            ans = str([x * mult for x in arr])
            options = [ans, str([x + mult for x in arr]), "undefined", "TypeError"]
            random.shuffle(options)
            return {"id": str(uuid.uuid4()), "skill": "JavaScript", "question": q_text, "options": options, "correct": ans}

    def _generate_aws_question(self, level: str):
        # Even procedural templates can use domain knowledge rules
        services = {"EC2": "Compute", "S3": "Object Storage", "RDS": "Relational Database", "Lambda": "Serverless Functions"}
        svc, desc = random.choice(list(services.items()))
        q_text = f"In AWS, which service is primarily known for '{desc}'?"
        options = [svc]
        others = list(services.keys())
        others.remove(svc)
        options.extend(random.sample(others, 3))
        random.shuffle(options)
        return {"id": str(uuid.uuid4()), "skill": "AWS", "question": q_text, "options": options, "correct": svc}

    def generate_assessment(self, jd_text: str, level: str, num_questions_per_skill: int = 2):
        target_skills = self._extract_skills(jd_text)
        modules = []
        for skill in target_skills:
            qs = []
            for _ in range(num_questions_per_skill):
                if skill == "python": qs.append(self._generate_python_question(level))
                elif skill == "sql": qs.append(self._generate_sql_question(level))
                elif skill == "javascript": qs.append(self._generate_js_question(level))
                elif skill == "aws": qs.append(self._generate_aws_question(level))
            modules.append({
                "skill_name": skill.upper(),
                "questions": qs
            })
        return {"modules": modules}

    def score_assessment(self, answers_payload: dict):
        """
        Expects a payload like:
        {
           "modules": [... original modules with questions ...],
           "candidate_answers": {
               "uuid1": "Selected Option",
               "uuid2": "Selected Option"
           }
        }
        """
        modules = answers_payload.get("modules", [])
        user_ans = answers_payload.get("candidate_answers", {})
        
        total_q = 0
        correct_q = 0
        breakdown = {}
        
        for mod in modules:
            s_name = mod["skill_name"]
            breakdown[s_name] = {"total": 0, "correct": 0}
            for q in mod["questions"]:
                total_q += 1
                breakdown[s_name]["total"] += 1
                qid = q["id"]
                if user_ans.get(qid) == q["correct"]:
                    correct_q += 1
                    breakdown[s_name]["correct"] += 1
                    
        score = (correct_q / total_q * 100) if total_q > 0 else 0
        return {
            "score_percentage": round(score, 1),
            "breakdown": breakdown,
            "total_questions": total_q,
            "correct_answers": correct_q
        }
