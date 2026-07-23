import os
from dotenv import load_dotenv

print("Loading .env...")
load_dotenv()

print("\n--- Testing Qdrant ---")
try:
    from qdrant_client import QdrantClient
    client = QdrantClient(url=os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY'))
    print("Qdrant Collections:", client.get_collections())
except Exception as e:
    print("Qdrant Error:", e)

print("\n--- Testing MySQL ---")
try:
    import ssl
    from sqlalchemy import create_engine, text
    engine = create_engine(os.getenv('DATABASE_URL'), connect_args={"ssl": {"check_hostname": False, "verify_mode": ssl.CERT_NONE}})
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("MySQL OK:", result.fetchone())
except Exception as e:
    print("MySQL Error:", e)

print("\n--- Testing Gemini ---")
try:
    from google import genai
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    resp = client.models.generate_content(model="gemini-flash-latest", contents="Halo, respond with 'Koneksi Gemini Sukses!'")
    print("Gemini Response:", resp.text.strip())
except Exception as e:
    print("Gemini Error:", e)
