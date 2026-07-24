import sys
sys.path.insert(0, ".")

from qdrant_client import QdrantClient, models
from agents import interview_agent as ia

COLLECTION_NAME = "interview_questions_bank"
client = QdrantClient(":memory:")
client.create_collection(COLLECTION_NAME, vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE))
points = []
pid = 0
for tahap in ["Situation", "Task", "Action", "Result"]:
    points.append(models.PointStruct(
        id=pid, vector=[0.1, 0.2, 0.3, 0.4],
        payload={"kompetensi": "Kerjasama (Teamwork)", "tahap": tahap,
                 "pertanyaan": f"[Teamwork-{tahap}] pertanyaan contoh.",
                 "posisi_relevan": ["Umum"]},
    ))
    pid += 1
client.upsert(COLLECTION_NAME, points=points)

print("=== TEST A: relevan=true, lengkap=true -> harus dianggap CUKUP (maju) ===")
def mock_relevan_lengkap(messages, temperature, max_tokens):
    return '{"relevan": true, "lengkap": true, "alasan": "menjawab pertanyaan dengan detail"}'

session_a = ia.start_interview("dummy", {"job_title": "Umum"}, qdrant_client=client)
tahap_awal = session_a.turns[-1].tahap
next_q = ia.handle_candidate_answer(session_a, "Jawaban relevan dan detail.", chat_completion_fn=mock_relevan_lengkap)
assert session_a.turns[-1].tahap != tahap_awal or session_a.completed, "FAIL: harus maju ke tahap berikutnya"
assert not session_a.turns[-2].is_followup if len(session_a.turns) > 1 else True
print("  PASS: relevan+lengkap -> langsung maju, tidak ada follow-up.\n")

print("=== TEST B (FALSE NEGATIVE case): relevan=true TAPI lengkap=false -> follow-up muncul ===")
def mock_relevan_tidak_lengkap(messages, temperature, max_tokens):
    if "menilai jawaban kandidat" in messages[0]["content"]:
        return '{"relevan": true, "lengkap": false, "alasan": "kurang detail Action dan Result"}'
    return "Bisa dijelaskan langkah konkret apa yang Anda ambil?"

session_b = ia.start_interview("dummy", {"job_title": "Umum"}, qdrant_client=client)
q = ia.handle_candidate_answer(session_b, "Jawaban relevan tapi cuma nyebut Situation doang.", chat_completion_fn=mock_relevan_tidak_lengkap)
assert session_b.turns[-1].is_followup, "FAIL: harus jadi follow-up karena lengkap=false"
print(f"  PASS: relevan tapi tidak lengkap -> follow-up muncul: {q!r}\n")

print("=== TEST C (FALSE POSITIVE case yang HARUS ditolak): relevan=false TAPI lengkap=true -> tetap follow-up, BUKAN lolos ===")
def mock_lengkap_tapi_tidak_relevan(messages, temperature, max_tokens):
    content = messages[0]["content"]
    if "menilai jawaban kandidat" in content:
        return '{"relevan": false, "lengkap": true, "alasan": "jawaban membahas topik lain, tidak menjawab pertanyaan yang diajukan"}'
    return "Kembali ke pertanyaan awal, bisa diceritakan situasinya?"

session_c = ia.start_interview("dummy", {"job_title": "Umum"}, qdrant_client=client)
jawaban_off_topic_tapi_panjang = (
    "Saya sangat suka bermain sepak bola sejak kecil dan pernah menjadi kapten tim "
    "sekolah selama tiga tahun berturut-turut, itu pengalaman yang sangat berkesan."
)
q = ia.handle_candidate_answer(session_c, jawaban_off_topic_tapi_panjang, chat_completion_fn=mock_lengkap_tapi_tidak_relevan)
assert session_c.turns[-1].is_followup, "FAIL: jawaban off-topic (relevan=false) HARUS tetap memicu follow-up walau panjang"
print(f"  PASS: jawaban panjang tapi TIDAK relevan -> tetap ditolak (follow-up), tidak keliru lolos: {q!r}\n")

print("=== TEST D: guardrail follow-up cacat -> fallback ke teks aman, bukan tampil mentah ke kandidat ===")

def mock_followup_echo_pertanyaan(messages, temperature, max_tokens):
    content = messages[0]["content"]
    if "menilai jawaban kandidat" in content:
        return '{"relevan": true, "lengkap": false, "alasan": "kurang detail"}'
    return "[Teamwork-Situation] pertanyaan contoh."

session_d = ia.start_interview("dummy", {"job_title": "Umum"}, qdrant_client=client)
q = ia.handle_candidate_answer(session_d, "singkat", chat_completion_fn=mock_followup_echo_pertanyaan)
assert q == ia.FALLBACK_FOLLOWUP_TEXT, f"FAIL: echo pertanyaan harus ditolak & fallback, got {q!r}"
print(f"  PASS: follow-up yang cuma echo pertanyaan ditolak, fallback ke: {q!r}\n")


def mock_followup_broken_json_leftover(messages, temperature, max_tokens):
    content = messages[0]["content"]
    if "menilai jawaban kandidat" in content:
        return '{"relevan": true, "lengkap": false, "alasan": "kurang detail"}'
    return '{"pertanyaan": "ini seharusnya teks natural tapi LLM lupa keluar dari mode JSON"}'

session_e = ia.start_interview("dummy", {"job_title": "Umum"}, qdrant_client=client)
q = ia.handle_candidate_answer(session_e, "singkat", chat_completion_fn=mock_followup_broken_json_leftover)
assert q == ia.FALLBACK_FOLLOWUP_TEXT, f"FAIL: sisa artefak JSON harus ditolak & fallback, got {q!r}"
print(f"  PASS: follow-up dengan sisa artefak JSON ditolak, fallback ke teks aman.\n")

print("=== SEMUA TEST DUA-ARAH + GUARDRAIL PASS ===")
