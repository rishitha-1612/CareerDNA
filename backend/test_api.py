import requests
import json
try:
    r = requests.post("http://localhost:8000/api/v1/analyze/text", json={
        "resume_text": "I know python",
        "jd_text": "Need python developer",
        "candidate_name": "Test"
    })
    print("STATUS:", r.status_code)
    print("BODY:", r.text[:500])
except Exception as e:
    print("EXCEPTION:", e)
