"""
Career Consultant Agent — AI career advisor for chat-based consultation.
Multi-turn conversation about career goals, aspirations, and skill development.
"""

import config
from llm_client import chat_completion


SYSTEM_PROMPT = """Kamu adalah Career Consultant AI yang berpengalaman dengan kemampuan pencarian Google secara real-time. Tugasmu adalah membantu user mendiskusikan karir, cita-cita, dan mencarikan lowongan pekerjaan eksternal.

Konteks: User telah meng-upload CV mereka. Berdasarkan CV tersebut dan pencarian web secara real-time, bantu mereka:
1. Memahami posisi karir mereka saat ini.
2. Mengeksplorasi cita-cita, tren industri terbaru, dan estimasi gaji.
3. Mencari lowongan pekerjaan relevan secara real-time di Google, LinkedIn, dan Jobstreet menggunakan alat Google Search yang Anda miliki.
4. Merekomendasikan langkah-langkah konkret atau sertifikasi yang diperlukan.

Rules:
- Gunakan alat pencarian Google untuk mencari lowongan aktif, syarat kualifikasi terbaru, atau info tren industri.
- Jika user meminta dicarikan lowongan kerja baru di platform tertentu (Google, LinkedIn, Jobstreet), lakukan pencarian web dan berikan daftar lowongan aktif lengkap dengan NAMA POSISI, PERUSAHAAN, LOKASI, dan LINK sumber lowongan tersebut agar user bisa langsung melamar.
- Jawab dalam Bahasa Indonesia yang profesional dan supportive.
- Berikan saran yang spesifik, relevan, dan actionable."""


def get_career_response(
    cv_text: str,
    chat_history: list[dict],
    user_message: str,
    target_job: dict = None,
) -> dict:
    """
    Generate career consultation response.

    Args:
        cv_text: The user's CV content
        chat_history: List of {"role": "user"/"assistant", "content": "..."} messages
        user_message: Current user message
        target_job: Optional dict with target job info (job_title, company_name, job_description)

    Returns dict with:
    - "response": AI response text
    - "available": whether LLM/N8N is configured
    """
    # Try N8N first
    if config.is_n8n_configured():
        try:
            from n8n_client import career_chat_n8n
            ai_text = career_chat_n8n(cv_text, chat_history, user_message, target_job=target_job)
            if ai_text and not ai_text.startswith("Error") and not ai_text.startswith("Tidak dapat") and not ai_text.startswith("N8N"):
                return {"response": ai_text, "available": True}
        except Exception:
            pass

    if not config.is_llm_configured():
        return {
            "response": None,
            "available": False,
        }

    try:
        # Build system prompt with target job context
        enhanced_prompt = SYSTEM_PROMPT
        if target_job:
            enhanced_prompt += f"""\n\nKONTEKS PENTING: User menargetkan posisi spesifik:
- Posisi: {target_job.get('job_title', 'N/A')}
- Perusahaan: {target_job.get('company_name', 'N/A')}

Fokuskan saran karir kamu untuk membantu user mencapai posisi tersebut.
Berikan insight tentang skill yang dibutuhkan, cara mempersiapkan diri, dan langkah konkret menuju posisi tersebut."""

        # Build messages
        messages = [
            {"role": "system", "content": enhanced_prompt},
        ]

        # Add CV context as first user message if available
        if cv_text:
            messages.append({
                "role": "user",
                "content": f"[KONTEKS: Berikut CV saya untuk referensi]\n\n{cv_text[:4000]}",
            })
            messages.append({
                "role": "assistant",
                "content": "Terima kasih sudah berbagi CV kamu! Saya sudah membacanya. Silakan ceritakan tentang cita-cita atau tujuan karir yang ingin kamu capai, dan saya akan bantu memberikan saran berdasarkan profil kamu saat ini. 😊",
            })

        # Add conversation history
        for msg in chat_history:
            messages.append(msg)

        # Add current message
        messages.append({"role": "user", "content": user_message})

        reply = chat_completion(messages=messages, temperature=0.7, max_tokens=1500, use_google_search=True, agent_id=3)

        return {
            "response": reply,
            "available": True,
        }
    except Exception as e:
        return {
            "response": f"Error: {str(e)}",
            "available": True,
        }
