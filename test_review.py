import config
from agents.cv_analyzer_agent import review_cv

# Ensure we bypass N8N to test the fallback directly
config.USE_N8N = False

res = review_cv("Software Engineer with Python experience", language="id")
print("RESULT:", res)
