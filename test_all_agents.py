import sys
import os

import config

print("=== VERIFIKASI SISTEM LLM & AGENT ===")
print(f"LLM Provider Aktif: {config.LLM_PROVIDER}")
print(f"Model Utama: {config.GROQ_MODEL if config.LLM_PROVIDER == 'groq' else 'Lainnya'}")

try:
    from agents.cv_analyzer_agent import review_cv
    print("\n[1/3] Mengetes Modul Analisis CV...")
    res = review_cv(cv_text="Nama: Budi. Pengalaman: 5 Tahun Software Engineer.", target_job=None, language="id")
    print("✓ Berhasil! Preview Output:", res["feedback"][:100].replace("\n", " "), "...")
except Exception as e:
    print("✗ Gagal modul CV:", e)

try:
    from agents.career_agent import get_career_response
    print("\n[2/3] Mengetes Modul Konsultasi Karir...")
    res = get_career_response(cv_text="Budi, SE", chat_history=[], user_message="Halo, saya ingin mengubah jalur karir saya.")
    print("✓ Berhasil! Preview Output:", res["response"][:100].replace("\n", " "), "...")
except Exception as e:
    print("✗ Gagal modul Karir:", e)

try:
    from agents.interview_agent import start_interview
    print("\n[3/3] Mengetes Modul Mock Interview...")
    res = start_interview(cv_text="Budi, SE", job_info={"job_title": "Software Engineer", "company_name": "Google", "job_description": "Coding in Python"})
    print("✓ Berhasil! Preview Output:", res["response"][:100].replace("\n", " "), "...")
except Exception as e:
    print("✗ Gagal modul Wawancara:", e)

print("\n=== VERIFIKASI SELESAI ===")
