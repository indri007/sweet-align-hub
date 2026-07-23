import json
from typing import Optional

import agents.interview_agent_questions as iq
import agents.interview_agent_state as ist


def _default_chat_completion(messages, temperature, max_tokens):
    """
    Lazy import supaya modul ini tetap bisa di-import/dites tanpa llm_client
    tersedia.
    """
    from llm_client import chat_completion

    return chat_completion(messages=messages, temperature=temperature, max_tokens=max_tokens)


# ---------------------------------------------------------------------------
# Wiring LLM untuk dua keputusan sempit Agen 5 (bukan generator soal bebas)
# ---------------------------------------------------------------------------

def llm_is_answer_sufficient(jawaban: str, pertanyaan_aktif: str, chat_completion_fn=_default_chat_completion) -> bool:
    """
    Minta LLM menilai jawaban kandidat pada DUA dimensi terpisah:
      1. relevan -- apakah jawaban benar-benar menjawab pertanyaan yang
         diajukan.
      2. lengkap -- apakah struktur STAR-nya cukup detail.
    """
    system_prompt = (
        "Anda menilai jawaban kandidat wawancara kerja pada DUA dimensi terpisah:\n"
        "1. relevan: apakah jawaban ini benar-benar menjawab PERTANYAAN yang "
        "diajukan (bukan topik lain yang tidak berhubungan)?\n"
        "2. lengkap: apakah jawaban ini cukup detail secara struktur STAR "
        "(Situation/Task/Action/Result)?\n"
        "Tugas Anda HANYA menilai, bukan menjawab atau mengomentari isi jawaban.\n"
        "Balas HANYA dalam format JSON dengan alasan MAKSIMAL 10 KATA: "
        "{\"relevan\": true/false, \"lengkap\": true/false, \"alasan\": \"...\"}\n\n"
        f"Pertanyaan yang diajukan: {pertanyaan_aktif}\n"
    )
    try:
        raw = chat_completion_fn(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Jawaban kandidat: {jawaban}"}
            ],
            temperature=0.0,
            max_tokens=250,
        )
        parsed = _parse_json_response(raw)
        if parsed is None or "relevan" not in parsed or "lengkap" not in parsed:
            raise ValueError(f"LLM tidak merespons dalam format JSON yang valid. Raw: {raw!r}")

        relevan = bool(parsed["relevan"])
        lengkap = bool(parsed["lengkap"])
        if not relevan:
            print(f"[INFO] Jawaban dinilai TIDAK relevan terhadap pertanyaan aktif -- alasan: {parsed.get('alasan')!r}")
        return relevan and lengkap
    except Exception as e:
        # Bubble up exception to UI so state is not mutated
        raise RuntimeError(f"API Error saat mengevaluasi jawaban: {e}")


def llm_generate_followup(system_prompt: str, chat_completion_fn=_default_chat_completion) -> str:
    """
    Panggil LLM (Agen 5) dengan system prompt dari build_agent5_system_prompt()
    """
    try:
        text = chat_completion_fn(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Tolong berikan SATU pertanyaan follow-up untuk jawaban saya."}
            ],
            temperature=0.7,
            max_tokens=200,
        )
        return text.strip()
    except Exception as e:
        raise RuntimeError(f"API Error saat generate follow-up: {e}")


FALLBACK_FOLLOWUP_TEXT = "Bisa diceritakan lebih detail lagi tentang situasi tersebut?"


def llm_generate_followup_validated(
    system_prompt: str,
    pertanyaan_aktif: str,
    chat_completion_fn=_default_chat_completion,
) -> str:
    """
    Guardrail atas llm_generate_followup(): jangan tampilkan output LLM
    mentah-mentah ke kandidat kalau kelihatan rusak/kosong/halusinasi keluar
    peran.
    """
    text = llm_generate_followup(system_prompt, chat_completion_fn)

    is_broken = (
        not text
        or len(text) < 10
        or any(artefak in text for artefak in ("{", "}", "```"))
        or text.strip().lower() == pertanyaan_aktif.strip().lower()
    )
    if is_broken:
        print(f"[WARNING] Follow-up dari LLM terdeteksi cacat/echo, raw={text!r} -- fallback ke teks aman.")
        return FALLBACK_FOLLOWUP_TEXT
    return text


def _parse_json_response(raw: str) -> Optional[dict]:
    """Toleran terhadap LLM yang membungkus JSON dengan ```json fences."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).replace("json", "", 1)
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# API publik yang dipanggil dari Streamlit app
# ---------------------------------------------------------------------------

def start_interview(cv_text: str, job_info: dict, qdrant_client=None) -> ist.InterviewSession:
    job_title = job_info.get("job_title", "Umum")
    session = ist.start_interview(
        posisi=job_title,
        jumlah_kompetensi=4,
        get_questions_fn=iq.get_interview_questions,
        client=qdrant_client,
    )
    return session


def get_active_question(session: ist.InterviewSession) -> str:
    return session.turns[-1].pertanyaan


def handle_candidate_answer(
    session: ist.InterviewSession,
    jawaban_user: str,
    chat_completion_fn=_default_chat_completion,
) -> Optional[str]:
    pertanyaan_aktif = session.turns[-1].pertanyaan
    return ist.record_answer_and_get_next(
        session,
        jawaban_user,
        is_answer_sufficient_fn=lambda j: llm_is_answer_sufficient(j, pertanyaan_aktif, chat_completion_fn),
        generate_followup_fn=lambda p: llm_generate_followup_validated(p, pertanyaan_aktif, chat_completion_fn),
    )


def evaluate_interview(
    session: ist.InterviewSession,
    chat_completion_fn=_default_chat_completion,
) -> dict:
    if not session.completed:
        raise ValueError("Wawancara belum selesai. Evaluasi hanya dapat dilakukan di akhir sesi.")
    
    transcript = f"Posisi: {session.posisi}\n\n"
    for t in session.turns:
        tipe_q = "Pertanyaan (Follow-up)" if t.is_followup else f"Pertanyaan ({t.tahap} - {t.kompetensi})"
        transcript += f"{tipe_q}: {t.pertanyaan}\n"
        transcript += f"Jawaban Kandidat: {t.jawaban or '(Tidak ada jawaban)'}\n\n"
        
    system_prompt = (
        "Anda adalah Agen 6 (Scoring Evaluator) untuk wawancara kerja.\n"
        "Tugas Anda mengevaluasi kandidat berdasarkan keseluruhan transkrip sesi wawancara berbasis kompetensi STAR (Situation, Task, Action, Result).\n"
        "Berikan penilaian kualitatif (PILIH TEPAT SATU dari 3 opsi berikut, JANGAN gunakan variasi lain: 'Kurang', 'Cukup', atau 'Baik') untuk setiap kompetensi yang diujikan, beserta feedback singkat (maksimal 30 kata per kompetensi).\n"
        "Balas HANYA dalam format JSON dengan skema berikut:\n"
        "{\n"
        '  "evaluasi": [\n'
        '    {"kompetensi": "Nama Kompetensi", "label": "Baik", "feedback": "..."}\n'
        "  ],\n"
        '  "kesimpulan_umum": "Ringkasan singkat performa kandidat secara keseluruhan (maks 50 kata)."\n'
        "}\n\n"
        f"Berikut adalah transkrip wawancaranya:\n{transcript}"
    )

    try:
        raw = chat_completion_fn(
            messages=[{"role": "user", "content": system_prompt}],
            temperature=0.2,
            max_tokens=1500,
        )
        parsed = _parse_json_response(raw)
        if parsed is None or "evaluasi" not in parsed:
            raise ValueError(f"LLM tidak merespons JSON valid. Raw: {raw!r}")
            
        # Validasi label ketat
        valid_labels = {"Kurang", "Cukup", "Baik"}
        for item in parsed["evaluasi"]:
            label = item.get("label")
            if label not in valid_labels:
                raise ValueError(f"LLM mengembalikan label yang tidak valid: {label!r}. Harus salah satu dari {valid_labels}")
        
        # Simpan ke state
        session.evaluation_result = parsed
        return parsed
    except Exception as e:
        raise RuntimeError(f"API Error saat evaluasi akhir: {e}")


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
    return "[Fitur transkripsi suara dinonaktifkan]"

def text_to_speech(text: str) -> bytes:
    return b""
