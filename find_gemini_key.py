import os
from google import genai

keys = [
    "***GEMINI_KEY_ROTATED***",
    "***GEMINI_KEY_ROTATED***",
    "***GEMINI_KEY_ROTATED***",
    "***GEMINI_KEY_ROTATED***"
]

print("Testing Gemini Keys...")
working_key = None
for key in keys:
    try:
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(model="gemini-2.5-flash", contents="Test")
        print(f"SUCCESS with key: {key}")
        working_key = key
        break
    except Exception as e:
        print(f"FAILED for {key}: {str(e)[:150]}...")

if working_key:
    env_path = "/Users/jevin/Downloads/sweet-align-hub-backup-20260718/sweet-align-hub-extracted/.env"
    with open(env_path, "r") as f:
        content = f.read()
    import re
    content = re.sub(r'GEMINI_API_KEY=.*', f'GEMINI_API_KEY="{working_key}"', content)
    with open(env_path, "w") as f:
        f.write(content)
    print("Updated .env with working key.")
else:
    print("NO WORKING KEYS FOUND.")
