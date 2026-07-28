"""
interview_agent.py — FR-15: state tracking & percabangan Agen 5 (HRD Interviewer)
==================================================================================
Menutup FR-15 (PRD JobMatch AI v2, Bagian 7.5): "Alur wawancara bertahap
(multi-turn) yang dikelola melalui workflow n8n, termasuk logika percabangan
pertanyaan lanjutan berdasarkan jawaban pengguna sebelumnya."

Desain mengikuti persis pola Agen 5 di Dokumentasi_Scope_Batasan_Pengujian_
Chatbot_CS_HRD.md §8.5:
  - State tracking dikirim eksplisit tiap pemanggilan LLM (posisi, jumlah
    pertanyaan, daftar topik) -- karena LLM tidak menyimpan memori sendiri
    di luar konteks yang dikirim.
  - Guardrail: agen TIDAK menilai benar/salah jawaban kandidat selama sesi
    berlangsung (itu tugas Agen 6/Evaluator -- FR-16, belum dikerjakan).
  - Tidak mengulang topik yang sudah dibahas kecuali untuk menggali lebih
    dalam (follow-up).

Bergantung pada get_interview_questions() dari interview_agent_questions.py
(FR-14) sebagai sumber soal kanonik per kompetensi/tahap STAR.

PENTING -- yang di luar tanggung jawab modul ini:
  - Fungsi ini TIDAK memanggil LLM secara langsung. Pengambilan keputusan
    "apakah jawaban cukup lengkap" dan "generate teks follow-up" di-inject
    lewat parameter fungsi (is_answer_sufficient_fn, generate_followup_fn)
    supaya bisa diuji tanpa API key sungguhan, dan supaya pemanggilan LLM
    yang sesungguhnya (Gemini/Groq) tetap satu tempat di caller, bukan
    tersembunyi di dalam modul ini.
  - Evaluasi akhir sesi (Agen 6, FR-16) dan penyimpanan transkrip ke Aiven
    (FR-17) TIDAK ada di sini -- lihat get_transcript_for_storage() sebagai
    titik integrasi untuk FR-17.
"""

import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional

STAGES = ["Situation", "Task", "Action", "Result"]
MAX_FOLLOWUP_PER_STAGE = 2  # guardrail -- cegah sesi berputar tanpa akhir di satu tahap


@dataclass
class InterviewTurn:
    kompetensi: str
    tahap: str
    pertanyaan: str
    jawaban: Optional[str] = None
    is_followup: bool = False


@dataclass
class InterviewSession:
    session_id: str
    posisi: str
    questions: list[dict]  # output get_interview_questions()
    turns: list[InterviewTurn] = field(default_factory=list)
    komp_index: int = 0
    stage_index: int = 0
    completed: bool = False
    evaluation_result: Optional[dict] = None


def default_is_answer_sufficient(jawaban: str) -> bool:
    """
    Heuristik fallback SANGAT sederhana (jumlah kata) -- BUKAN pengganti
    penilaian LLM sungguhan. Di produksi, ganti dengan is_answer_sufficient_fn
    yang memanggil LLM untuk menilai kelengkapan jawaban STAR (mis. apakah
    kandidat sudah menyebut Situation+Task+Action+Result dalam jawabannya).
    Dipertahankan sebagai default supaya modul ini tetap bisa jalan/dites
    tanpa API key, bukan sebagai rekomendasi kualitas penilaian.
    """
    return len(jawaban.split()) >= 15


def build_agent5_system_prompt(session: InterviewSession, jawaban_kandidat: Optional[str] = None) -> str:
    """
    System prompt untuk Agen 5, persis mengikuti template resmi di
    Dokumentasi_Scope_Batasan_Pengujian_Chatbot_CS_HRD.md §8.5.

    Args:
        jawaban_kandidat: jawaban kandidat untuk pertanyaan yang SEDANG diproses.
            WAJIB dikirim eksplisit saat dipanggil dari dalam
            record_answer_and_get_next() -- karena mutasi state (current.jawaban)
            sengaja DITUNDA sampai LLM call berhasil (lihat komentar "menunda
            mutasi state" di record_answer_and_get_next), jadi
            session.turns[-1].jawaban MASIH None persis di titik fungsi ini
            dipanggil. Tanpa parameter ini, LLM akan menerima "Jawaban kandidat: "
            kosong dan menghasilkan follow-up yang tidak nyambung dengan apa
            yang sebenarnya baru saja dijawab kandidat.
            Kalau None, fallback ke jawaban tersimpan di turn terakhir (dipakai
            untuk kasus lain di luar alur follow-up, mis. debugging/inspeksi).
    """
    turns_terjawab = [t for t in session.turns if t.jawaban is not None]
    jumlah_pertanyaan = len(turns_terjawab) + (1 if jawaban_kandidat is not None else 0)
    daftar_topik = sorted({t.kompetensi for t in session.turns})

    if jawaban_kandidat is None:
        jawaban_kandidat = session.turns[-1].jawaban if session.turns and session.turns[-1].jawaban else ""

    return (
        "Anda adalah Pak/Bu Arini, pewawancara HRD senior di sebuah perusahaan teknologi terkemuka di Indonesia.\n"
        "Anda dikenal ramah, hangat, dan profesional — bisa membuat kandidat merasa nyaman sambil tetap menggali\n"
        "informasi yang dibutuhkan secara mendalam.\n\n"
        f"Saat ini Anda sedang mewawancarai kandidat untuk posisi: **{session.posisi}**.\n"
        f"Progres wawancara: sudah {jumlah_pertanyaan} pertanyaan diajukan.\n"
        f"Topik yang sudah dibahas: {', '.join(daftar_topik) if daftar_topik else '(wawancara baru saja dimulai)'}.\n\n"
        "PANDUAN GAYA BICARA (WAJIB DIIKUTI):\n"
        "- Mulai dengan satu kalimat singkat yang mengakui/merespons jawaban kandidat (misal: 'Menarik sekali', "
        "'Terima kasih sudah berbagi', 'Saya paham situasinya') sebelum mengajukan pertanyaan selanjutnya.\n"
        "- Jika jawaban kandidat SANGAT singkat (<10 kata) atau tampak menghindari inti pertanyaan, "
        "dorong mereka dengan lembut: 'Boleh Anda ceritakan lebih konkret?' atau 'Bisa kasih contoh spesifiknya?'\n"
        "- Gunakan bahasa Indonesia yang natural dan bersahabat — bukan kaku seperti robot.\n"
        "- Jangan pernah menilai benar/salah jawaban kandidat selama sesi berlangsung.\n"
        "- Jangan mengulang pertanyaan yang PERSIS sama dengan yang sudah diajukan.\n\n"
        "Berdasarkan jawaban kandidat terbaru di bawah, ajukan SATU pertanyaan lanjutan yang relevan "
        "dan menggali lebih dalam:\n\n"
        f"Jawaban kandidat: {jawaban_kandidat}"
    )


def start_interview(
    posisi: str,
    jumlah_kompetensi: int = 4,
    get_questions_fn: Optional[Callable] = None,
    client=None,
) -> InterviewSession:
    """
    Mulai sesi baru: ambil bank soal (FR-14) dan siapkan pertanyaan pertama
    (tahap Situation, kompetensi pertama).
    """
    if get_questions_fn is None:
        from agents.interview_agent_questions import get_interview_questions as get_questions_fn

    questions = get_questions_fn(posisi, jumlah_kompetensi=jumlah_kompetensi, client=client)
    session = InterviewSession(session_id=str(uuid.uuid4()), posisi=posisi, questions=questions)

    first = questions[0]
    first_tahap = STAGES[0]
    session.turns.append(InterviewTurn(
        kompetensi=first["kompetensi"],
        tahap=first_tahap,
        pertanyaan=first["pertanyaan_star"][first_tahap],
    ))
    return session


def record_answer_and_get_next(
    session: InterviewSession,
    jawaban_kandidat: str,
    is_answer_sufficient_fn: Callable[[str], bool] = default_is_answer_sufficient,
    generate_followup_fn: Optional[Callable[[str], str]] = None,
) -> Optional[str]:
    """
    Catat jawaban kandidat untuk pertanyaan saat ini, lalu tentukan langkah
    berikutnya (logika percabangan FR-15):

      1. Kalau jawaban terdeteksi kurang lengkap DAN belum mencapai batas
         follow-up per tahap -> minta satu pertanyaan lanjutan (follow-up)
         lewat generate_followup_fn, dengan system prompt dari
         build_agent5_system_prompt().
      2. Kalau cukup lengkap, atau sudah mencapai batas follow-up (guardrail
         supaya tidak berputar tanpa akhir di satu tahap) -> maju ke tahap
         STAR berikutnya, atau ke kompetensi berikutnya kalau tahap Result
         sudah selesai.
      3. Kalau seluruh kompetensi terpilih sudah selesai -> session.completed
         = True, return None (sinyal ke caller: sesi siap diserahkan ke
         Agen 6/Evaluator -- FR-16).

    Returns:
        Teks pertanyaan berikutnya (follow-up atau tahap baru), atau None
        kalau sesi sudah selesai.
    """
    if session.completed:
        raise ValueError("Sesi sudah selesai (completed=True) -- tidak bisa menerima jawaban baru.")
    if not session.turns:
        raise ValueError("Sesi belum dimulai -- panggil start_interview() dulu.")

    current = session.turns[-1]
    if current.jawaban is not None:
        raise ValueError(
            "Pertanyaan saat ini sudah dijawab sebelumnya -- "
            "record_answer_and_get_next() hanya boleh dipanggil sekali per pertanyaan aktif."
        )

    # PENTING: jangan mutasi `current.jawaban` di sini. Kalau is_answer_sufficient_fn
    # gagal total (mis. RuntimeError -- Gemini 429 tanpa fallback), exception harus
    # tembus ke caller dengan state SEUTUHNYA belum berubah, supaya kandidat bisa
    # submit ulang tanpa kehilangan giliran ("turn terbakar"). jawaban_kandidat
    # dikirim langsung sebagai argumen, bukan dibaca dari state, sampai kita yakin
    # LLM call ini akan berhasil.
    followups_in_stage = sum(
        1 for t in session.turns
        if t.kompetensi == current.kompetensi and t.tahap == current.tahap and t.is_followup
    )

    perlu_followup = (
        not is_answer_sufficient_fn(jawaban_kandidat) and followups_in_stage < MAX_FOLLOWUP_PER_STAGE
    )

    if perlu_followup:
        if generate_followup_fn is None:
            raise ValueError(
                "Jawaban terdeteksi kurang lengkap tapi generate_followup_fn tidak "
                "disediakan. Di produksi ini harus memanggil LLM (Agen 5) dengan "
                "prompt dari build_agent5_system_prompt(session)."
            )
        # generate_followup_fn juga bisa gagal (RuntimeError) -- kalau begitu,
        # baris di bawah ini TIDAK tercapai, current.jawaban TETAP None.
        followup_text = generate_followup_fn(build_agent5_system_prompt(session, jawaban_kandidat))

        # Baru sampai sini kita YAKIN kedua panggilan LLM berhasil -- aman untuk
        # mutasi state sekarang.
        current.jawaban = jawaban_kandidat
        session.turns.append(InterviewTurn(
            kompetensi=current.kompetensi,
            tahap=current.tahap,
            pertanyaan=followup_text,
            is_followup=True,
        ))
        return followup_text

    # Kalau sampai sini: is_answer_sufficient_fn sudah berhasil dipanggil tanpa
    # exception (baik hasilnya True, atau False tapi guardrail sudah tercapai).
    # Aman untuk mutasi state sekarang.
    current.jawaban = jawaban_kandidat
    return _advance_to_next_question(session)


def _advance_to_next_question(session: InterviewSession) -> Optional[str]:
    session.stage_index += 1
    if session.stage_index >= len(STAGES):
        session.stage_index = 0
        session.komp_index += 1

    if session.komp_index >= len(session.questions):
        session.completed = True
        return None

    komp_data = session.questions[session.komp_index]
    tahap = STAGES[session.stage_index]
    pertanyaan = komp_data["pertanyaan_star"][tahap]
    session.turns.append(InterviewTurn(
        kompetensi=komp_data["kompetensi"],
        tahap=tahap,
        pertanyaan=pertanyaan,
    ))
    return pertanyaan


def get_transcript_for_storage(session: InterviewSession) -> dict:
    """
    Bentuk data siap simpan untuk FR-17 (transkrip ke tabel HRD_TRANSCRIPTS
    di Aiven) -- modul ini TIDAK melakukan penulisan ke database, hanya
    menyiapkan struktur datanya.
    """
    return {
        "session_id": session.session_id,
        "posisi": session.posisi,
        "completed": session.completed,
        "turns": [
            {
                "kompetensi": t.kompetensi,
                "tahap": t.tahap,
                "pertanyaan": t.pertanyaan,
                "jawaban": t.jawaban,
                "is_followup": t.is_followup,
            }
            for t in session.turns
        ],
        "evaluation_result": session.evaluation_result,
    }
