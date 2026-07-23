import sys
sys.path.insert(0, ".")

from qdrant_client import QdrantClient, models
import agents.interview_agent_questions as iq
import agents.interview_agent_state as ist

COLLECTION_NAME = "interview_questions_bank"
client = QdrantClient(":memory:")
client.create_collection(COLLECTION_NAME, vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE))
points = [
    models.PointStruct(
        id=0, vector=[0.1, 0.2, 0.3, 0.4],
        payload={"kompetensi": "Kerjasama (Teamwork)", "tahap": "Situation",
                 "pertanyaan": "[Teamwork-Situation] contoh.", "posisi_relevan": ["Umum"]},
    )
]
# perlu 4 tahap supaya start_interview tidak error di stage lain -- tapi test ini
# cuma butuh 1 kompetensi untuk memicu followup di tahap pertama
for i, tahap in enumerate(["Task", "Action", "Result"], start=1):
    points.append(models.PointStruct(
        id=i, vector=[0.1, 0.2, 0.3, 0.4],
        payload={"kompetensi": "Kerjasama (Teamwork)", "tahap": tahap,
                 "pertanyaan": f"[Teamwork-{tahap}] contoh.", "posisi_relevan": ["Umum"]},
    ))
client.upsert(COLLECTION_NAME, points=points)

print("=== TEST: system prompt follow-up HARUS memuat jawaban kandidat, bukan kosong ===\n")

session = ist.start_interview("Umum", jumlah_kompetensi=1, get_questions_fn=iq.get_interview_questions, client=client)

captured_prompt = {}

def is_answer_sufficient_selalu_kurang(jawaban: str) -> bool:
    return False  # paksa masuk jalur follow-up

def generate_followup_intercept(system_prompt: str) -> str:
    captured_prompt["text"] = system_prompt  # rekam PERSIS apa yang dikirim ke LLM
    return "Follow-up: bisa dijelaskan lebih detail?"

jawaban_kandidat = "JAWABAN_UNIK_UNTUK_DIVERIFIKASI_12345"

ist.record_answer_and_get_next(
    session,
    jawaban_kandidat,
    is_answer_sufficient_fn=is_answer_sufficient_selalu_kurang,
    generate_followup_fn=generate_followup_intercept,
)

prompt_yang_dikirim = captured_prompt["text"]
print("System prompt yang benar-benar dikirim ke LLM:")
print("---")
print(prompt_yang_dikirim)
print("---\n")

assert jawaban_kandidat in prompt_yang_dikirim, (
    f"FAIL (BUG TERKONFIRMASI): jawaban kandidat {jawaban_kandidat!r} TIDAK ada di system "
    f"prompt yang dikirim ke LLM. LLM akan melihat 'Jawaban kandidat: ' kosong, "
    f"padahal kandidat sudah menjawab -- follow-up yang dihasilkan tidak akan "
    f"kontekstual terhadap jawaban sesungguhnya."
)
print("✅ PASS: jawaban kandidat benar-benar termuat di system prompt yang dikirim ke LLM.")
