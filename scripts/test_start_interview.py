import sys, os, json
sys.path.insert(0, os.path.abspath("."))
import config
from agents import interview_agent

# Monkey-patch chat_completion to intercept the prompt
def mock_chat_completion(messages, temperature, max_tokens):
    print("=== INTERCEPTED SYSTEM PROMPT ===")
    for msg in messages:
        if msg["role"] == "system":
            print(msg["content"])
            print("=================================")
    return "MOCK AI QUESTION"

interview_agent.chat_completion = mock_chat_completion

job_info = {
    "job_title": "Data Analyst",
    "company_name": "PT Tech Indonesia",
    "job_description": "Membutuhkan Data Analyst dengan pengalaman SQL dan Python."
}
cv_text = "Nama: Jevin\nPengalaman: 3 tahun bekerja sebagai Data Analyst..."

print("Running start_interview...")
result = interview_agent.start_interview(cv_text, job_info)
print("\nResult:", result)
