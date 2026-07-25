import os
import requests
from dotenv import load_dotenv

load_dotenv(".env")

# Coba ambil URL, jika kosong fallback ke base kelasantai
base_url = os.environ.get("N8N_WEBHOOK_URL", "https://n8n.kelasantai.online")
api_key = os.environ.get("N8N_API_KEY", "")

print(f"Menggunakan N8N_WEBHOOK_URL: {base_url}")
print(f"API Key tersetting: {'Ya' if api_key else 'Tidak'}")

# Kita coba hit webhook test
url = base_url.rstrip("/") + "/webhook-test/job-assistant"
print(f"Mengirim POST request ke: {url}")

headers = {
    "Content-Type": "application/json"
}
if api_key:
    headers["Authorization"] = f"Bearer {api_key}"
    headers["X-API-Key"] = api_key
    # Jika Anda menggunakan Header Auth custom di n8n (seperti 'Header Auth account 2' di gambar),
    # pastikan nama header-nya sesuai. N8N biasanya default menggunakan header yang dikonfigurasi.
    # Kita coba kirim dua header umum.

payload = {
    "session_id": "test_session_123",
    "query": "Halo, ini pesan test dari script python!"
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"\nError saat menghubungi N8N: {e}")
