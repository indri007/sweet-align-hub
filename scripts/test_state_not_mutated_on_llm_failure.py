import sys
sys.path.insert(0, ".")

from qdrant_client import QdrantClient, models
from agents import interview_agent_questions as iq
from agents import interview_agent_state as ist

COLLECTION_NAME = "interview_questions_bank"
client = QdrantClient(":memory:")
client.create_collection(COLLECTION_NAME, vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE))
points = []
for i, tahap in enumerate(["Situation", "Task", "Action", "Result"]):
    points.append(models.PointStruct(
        id=i, vector=[0.1, 0.2, 0.3, 0.4],
        payload={"kompetensi": "Kerjasama (Teamwork)", "tahap": tahap,
                 "pertanyaan": f"[Teamwork-{tahap}] pertanyaan contoh.",
                 "posisi_relevan": ["Umum"]},
    ))
client.upsert(COLLECTION_NAME, points=points)


def snapshot(session):
    return {
        "jumlah_turns": len(session.turns),
        "jawaban_turn_aktif": session.turns[-1].jawaban if session.turns else None,
        "completed": session.completed,
        "komp_index": session.komp_index,
        "stage_index": session.stage_index,
    }


def is_answer_sufficient_gagal_total(jawaban):
    raise RuntimeError(
        "Gemini 429 Rate Limit -- OPENAI_API_KEY kosong, tidak ada fallback provider tersedia."
    )


print("=== TEST: state TIDAK BOLEH berubah kalau LLM gagal total (RuntimeError) ===\n")

session = ist.start_interview(
    "Umum", jumlah_kompetensi=1, get_questions_fn=iq.get_interview_questions, client=client
)

before = snapshot(session)
print(f"State SEBELUM panggilan: {before}")

jawaban_kandidat = "Ini jawaban kandidat yang seharusnya TIDAK tercatat kalau LLM gagal total."

exception_tertangkap = None
try:
    ist.record_answer_and_get_next(
        session,
        jawaban_kandidat,
        is_answer_sufficient_fn=is_answer_sufficient_gagal_total,
        generate_followup_fn=None,
    )
except RuntimeError as e:
    exception_tertangkap = e
    print(f"\nRuntimeError tertangkap (sesuai ekspektasi): {e}\n")

after = snapshot(session)
print(f"State SESUDAH panggilan (dan exception ditangkap): {after}\n")

assert exception_tertangkap is not None, "FAIL: RuntimeError seharusnya benar-benar terlempar."
assert after == before, (
    f"FAIL: state BERUBAH walau LLM gagal total -- ini bug 'turn terbakar'.\n"
    f"  Sebelum : {before}\n"
    f"  Sesudah : {after}"
)

print("PASS: state persis identik sebelum dan sesudah kegagalan LLM.")
print("   Tidak ada turn baru, jawaban kandidat TIDAK tercatat, giliran tidak hilang.")
print("   Kandidat aman untuk menekan submit ulang tanpa kehilangan progres.\n")


print("=== TEST 2: titik kegagalan KEDUA -- generate_followup_fn gagal (bukan is_answer_sufficient_fn) ===\n")

def is_answer_sufficient_bilang_kurang(jawaban):
    return False

def generate_followup_gagal_total(system_prompt):
    raise RuntimeError("Gemini 429 Rate Limit saat generate follow-up -- tidak ada fallback.")

session2 = ist.start_interview(
    "Umum", jumlah_kompetensi=1, get_questions_fn=iq.get_interview_questions, client=client
)
before2 = snapshot(session2)
print(f"State SEBELUM panggilan: {before2}")

exception2 = None
try:
    ist.record_answer_and_get_next(
        session2,
        "jawaban singkat",
        is_answer_sufficient_fn=is_answer_sufficient_bilang_kurang,
        generate_followup_fn=generate_followup_gagal_total,
    )
except RuntimeError as e:
    exception2 = e
    print(f"\nRuntimeError tertangkap (sesuai ekspektasi): {e}\n")

after2 = snapshot(session2)
print(f"State SESUDAH panggilan: {after2}\n")

assert exception2 is not None, "FAIL: RuntimeError seharusnya terlempar dari generate_followup_fn."
assert after2 == before2, (
    f"FAIL: state berubah walau generate_followup_fn gagal total.\n"
    f"  Sebelum : {before2}\n  Sesudah : {after2}"
)
print("PASS: kegagalan di titik generate_followup_fn JUGA tidak mengubah state.\n")

print("=== SEMUA TEST PEMBUKTIAN 'MENUNDA MUTASI STATE' PASS ===")
