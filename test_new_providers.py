import config
import llm_client

# Test Cerebras
config.LLM_PROVIDER = "cerebras"
print("Testing Cerebras...")
try:
    res = llm_client.chat_completion([{"role": "user", "content": "Hello, Cerebras!"}], max_tokens=10)
    print("Cerebras result:", res)
except Exception as e:
    print("Cerebras failed:", e)

# Test Zhipu
config.LLM_PROVIDER = "zhipu"
print("\nTesting Zhipu...")
try:
    res = llm_client.chat_completion([{"role": "user", "content": "Hello, Zhipu!"}], max_tokens=10)
    print("Zhipu result:", res)
except Exception as e:
    print("Zhipu failed:", e)

# Test Groq rotation
config.LLM_PROVIDER = "groq"
print("\nTesting Groq Rotation...")
try:
    res = llm_client.chat_completion([{"role": "user", "content": "Hello, Groq!"}], max_tokens=10)
    print("Groq result:", res)
except Exception as e:
    print("Groq failed:", e)

