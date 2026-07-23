# Walkthrough: FR-16 (Agen 6 - Evaluator Scoring)

Fase FR-16 telah selesai diimplementasikan. Berikut adalah ringkasan perubahan dan hasil validasinya.

## Perubahan yang Dilakukan

1. **Agen 6 LLM Logic (`agents/interview_agent.py`)**
   - Menambahkan fungsi `evaluate_interview(session)` yang merangkai seluruh `session.turns` menjadi satu transkrip wawancara lengkap.
   - Menggunakan *System Prompt* khusus yang menginstruksikan Agen 6 untuk mengevaluasi jawaban menggunakan metodologi STAR.
   - Memaksa *output* dalam bentuk JSON terstruktur yang berisi skor (skala 1-5), *feedback* per kompetensi, dan kesimpulan umum.
   - Hasil evaluasi disimpan dengan aman ke `session.evaluation_result`.

2. **State Management (`agents/interview_agent_state.py`)**
   - Menambahkan *field* `evaluation_result: Optional[dict]` pada *dataclass* `InterviewSession` agar skor akhir dapat disimpan dan nantinya digunakan untuk FR-17.
   - Menyesuaikan `get_transcript_for_storage()` agar ikut mem-nge-ekstrak `evaluation_result`.

3. **Integrasi UI (`pages/step_e_interview.py`)**
   - Ketika wawancara mencapai akhir (`next_q` = None), UI akan menampilkan status pemuatan: `"🎉 Wawancara selesai! Sedang menyusun laporan evaluasi..."`
   - Memanggil `evaluate_interview` dan langsung merender hasilnya dalam format Markdown yang rapi ke riwayat *chat*.
   - Menggunakan *error handling* (`try/except`) agar *crash* pada API (misalnya *rate limit*) tidak membuat UI macet.

## Hasil Validasi

Telah dibuat dan dijalankan *script* `scripts/test_llm_quality_fr16.py` yang menyimulasikan sesi wawancara lengkap dengan dua kompetensi. 

**Skenario Mock:**
- **Kemampuan Analitis:** Kandidat memberikan jawaban STAR yang sangat detail dan berdampak tinggi.
- **Kerjasama Tim:** Kandidat memberikan jawaban yang sangat arogan dan tidak profesional ("Saya marahi saja biar dia sadar diri").

**Hasil Evaluator LLM (Lolos Uji):**
```json
{
  "evaluasi": [
    {
      "kompetensi": "Kemampuan Analitis",
      "skor": 5,
      "feedback": "Kandidat menunjukkan kemampuan analitis dan pemecahan masalah teknis yang sangat baik menggunakan Python Pandas, menghasilkan efisiensi tinggi serta solusi yang dijadikan SOP perusahaan."
    },
    {
      "kompetensi": "Kerjasama Tim",
      "skor": 1,
      "feedback": "Kandidat menunjukkan keterampilan interpersonal dan resolusi konflik yang sangat buruk. Cara menangani rekan kerja tidak profesional dan konfrontatif tanpa pendekatan kolaboratif."
    }
  ],
  "kesimpulan_umum": "Kandidat memiliki kemampuan teknis dan analitis yang sangat unggul dengan dampak terukur. Namun, kandidat memiliki kelemahan kritis pada keterampilan interpersonal dan komunikasi tim yang sangat tidak profesional."
}
```

Seperti yang terlihat, Agen 6 mampu memberikan skor absolut (**5** untuk jawaban yang sempurna, dan **1** untuk jawaban yang buruk) dengan *feedback* yang tajam dan masuk akal.

> [!TIP]
> Fitur ini siap diuji langsung di UI Streamlit! Lakukan satu wawancara penuh untuk melihat skor akhir Anda.
