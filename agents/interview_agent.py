"""
Mock Interview Agent — Simulates HR interview with AI.
Supports text-based and voice-based (OpenAI Whisper + TTS) interview.
"""

import config


INTERVIEWER_PROMPT = """Kamu adalah seorang HR Interviewer profesional di perusahaan besar Indonesia. 
Kamu sedang melakukan mock interview dengan seorang kandidat.

Konteks:
- CV Kandidat sudah diberikan
- Posisi yang dilamar: {job_title} di {company_name}
- Deskripsi pekerjaan sudah diberikan

Aturan:
1. Tanyakan SATU pertanyaan interview pada satu waktu
2. Setelah kandidat menjawab, berikan feedback singkat dan lanjut pertanyaan berikutnya
3. Campurkan pertanyaan behavioral, technical, dan situational
4. Bersikap profesional tapi ramah
5. Gunakan Bahasa Indonesia (kecuali posisi mengharuskan Bahasa Inggris)
6. Setelah 5-7 pertanyaan, akhiri interview dan berikan ringkasan feedback

Format jawaban:
- Jika ini pertanyaan baru: langsung tanyakan pertanyaannya
- Jika sedang memberi feedback: berikan feedback singkat lalu pertanyaan selanjutnya
- Jika interview selesai: berikan summary dengan format:

## 📋 Ringkasan Interview
### Skor Keseluruhan: [X]/10
### Kelebihan:
- [point]
### Area Perbaikan:
- [point]
### Tips:
- [tip]"""


def start_interview(cv_text: str, job_info: dict) -> dict:
    """
    Start a mock interview session.

    Args:
        cv_text: User's CV content
        job_info: dict with job_title, company_name, job_description

    Returns dict with:
    - "response": AI's first question
    - "available": whether OpenAI is configured
    """
    if not config.is_gemini_configured():
        return {"response": None, "available": False}

    try:
        client = config.get_gemini_client()
        from google.genai import types
        system_prompt = INTERVIEWER_PROMPT.format(
            job_title=job_info.get("job_title", "Unknown Position"),
            company_name=job_info.get("company_name", "Unknown Company"),
        )
        prompt = f"""[INFO INTERVIEW]
CV Kandidat:
{cv_text[:3000]}

Deskripsi Pekerjaan:
{job_info.get('job_description', 'N/A')[:2000]}

Mulai interview sekarang. Perkenalkan diri kamu sebagai HR dan mulai dengan pertanyaan pertama."""

        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )
        return {
            "response": response.text,
            "available": True,
        }
    except Exception as e:
        return {"response": f"Error: {str(e)}", "available": True}


def continue_interview(
    cv_text: str,
    job_info: dict,
    interview_history: list[dict],
    user_answer: str,
) -> dict:
    """
    Continue the mock interview with user's answer.

    Args:
        cv_text: User's CV content
        job_info: Job information dict
        interview_history: Previous Q&A messages
        user_answer: User's answer to the current question

    Returns dict with:
    - "response": AI's feedback + next question (or summary if interview is done)
    - "available": whether OpenAI is configured
    """
    if not config.is_gemini_configured():
        return {"response": None, "available": False}

    try:
        client = config.get_gemini_client()
        from google.genai import types
        system_prompt = INTERVIEWER_PROMPT.format(
            job_title=job_info.get("job_title", "Unknown Position"),
            company_name=job_info.get("company_name", "Unknown Company"),
        )

        contents = []
        contents.append({"role": "user", "parts": [{"text": f"[KONTEKS]\nCV: {cv_text[:2000]}\nJob: {job_info.get('job_description', '')[:1000]}"}]})
        contents.append({"role": "model", "parts": [{"text": "Baik, saya sudah memahami profil kandidat dan posisi yang dilamar. Mari kita mulai interview."}]})

        for msg in interview_history:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        user_count = sum(1 for m in interview_history if m["role"] == "user")
        prompt = user_answer
        if user_count >= 5:
            prompt = user_answer + "\n\n[SYSTEM]: Interview sudah cukup panjang. Berikan feedback terakhir dan RINGKASAN INTERVIEW dengan skor keseluruhan."
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )
        return {
            "response": response.text,
            "available": True,
        }
    except Exception as e:
        return {"response": f"Error: {str(e)}", "available": True}


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribe audio to text.
    Note: Replaced OpenAI Whisper with a stub because Gemini API standard SDK doesn't support audio byte streaming to text directly without file upload API.
    """
    return "[Audio transcription is currently not available with Gemini API. Please use text chat.]"


def text_to_speech(text: str) -> bytes:
    """
    Convert text to speech.
    Note: Replaced OpenAI TTS with a stub because Gemini API does not natively support TTS.
    """
    return b""
