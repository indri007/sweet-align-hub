import sys
import os
sys.path.insert(0, ".")

from qdrant_client import QdrantClient, models
import agents.interview_agent as ia

COLLECTION_NAME = "interview_questions_bank"

# Data mock persis meniru struktur nyata: 10 kompetensi x 4 tahap STAR,
# plus payload posisi_relevan seperti yang dihasilkan update_interview_kb_posisi.py
KOMPETENSI_MAP = {
    "Orientasi pada Kualitas Kerja Prima": ["Umum"],
    "Kemampuan Memecahkan Masalah (Problem Solving)": ["Data Analyst", "Software Engineer", "Product Manager", "Umum"],
    "Perencanaan Kerja (Planning)": ["Project Manager", "Product Manager", "Operations", "Umum"],
    "Kerjasama (Teamwork)": ["Umum"],
    "Inisiatif": ["Umum"],
    "Leadership": ["Team Lead", "Manager", "Supervisor"],
    "Negosiasi (Negotiation Skills)": ["Sales", "Business Development", "Procurement"],
    "Learning Skills": ["Umum"],
    "Mentoring (Mentor)": ["Senior Staff", "Team Lead", "Manager"],
    "Communication Skills": ["Umum"],
}
STAGES = ["Situation", "Task", "Action", "Result"]

client = QdrantClient(":memory:")
client.create_collection(
    COLLECTION_NAME,
    vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE),
)

points = []
pid = 0
for komp, posisi_relevan in KOMPETENSI_MAP.items():
    for tahap in STAGES:
        points.append(models.PointStruct(
            id=pid,
            vector=[0.1, 0.2, 0.3, 0.4],  # vektor dummy -- kita test filter, bukan similarity
            payload={
                "kompetensi": komp,
                "tahap": tahap,
                "pertanyaan": f"[{komp} - {tahap}] contoh pertanyaan.",
                "posisi_relevan": posisi_relevan,
                "kategori_posisi": "Umum" if posisi_relevan == ["Umum"] else "Spesifik",
            },
        ))
        pid += 1

client.upsert(COLLECTION_NAME, points=points)
print(f"Upserted {len(points)} mock points (10 kompetensi x 4 tahap).\n")

# --- TEST 1: posisi spesifik yang match beberapa kompetensi + Umum ---
print("=== TEST 1: posisi='Data Analyst' ===")
result = ia.get_interview_questions("Data Analyst", jumlah_kompetensi=3, client=client)
for r in result:
    tahap_order = list(r["pertanyaan_star"].keys())
    print(f"  - {r['kompetensi']!r}: urutan tahap = {tahap_order} (harus S,T,A,R)")
    assert tahap_order == STAGES, f"FAIL: urutan tahap salah untuk {r['kompetensi']}"
assert len(result) == 3, f"FAIL: expected 3 kompetensi, got {len(result)}"
print("  PASS: jumlah kompetensi & urutan STAR benar.\n")

# --- TEST 2: posisi yang sama sekali tidak ada di data -> fallback ke Umum saja ---
print("=== TEST 2: posisi='Posisi Yang Tidak Ada' (fallback ke Umum) ===")
result2 = ia.get_interview_questions("Posisi Yang Tidak Ada", jumlah_kompetensi=2, client=client)
umum_only_komps = {k for k, v in KOMPETENSI_MAP.items() if v == ["Umum"]}
for r in result2:
    assert r["kompetensi"] in umum_only_komps, f"FAIL: {r['kompetensi']} bukan kompetensi Umum"
print(f"  PASS: {len(result2)} kompetensi diambil, semuanya dari kategori Umum sesuai fallback.\n")

# --- TEST 3: posisi spesifik untuk kompetensi Leadership ---
print("=== TEST 3: posisi='Manager' ===")
result3 = ia.get_interview_questions("Manager", jumlah_kompetensi=10, client=client)
komp_names = {r["kompetensi"] for r in result3}
assert "Leadership" in komp_names, "FAIL: Leadership harus ikut untuk posisi Manager"
assert "Mentoring (Mentor)" in komp_names, "FAIL: Mentoring harus ikut untuk posisi Manager"
assert "Negosiasi (Negotiation Skills)" not in komp_names, "FAIL: Negotiation seharusnya tidak relevan untuk Manager (bukan Sales/BD)"
print(f"  PASS: {len(komp_names)} kompetensi termasuk Leadership & Mentoring, TIDAK termasuk Negotiation.\n")

# --- TEST 4: collection kosong / field posisi_relevan tidak ada -> harus raise, bukan silent empty ---
print("=== TEST 4: error handling saat tidak ada data cocok ===")
client.create_collection(
    "empty_bank",
    vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE),
)
ia.COLLECTION_NAME = "empty_bank"
try:
    ia.get_interview_questions("Data Analyst", client=client)
    print("  FAIL: seharusnya raise ValueError")
except ValueError as e:
    print(f"  PASS: ValueError ter-raise dengan pesan jelas -> {e}\n")
ia.COLLECTION_NAME = COLLECTION_NAME

print("=== SEMUA TEST PASS ===")
