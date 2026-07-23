import sys, os
sys.path.insert(0, os.path.abspath("."))
import config
from llm_client import chat_completion

print(f"Provider: {config.LLM_PROVIDER}")
try:
    messages = [{"role": "user", "content": "Halo, jawab dengan kata OK."}]
    response = chat_completion(messages=messages, temperature=0.7, max_tokens=100)
    print(f"Response: {repr(response)}")
except Exception as e:
    print(f"Exception: {e}")
