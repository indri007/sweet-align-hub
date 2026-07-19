"""
Mock Interview Agent — Simulates HR interview with AI.
Text-based interview via Gemini/OpenAI. Voice mode (Whisper/TTS) is disabled
since it requires an OpenAI key specifically and is not used in this deployment.
"""

import config
from llm_client import chat_completion


INTERVIEWER_PROMPT = """Kamu adalah Veronica, seorang HR Interviewer profesional dan berpengalaman di perusahaan besar Indonesia. 
Kamu sedang melakukan sesi "Mock Interview" dengan seorang kandidat.

Konteks (Knowledge yang kamu miliki):
- Teks CV Kandidat lengkap
- Posisi yang dilamar: {job_title} di {company_name}
- Deskripsi pekerjaan (Job Description) lengkap dari posisi tersebut

Aturan Wawancara:
1. Perkenalkan diri kamu dengan nama Veronica secara singkat di awal.
2. Tanyakan SATU pertanyaan interview pada satu waktu.
3. Setelah kandidat menjawab, berikan feedback singkat dan apresiasi, lalu lanjut ke pertanyaan berikutnya.
4. Campurkan pertanyaan behavioral, technical, dan situational yang sangat relevan dengan Job Description.
5. Bersikap profesional, elegan, namun tetap ramah.
6. Gunakan Bahasa Indonesia (kecuali kandidat menggunakan Bahasa Inggris atau posisi mengharuskan Bahasa Inggris).
7. Setelah 5 pertanyaan (atau jika kandidat ingin menyudahi), akhiri interview dan berikan ringkasan evaluasi.

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
    - "available": whether an LLM provider or N8N is configured
    """
    # Try N8N first
    if config.is_n8n_configured():
        try:
            from n8n_client import start_interview_n8n
            ai_text = start_interview_n8n(cv_text, job_info)
            if ai_text and not ai_text.startswith("Error") and not ai_text.startswith("Tidak dapat") and not ai_text.startswith("N8N"):
                return {"response": ai_text, "available": True}
        except Exception:
            pass

    if not config.is_llm_configured():
        return {"response": None, "available": False}

    try:
        # RAG: Fetch HR Knowledge and Memory from Qdrant
        from vector_store import VectorStoreManager
        hr_store = VectorStoreManager(collection_name=config.HR_KNOWLEDGE_COLLECTION)
        hr_memory = VectorStoreManager(collection_name=config.HR_MEMORY_COLLECTION)
        
        search_query = f"{job_info.get('job_title', '')} {job_info.get('company_name', '')}"
        
        hr_knowledge_chunks = hr_store.search_similar_jobs(search_query, top_k=3)
        hr_memory_chunks = hr_memory.search_similar_jobs(search_query, top_k=2)
        
        hr_context = "\n".join([chunk["document"] for chunk in hr_knowledge_chunks]) if hr_knowledge_chunks else "Tidak ada instruksi spesifik. Gunakan penilaian standar HR."
        memory_context = "\n".join([chunk["document"] for chunk in hr_memory_chunks]) if hr_memory_chunks else "Tidak ada kenangan masa lalu untuk peran ini."

        system_prompt = INTERVIEWER_PROMPT.format(
            job_title=job_info.get("job_title", "Unknown Position"),
            company_name=job_info.get("company_name", "Unknown Company"),
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""[INFO INTERVIEW]
CV Kandidat:
{cv_text[:3000]}

Deskripsi Pekerjaan:
{job_info.get('job_description', 'N/A')[:2000]}

[PANDUAN HR KHUSUS (RAG)]:
{hr_context}

[KENANGAN WAWANCARA SEBELUMNYA]:
{memory_context}

Mulai interview sekarang. Perkenalkan diri kamu sebagai HR dan mulai dengan pertanyaan pertama.""",
            },
        ]

        reply = chat_completion(messages=messages, temperature=0.7, max_tokens=800)

        return {
            "response": reply,
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
    - "available": whether an LLM provider or N8N is configured
    """
    # Try N8N first
    if config.is_n8n_configured():
        try:
            from n8n_client import continue_interview_n8n
            ai_text = continue_interview_n8n(cv_text, job_info, interview_history, user_answer)
            if ai_text and not ai_text.startswith("Error") and not ai_text.startswith("Tidak dapat") and not ai_text.startswith("N8N"):
                return {"response": ai_text, "available": True}
        except Exception:
            pass

    if not config.is_llm_configured():
        return {"response": None, "available": False}

    try:
        # RAG: Fetch HR Knowledge and Memory from Qdrant
        from vector_store import VectorStoreManager
        hr_store = VectorStoreManager(collection_name=config.HR_KNOWLEDGE_COLLECTION)
        hr_memory = VectorStoreManager(collection_name=config.HR_MEMORY_COLLECTION)
        
        search_query = f"{job_info.get('job_title', '')} {job_info.get('company_name', '')}"
        
        hr_knowledge_chunks = hr_store.search_similar_jobs(search_query, top_k=3)
        hr_memory_chunks = hr_memory.search_similar_jobs(search_query, top_k=2)
        
        hr_context = "\n".join([chunk["document"] for chunk in hr_knowledge_chunks]) if hr_knowledge_chunks else "Tidak ada instruksi spesifik."
        memory_context = "\n".join([chunk["document"] for chunk in hr_memory_chunks]) if hr_memory_chunks else "Tidak ada kenangan masa lalu."

        system_prompt = INTERVIEWER_PROMPT.format(
            job_title=job_info.get("job_title", "Unknown Position"),
            company_name=job_info.get("company_name", "Unknown Company"),
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"[KONTEKS]\nCV: {cv_text[:2000]}\nJob: {job_info.get('job_description', '')[:1000]}\n\n[PANDUAN HR KHUSUS (RAG)]:\n{hr_context}\n\n[KENANGAN WAWANCARA SEBELUMNYA]:\n{memory_context}",
            },
            {
                "role": "assistant",
                "content": "Baik, saya sudah memahami profil kandidat dan posisi yang dilamar. Mari kita mulai interview.",
            },
        ]

        # Add interview history
        for msg in interview_history:
            messages.append(msg)

        # Add current answer
        messages.append({"role": "user", "content": user_answer})

        # Check if we should end the interview (after 5+ exchanges)
        user_count = sum(1 for m in interview_history if m["role"] == "user")
        if user_count >= 5:
            messages.append({
                "role": "system",
                "content": "Interview sudah cukup panjang. Berikan feedback terakhir dan RINGKASAN INTERVIEW dengan skor keseluruhan.",
            })

        reply = chat_completion(messages=messages, temperature=0.7, max_tokens=1200)

        # Kafka Pilar 1: Siaran Wawancara (Interview Streaming)
        try:
            from kafka_producer import send_kafka_message
            import time
            stream_data = {
                "kandidat_id": cv_text[:50].replace('\n', ' '), # Just a snippet for id
                "job_title": job_info.get("job_title", "Unknown"),
                "tanya_user": user_answer,
                "jawab_veronica": reply,
                "timestamp": int(time.time())
            }
            send_kafka_message("interview_streams", stream_data)
        except ImportError:
            pass

        # Fire-and-forget thread to save memory
        import threading
        import uuid
        def _save_memory():
            try:
                interaction = f"Posisi: {job_info.get('job_title', 'Unknown')}\nKandidat menjawab: {user_answer}\nVeronica HR merespons: {reply}"
                hr_memory.add_documents(
                    documents=[interaction],
                    metadatas=[{"source": "hr_interview_history"}],
                    ids=[str(uuid.uuid4())]
                )
            except Exception as e:
                print(f"[Memory] Gagal menyimpan kenangan Veronica: {e}")
        threading.Thread(target=_save_memory, daemon=True).start()

        return {
            "response": reply,
            "available": True,
        }
    except Exception as e:
        return {"response": f"Error: {str(e)}", "available": True}


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Voice transcription is disabled in this deployment (requires OpenAI Whisper,
    not part of the Gemini setup). Kept as a stub so app.py doesn't break if it
    still references this function.
    """
    return "[Fitur transkripsi suara dinonaktifkan]"


def text_to_speech(text: str) -> bytes:
    """
    Voice output (TTS) is disabled in this deployment (requires OpenAI TTS,
    not part of the Gemini setup). Kept as a stub so app.py doesn't break if it
    still references this function.
    """
    return b""
