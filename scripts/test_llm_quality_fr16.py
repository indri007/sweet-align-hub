import sys
import json
sys.path.insert(0, ".")

from agents.interview_agent import evaluate_interview
from agents.interview_agent_state import InterviewSession, InterviewTurn

def main():
    print("MENGUJI KUALITAS LLM UNTUK AGEN 6 (EVALUATOR SCORING - FR-16)\n")

    session = InterviewSession(session_id="test-evaluator-1", posisi="Data Analyst", questions=[])
    
    # Mocking a completed session transcript
    session.turns = [
        InterviewTurn(
            kompetensi="Kemampuan Analitis", 
            tahap="Situation", 
            pertanyaan="Ceritakan saat Anda harus menganalisis dataset besar dengan deadline ketat.",
            jawaban="Saat itu sistem CRM perusahaan error menjelang akhir bulan, sehingga saya harus merekonsiliasi 5 juta baris data transaksi secara manual dalam 2 hari untuk laporan keuangan direksi."
        ),
        InterviewTurn(
            kompetensi="Kemampuan Analitis", 
            tahap="Task", 
            pertanyaan="Apa target utama Anda?",
            jawaban="Targetnya memastikan tidak ada selisih angka antara data mentah dengan dashboard keuangan, dan melaporkannya tepat waktu."
        ),
        InterviewTurn(
            kompetensi="Kemampuan Analitis", 
            tahap="Action", 
            pertanyaan="Langkah spesifik apa yang Anda lakukan?",
            jawaban="Saya menggunakan Pandas di Python untuk mempercepat join tabel dan menemukan anomali. Lalu saya membuat skrip otomasi yang membersihkan data duplikat."
        ),
        InterviewTurn(
            kompetensi="Kemampuan Analitis", 
            tahap="Result", 
            pertanyaan="Bagaimana hasilnya?",
            jawaban="Laporan selesai 6 jam sebelum deadline dengan akurasi 100%, dan skrip saya sekarang dijadikan standar operasional perusahaan."
        ),
        # Bad answers for second competency
        InterviewTurn(
            kompetensi="Kerjasama Tim", 
            tahap="Situation", 
            pertanyaan="Pernahkah Anda berkonflik dengan rekan kerja?",
            jawaban="Pernah, teman saya malas."
        ),
        InterviewTurn(
            kompetensi="Kerjasama Tim", 
            tahap="Task", 
            pertanyaan="Apa yang Anda coba capai?",
            jawaban="Ya biar dia kerja."
        ),
        InterviewTurn(
            kompetensi="Kerjasama Tim", 
            tahap="Action", 
            pertanyaan="Bagaimana cara Anda menghadapinya?",
            jawaban="Saya marahi saja biar dia sadar diri."
        ),
        InterviewTurn(
            kompetensi="Kerjasama Tim", 
            tahap="Result", 
            pertanyaan="Apa akhirnya?",
            jawaban="Akhirnya dia kesal tapi kerjaannya selesai."
        ),
    ]
    
    session.completed = True

    try:
        print("[INFO] Memanggil Evaluator LLM...")
        result = evaluate_interview(session)
        print("\n=== HASIL EVALUASI ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Validate Structure
        assert "evaluasi" in result, "Kunci 'evaluasi' hilang dari JSON"
        assert "kesimpulan_umum" in result, "Kunci 'kesimpulan_umum' hilang dari JSON"
        assert len(result["evaluasi"]) == 2, "Harusnya ada 2 kompetensi yang dievaluasi"
        
        label_analitis = result["evaluasi"][0].get("label", "")
        label_tim = result["evaluasi"][1].get("label", "")
        
        print(f"\nLabel Analitis (Expected: Baik): {label_analitis}")
        print(f"Label Tim (Expected: Kurang): {label_tim}")
        
        assert label_analitis in ["Kurang", "Cukup", "Baik"], f"Label Analitis keluar dari opsi yang diizinkan: {label_analitis}"
        assert label_tim in ["Kurang", "Cukup", "Baik"], f"Label Tim keluar dari opsi yang diizinkan: {label_tim}"
        
        if label_analitis == "Baik" and label_tim == "Kurang":
            print("\n✅ PASS: Evaluator berfungsi logis dan akurat membedakan jawaban STAR yang bagus dan buruk.")
        else:
            print("\n❌ FAIL: Evaluator tidak memberikan label yang sesuai dengan logika STAR.")
            
    except Exception as e:
        print(f"\n❌ FAIL: Terjadi error - {e}")

if __name__ == "__main__":
    main()
