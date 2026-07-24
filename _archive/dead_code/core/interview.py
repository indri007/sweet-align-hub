from dataclasses import dataclass
from typing import Optional
from .models import JobPosting, InterviewStage
import json

# === FONDASI HRD 16 TAHUN (Sesuai Spesifikasi) ===
HRD_PERSONA_SYSTEM_PROMPT = """
Kamu adalah Senior HR & Technical Recruiter dengan 16 tahun pengalaman. 
Berikut adalah fondasi profesionalmu:

1. Technical Literacy: Kamu cukup paham teknologi untuk mendeteksi jawaban asal vs masuk akal, tapi kamu bukan expert coder. 
2. STAR Method: Ini kerangka evaluasi utamamu. Jika kandidat hanya menjelaskan Situation & Task tanpa Action & Result yang jelas, kamu HARUS melakukan probing (bertanya lebih dalam).
3. Kompetensi ≠ Culture fit: Kamu memisahkan penilaian skill dari kecocokan budaya.
4. Bias awareness: Kamu menghindari "halo effect" dan "similarity bias" secara ketat.
5. Legal boundary: Kamu tahu pertanyaan ilegal (SARA, status pernikahan) dan tidak pernah menanyakannya.

ATURAN INTERVIEW 6 TAHAP & FOKUSNYA:
- SCREENING: Fokus ke Motivasi & kesesuaian dasar. Red Flag: Jawaban generik/copas dari job desc.
- ROLE_SPECIFIC: Fokus ke Proyek kompleks, keputusan teknis. Red Flag: Nyebut teknologi tanpa reasoning.
- BEHAVIORAL_STAR: Fokus ke Konflik, kegagalan, kerja tim. Red Flag: Blaming orang lain, no ownership.
- CURVEBALL_STRESS: Fokus ke Skenario tekanan (deadline, bug kritis). Red Flag: Panik, gak komunikasi risiko ke tim.
- SALARY_NEGOTIATION: Fokus ke Ekspektasi gaji + reasoning. Red Flag: Terlalu vague, gak riset market rate.
- CLOSING: Fokus ke Pertanyaan balik ke interviewer, next step. Red Flag: Gak ada pertanyaan sama sekali = minat rendah.

PRINSIP FEEDBACK YANG BENAR (Setiap selesai evaluasi tahap):
1. Selalu breakdown per komponen STAR.
2. Berikan 1 hal spesifik yang perlu diperbaiki + CONTOH cara jawab yang lebih baik.
3. JANGAN overclaim (misal: "kamu pasti gagal interview beneran"). Framing harus sebagai "insight latihan".
"""

@dataclass
class InterviewTurnResult:
    stage: InterviewStage
    question: str
    user_answer: str
    star_compliance_score: float
    feedback: str
    red_flags_detected: list[str]

class MockInterviewEngine:
    """
    Mesin Interview 6-Tahap Berbasis OOP.
    Terintegrasi dengan Gemini untuk probing dinamis dan evaluasi STAR.
    """
    def __init__(self, gemini_client, tts_engine=None):
        self.gemini_client = gemini_client
        self.tts_engine = tts_engine 

    def generate_question(self, stage: InterviewStage, job: JobPosting) -> str:
        red_flags = job.semiotic_tags.get("red_flags", []) if job.semiotic_tags else []
        flags_text = f"Perhatikan red flags ini dari semiotik lowongan: {', '.join(red_flags)}" if red_flags else ""
        
        prompt = f"{HRD_PERSONA_SYSTEM_PROMPT}\n\n"
        prompt += f"Konteks Pekerjaan:\nTitle: {job.title}\n{flags_text}\n\n"
        prompt += f"Sekarang kita berada di tahap: {stage.value.upper()}.\n"
        prompt += "Buat SATU pertanyaan interview yang tajam dan natural dalam Bahasa Indonesia sesuai fokus tahap ini. JANGAN berikan pengantar atau sapaan HRD, langsung ketik pertanyaannya."
        
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"[InterviewEngine] Error generate question: {e}")
            return "Silakan ceritakan pengalaman tersulit yang pernah Anda hadapi terkait posisi ini."

    def evaluate_answer(
        self, stage: InterviewStage, question: str, user_answer: str
    ) -> InterviewTurnResult:
        prompt = f"{HRD_PERSONA_SYSTEM_PROMPT}\n\n"
        prompt += f"Pertanyaan (Tahap {stage.value}): {question}\n"
        prompt += f"Jawaban Kandidat: {user_answer}\n\n"
        prompt += """Evaluasi jawaban ini menggunakan JSON schema yang VALID (tanpa teks apapun di luarnya). 
Ikuti Prinsip Feedback (Breakdown STAR, 1 perbaikan spesifik + contoh perbaikan).
Schema:
{ 
  "star_compliance_score": float (0-100), 
  "feedback": "string (Feedback berbasis STAR, 1 saran spesifik, + contoh jawaban baik)", 
  "red_flags_detected": ["list indikasi buruk seperti yang didefinisikan di fokus tahap"] 
}"""
        
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
                
            data = json.loads(raw_text.strip())
            
            return InterviewTurnResult(
                stage=stage,
                question=question,
                user_answer=user_answer,
                star_compliance_score=float(data.get("star_compliance_score", 50.0)),
                feedback=data.get("feedback", "Jawaban cukup baik namun pastikan komponen Action dan Result lebih jelas terukur."),
                red_flags_detected=data.get("red_flags_detected", [])
            )
        except Exception as e:
            print(f"[InterviewEngine] JSON Parsing Error: {e}")
            return InterviewTurnResult(
                stage=stage,
                question=question,
                user_answer=user_answer,
                star_compliance_score=50.0,
                feedback="Sistem AI mengalami kendala saat mengevaluasi kedalaman STAR Anda. Latih terus teknik memberikan 'Action' dan 'Result' yang konkret.",
                red_flags_detected=[]
            )

    def text_to_speech(self, text: str) -> Optional[bytes]:
        if not self.tts_engine:
            return None
        try:
            import io
            fp = io.BytesIO()
            tts = self.tts_engine(text=text, lang='id', slow=False)
            tts.write_to_fp(fp)
            return fp.getvalue()
        except Exception as e:
            print(f"[MockInterviewEngine] TTS Error: {e}")
            return None

    def generate_scorecard(self, turns: list[InterviewTurnResult]) -> dict:
        if not turns:
            return {"total_score": 0, "improvements": []}
            
        avg_star = sum(t.star_compliance_score for t in turns) / len(turns)
        all_flags = []
        for t in turns:
            all_flags.extend(t.red_flags_detected)
            
        return {
            "overall_star_compliance": round(avg_star, 2),
            "red_flags_count": len(all_flags),
            "critical_flags": list(set(all_flags)),
            "actionable_feedback": "Fokus pada menceritakan 'Action' dan 'Result' yang terukur dengan angka pada wawancara berikutnya." if avg_star < 70 else "Pertahankan struktur jawaban ini, tingkatkan metrik impact."
        }
