import sys
import os
import json
import dataclasses
sys.path.insert(0, ".")

from database import DatabaseManager, HrdTranscript
from agents.interview_agent_state import InterviewSession, InterviewTurn

def main():
    print("=== MENGUJI PENYIMPANAN TRANSKRIP WAWANCARA (FR-17) ===")
    
    # 1. Gunakan database SQLite in-memory untuk testing
    db = DatabaseManager("sqlite:///:memory:")
    db.create_tables()
    print("[INFO] Tabel berhasil dibuat di SQLite in-memory.")

    # 2. Buat mock data sesi wawancara
    session = InterviewSession(session_id="test-db-1234", posisi="Data Analyst", questions=[])
    session.turns = [
        InterviewTurn(
            kompetensi="Kemampuan Analitis",
            tahap="Situation",
            pertanyaan="Ceritakan masalah data yang rumit.",
            jawaban="Saya menemukan data yang tidak konsisten di CRM."
        )
    ]
    session.completed = True
    session.evaluation_result = {
        "evaluasi": [
            {
                "kompetensi": "Kemampuan Analitis",
                "label": "Baik",
                "feedback": "Penanganan masalah yang bagus."
            }
        ],
        "kesimpulan_umum": "Kandidat analitis."
    }

    email_user = "test_candidate@email.com"

    # 3. Simpan ke database
    try:
        session_dict = dataclasses.asdict(session)
        db.save_hrd_transcript(session_dict, email_user)
        print("[INFO] Transkrip berhasil disimpan ke database!")
    except Exception as e:
        print(f"❌ FAIL: Gagal menyimpan ke database. Error: {e}")
        return

    # 4. Verifikasi data tersimpan
    db_session = db.Session()
    record = db_session.query(HrdTranscript).filter_by(session_id="test-db-1234").first()
    
    if record:
        print("\n=== RECORD DITEMUKAN ===")
        print(f"ID: {record.id}")
        print(f"Session ID: {record.session_id}")
        print(f"Email: {record.email}")
        print(f"Posisi: {record.posisi}")
        print(f"Completed: {record.completed}")
        
        # Validasi struktur JSON di db (jika dikembalikan sbg objek di python / dict)
        print("\n[VALIDASI JSON COLUMNS]")
        is_transcript_valid = isinstance(record.transcript_json, list) and len(record.transcript_json) == 1
        is_eval_valid = isinstance(record.evaluation_result, dict) and "kesimpulan_umum" in record.evaluation_result
        
        print(f"Transcript JSON Array valid? {is_transcript_valid}")
        print(f"Evaluation JSON Object valid? {is_eval_valid}")
        
        if record.email == email_user and is_transcript_valid and is_eval_valid:
            print("\n✅ PASS: Data transkrip dan kolom JSON berhasil dibaca dan ditulis dengan benar.")
        else:
            print("\n❌ FAIL: Data yang disimpan tidak sesuai.")
    else:
        print("\n❌ FAIL: Record tidak ditemukan setelah disimpan.")
        
    db_session.close()

if __name__ == "__main__":
    main()
