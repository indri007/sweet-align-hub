import sys, os
sys.path.insert(0, os.path.abspath('.'))

import config
from agents.interview_agent import llm_is_answer_sufficient

def run_test(pertanyaan, jawaban, expected_cukup, test_name):
    print(f"--- TEST: {test_name} ---")
    print(f"Q: {pertanyaan}")
    print(f"A: {jawaban}")
    
    # We use the real chat_completion here from llm_client
    # Make sure to not pass chat_completion_fn so it defaults to the real one
    
    is_cukup = llm_is_answer_sufficient(jawaban=jawaban, pertanyaan_aktif=pertanyaan)
    print(f"Result: Cukup? {is_cukup}")
    
    if is_cukup == expected_cukup:
        print("✅ PASS")
    else:
        print(f"❌ FAIL (Expected: {expected_cukup})")
    print()

def main():
    if not config.is_gemini_configured():
        print("Gemini API key is required for this test.")
        return
        
    print("MENGUJI KUALITAS LLM UNTUK RELEVANSI DAN KELENGKAPAN JAWABAN (FR-15)\n")
    
    # Tests 1-4 commented out to avoid rate limit for this specific proof
    
    # Test 5: Jawaban yang SANGAT komprehensif, relevan, dan terstruktur STAR dengan baik (True Positive test)
    run_test(
        pertanyaan="[Action] Ceritakan langkah demi langkah yang Anda ambil untuk menyelamatkan proyek tersebut dari keterlambatan.",
        jawaban="Pertama, saya mengumpulkan seluruh tim inti untuk melakukan meeting darurat selama 30 menit guna mengidentifikasi bottleneck utama, yang ternyata ada di proses integrasi API. Kedua, saya membagi ulang prioritas tugas di Trello, mendelegasikan tugas-tugas non-esensial ke sprint berikutnya. Ketiga, saya sendiri terjun langsung membantu tim backend melakukan pair programming selama dua hari berturut-turut untuk mempercepat penyelesaian endpoint yang kritis. Terakhir, saya mengkomunikasikan revisi timeline secara transparan kepada stakeholder agar ekspektasi mereka tetap terjaga.",
        expected_cukup=True,
        test_name="Sangat Relevan dan Sangat Lengkap (Action)"
    )

if __name__ == "__main__":
    main()
