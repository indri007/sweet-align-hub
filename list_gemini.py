import os
from dotenv import load_dotenv
from google import genai
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
for m in client.models.list(config={"page_size": 50}):
    print(m.name)
