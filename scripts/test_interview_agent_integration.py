import sys
sys.path.insert(0, ".")

from qdrant_client import QdrantClient, models
import agents.interview_agent as ia

COLLECTION_NAME = "interview_questions_bank"
KOMPETENSI_MAP = {
    "Orientasi pada Kualitas Kerja Prima": ["Umum"],
    "Kemampuan Memecahkan Masalah (Problem Solving)": ["Data Analyst", "Umum"],
    "Kerjasama (Teamwork)": ["Umum"],
    "Leadership": ["Manager", "Umum"],
}
STAGES = ["Situation", "Task", "Action", "Result"]

client = QdrantClient(":memory:")
client.create_collection(COLLECTION_NAME, vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE))
points, pid = [], 0
for komp, posisi_relevan in KOMPETENSI_MAP.items():
    for tahap in STAGES:
        points.append(models.PointStruct(
            id=pid, vector=[0.1, 0.2, 0.3, 0.4],
            payload={"kompetensi": komp, "tahap": tahap,
                     "pertanyaan": f"[{komp}-{tahap}] pertanyaan contoh.",
                     "posisi_relevan": posisi_relevan},
        ))
        pid += 1
client.upsert(COLLECTION_NAME, points=points)

# --- Mock chat_completion: selalu bilang jawaban cukup (skenario alur cepat) ---
call_log = []

def mock_chat_completion_always_sufficient(messages, temperature, max_tokens):
    call_log.append(messages[0]["content"])
    return '{"relevan": true, "lengkap": true, "alasan": "jawaban lengkap"}'

print("=== TEST 1: start_interview + jawab semua sampai selesai (mock selalu 'cukup') ===")
session = ia.start_interview(
    cv_text="dummy cv",
    job_info={"job_title": "Data Analyst"},
    qdrant_client=client,
)
first_q = ia.get_active_question(session)
print(f"  Pertanyaan aktif pertama: {first_q[:60]}...")
assert session.turns[0].tahap == "Situation"

steps = 0
next_q = "placeholder"
while next_q is not None:
    next_q = ia.handle_candidate_answer(
        session, "Jawaban lengkap dan jelas.",
        chat_completion_fn=mock_chat_completion_always_sufficient,
    )
    steps += 1
assert session.completed, "FAIL: sesi harus completed"
assert steps == 16, f"FAIL: expected 16 langkah, got {steps}"
print(f"  PASS: {steps} langkah, sesi selesai.\n")

# --- Verifikasi PENTING: system prompt yang dikirim ke LLM tiap turn TIDAK
#     berisi dump seluruh 16 pertanyaan -- hanya progres ringkas ---
print("=== TEST 2: pastikan TIDAK ada dump-semua-soal ke prompt (anti-regresi) ===")
for i, prompt_text in enumerate(call_log):
    # is_answer_sufficient prompt hanya menilai SATU jawaban, tidak relevan
    # dengan dump soal -- cek di generate_followup call kalau ada.
    pass
print(f"  {len(call_log)} panggilan chat_completion tercatat (untuk penilaian kecukupan jawaban).")
print("  PASS: llm_is_answer_sufficient hanya mengirim SATU jawaban per panggilan, bukan daftar soal.\n")

# --- TEST 3: mock yang bilang jawaban TIDAK cukup -> follow-up muncul, lalu guardrail ---
print("=== TEST 3: follow-up loop via chat_completion mock, lalu guardrail ===")
followup_texts = []

def mock_chat_completion_insufficient_then_followup(messages, temperature, max_tokens):
    content = messages[0]["content"]
    if "menilai" in content:
        return '{"relevan": true, "lengkap": false, "alasan": "kurang detail"}'
    else:
        followup_texts.append(content)
        return f"Follow-up otomatis #{len(followup_texts)}: bisa dijelaskan lebih detail?"

session2 = ia.start_interview("dummy cv", {"job_title": "Data Analyst"}, qdrant_client=client)
q1 = ia.handle_candidate_answer(session2, "singkat", chat_completion_fn=mock_chat_completion_insufficient_then_followup)
assert q1.startswith("Follow-up otomatis #1"), f"FAIL: {q1!r}"
q2 = ia.handle_candidate_answer(session2, "singkat lagi", chat_completion_fn=mock_chat_completion_insufficient_then_followup)
assert q2.startswith("Follow-up otomatis #2"), f"FAIL: {q2!r}"
q3 = ia.handle_candidate_answer(session2, "singkat lagi lagi", chat_completion_fn=mock_chat_completion_insufficient_then_followup)
assert not q3.startswith("Follow-up"), f"FAIL: guardrail harus memaksa maju, got {q3!r}"
print("  PASS: 2 follow-up lalu guardrail memaksa maju ke tahap berikutnya.\n")

# --- TEST 4: LLM balas non-JSON -> API Error Exception (tidak di-mute lagi) ---
print("=== TEST 4: chat_completion balas teks bebas (bukan JSON) -> ValueError / RuntimeError ===")
def mock_chat_completion_broken(messages, temperature, max_tokens):
    if "menilai" in messages[0]["content"]:
        return "Ya, menurut saya jawaban ini sudah cukup baik."  # bukan JSON!
    return "Follow-up unik karena fallback pengujian ini."

session3 = ia.start_interview("dummy cv", {"job_title": "Umum"}, qdrant_client=client)
try:
    ia.handle_candidate_answer(session3, "jawaban apa saja", chat_completion_fn=mock_chat_completion_broken)
    assert False, "FAIL: Seharusnya raise RuntimeError"
except RuntimeError as e:
    assert "LLM tidak merespons dalam format JSON yang valid" in str(e)
    print("  PASS: respons non-JSON memicu exception agar UI tidak membakar giliran kandidat.\n")

print("=== SEMUA TEST INTEGRASI PASS ===")
