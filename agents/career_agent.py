"""
Career Consultant Agent — AI career advisor for chat-based consultation.
Multi-turn conversation about career goals, aspirations, and skill development.
"""

import config


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
) -> dict:
    """
    Generate career consultation response.

    Args:
        cv_text: The user's CV content
        chat_history: List of {"role": "user"/"assistant", "content": "..."} messages
        user_message: Current user message

    Returns dict with:
    - "response": AI response text
    - "available": whether OpenAI is configured
    """
    if not config.is_gemini_configured():
        return {
            "response": None,
            "available": False,
        }

    try:
        client = config.get_gemini_client()
        
        # Build conversation as a list of contents
        contents = []
        if cv_text:
            contents.append({"role": "user", "parts": [{"text": f"[KONTEKS: Berikut CV saya untuk referensi]\n\n{cv_text[:4000]}"}]})
            contents.append({"role": "model", "parts": [{"text": "Terima kasih sudah berbagi CV kamu! Saya sudah membacanya. Silakan ceritakan tentang cita-cita atau tujuan karir yang ingin kamu capai. 😊"}]})

        for msg in chat_history:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        contents.append({"role": "user", "parts": [{"text": user_message}]})

        from google.genai import types
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[types.Tool(google_search=types.GoogleSearch())]
            ),
        )
        return {
            "response": response.text,
            "available": True,
        }
    except Exception as e:
        return {
            "response": f"Error: {str(e)}",
            "available": True,
        }
