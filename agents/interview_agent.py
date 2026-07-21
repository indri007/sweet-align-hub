"""
Mock Interview Agent — Simulates HR interview with AI.
Text-based interview via Gemini/OpenAI. Voice mode (Whisper/TTS) is disabled
since it requires an OpenAI key specifically and is not used in this deployment.
"""

import config
from llm_client import chat_completion


INTERVIEWER_PROMPT = """Kamu adalah Leonardo, seorang HR Interviewer profesional dan berpengalaman di perusahaan besar Indonesia. 
Kamu sedang melakukan sesi "Mock Interview" dengan seorang kandidat menggunakan metode STAR (Situation, Task/Action, Result).

Konteks (Knowledge yang kamu miliki):
- Teks CV Kandidat lengkap
- Posisi yang dilamar: {job_title} di {company_name}
- Deskripsi pekerjaan (Job Description) lengkap dari posisi tersebut

Aturan Wawancara (Metode STAR):
1. Perkenalkan diri kamu dengan nama Leonardo secara singkat di awal.
2. Tanyakan SATU pertanyaan interview pada satu waktu. Fokus pada kompetensi seperti Kerjasama, Inisiatif, Leadership, Negosiasi, atau Komunikasi.
3. Gunakan alur STAR:
   - Pembuka: "Harap uraikan contoh kejadian dimana Anda..."
   - Situation: "Uraikan konteksnya: kapan, siapa yang terlibat, apa tugas Anda?"
   - Action: "Tindakan detil apa yang Anda lakukan saat itu?"
   - Result: "Apa hasil akhirnya?"
4. Setelah kandidat menjawab satu fase, pancing ke fase STAR berikutnya secara elegan.
5. Bersikap profesional, elegan, namun tetap ramah. Gunakan Bahasa Indonesia (kecuali kandidat memakai Bahasa Inggris).
6. Setelah 5-7 pertanyaan (atau jika kandidat ingin menyudahi), akhiri interview dan berikan ringkasan evaluasi.

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

[PELAJARAN DARI WAWANCARA KANDIDAT SEBELUMNYA]:
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
                "content": f"[KONTEKS]\nCV: {cv_text[:2000]}\nJob: {job_info.get('job_description', '')[:1000]}\n\n[PANDUAN HR KHUSUS (RAG)]:\n{hr_context}\n\n[PELAJARAN DARI WAWANCARA KANDIDAT SEBELUMNYA]:\n{memory_context}",
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

        # Hermes Memory: Trigger reflection if interview is ending
        if user_count >= 5:
            full_history = interview_history + [
                {"role": "user", "content": user_answer}, 
                {"role": "assistant", "content": reply}
            ]
            _reflect_and_save_memory(job_info, full_history, hr_memory)

        return {
            "response": reply,
            "available": True,
        }
    except Exception as e:
        return {"response": f"Error: {str(e)}", "available": True}


def _reflect_and_save_memory(job_info: dict, interview_history: list[dict], hr_memory):
    """
    Hermes Agentic Memory: Distills the interview into semantic insights and saves to Qdrant.
    """
    import threading
    import uuid
    from llm_client import chat_completion
    
    def _run_reflection():
        try:
            job_title = job_info.get('job_title', 'Unknown')
            company_name = job_info.get('company_name', 'Unknown')
            
            transcript = ""
            for msg in interview_history:
                role = "Leonardo" if msg["role"] == "assistant" else "Kandidat"
                transcript += f"{role}: {msg['content']}\n\n"
            
            prompt = f"""Kamu adalah agen Refleksi HR (Hermes Memory).
Tugasmu adalah menganalisis transkrip wawancara berikut dan mengekstrak wawasan (insight) penting yang bisa digunakan Leonardo untuk wawancara kandidat berikutnya pada posisi yang sama.
Jangan merangkum isi percakapan. Fokus pada: 
1. Apa kelemahan umum atau titik buta (blind spot) kandidat ini yang mungkin dimiliki kandidat lain?
2. Strategi bertanya apa yang terbukti efektif di wawancara ini?
3. Rekomendasi 1-2 kalimat untuk Leonardo di masa depan.

Posisi: {job_title} di {company_name}
Transkrip Wawancara:
{transcript[:5000]}

Output harus singkat, padat, dan langsung menjadi instruksi bagi Leonardo."""
            
            reflection = chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=300
            )
            
            hr_memory.add_documents(
                documents=[f"Posisi: {job_title}\nInsight Refleksi: {reflection}"],
                metadatas=[{"source": "hermes_reflection", "job_title": job_title}],
                ids=[str(uuid.uuid4())]
            )
        except Exception as e:
            print(f"[Hermes Memory] Gagal melakukan refleksi: {e}")
            
    threading.Thread(target=_run_reflection, daemon=True).start()


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribe audio bytes to text using OpenAI Whisper.
    """
    import config
    if not config.is_openai_configured():
        return "[Fitur suara dinonaktifkan karena OPENAI_API_KEY tidak dikonfigurasi.]"
    
    from openai import OpenAI
    import tempfile
    import os

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    # OpenAI whisper SDK requires a file-like object with a filename ending in a supported format
    # Because audio_bytes comes from the browser, we'll write it to a temp file
    try:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return transcription.text
    except Exception as e:
        return f"[Gagal mentranskripsi suara: {str(e)}]"
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)


def text_to_speech(text: str) -> bytes:
    """
    Convert text to speech audio bytes using OpenAI TTS-1 with Nova voice.
    """
    import config
    if not config.is_openai_configured():
        return b""
        
    from openai import OpenAI
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    # Remove markdown formatting for cleaner speech
    clean_text = text.replace("#", "").replace("*", "").strip()
    
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=clean_text
        )
        return response.content
    except Exception as e:
        print(f"[TTS Error] {str(e)}")
        return b""
