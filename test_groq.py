import llm_client
try:
    print(llm_client.chat_completion([{"role": "user", "content": "hello"}]))
except Exception as e:
    print("ERROR:", e)
