import json
from .models import JobPosting

SEMIOTIC_SYSTEM_PROMPT = """
Kamu adalah analis semiotik yang membaca job posting untuk menangkap makna
tersirat (konotasi), bukan cuma requirement eksplisit (denotasi).

Kerangka: pendekatan Barthesian (denotasi vs konotasi).
- Denotasi: requirement eksplisit yang tertulis jelas.
- Konotasi: sinyal budaya kerja tersirat dari pilihan diksi.

Output HARUS JSON valid, tanpa teks tambahan, dengan schema:
{
  "work_culture_signal": [string],
  "hidden_requirement": [string],
  "tone_formality": "formal-korporat" | "casual-startup" | "netral",
  "red_flags": [string]
}

Jangan mengarang sinyal yang tidak didukung teks asli. Kalau tidak ada
indikasi kuat, kembalikan array kosong untuk field terkait.
"""

class SemioticAnalyzer:
    """
    Ekstrak semiotic_tags dari job description mentah via Gemini.
    PENTING: ini heuristik AI-assisted, harus ditampilkan ke user sebagai
    "insight tambahan", bukan fakta absolut (jangan overclaim akurasi).
    """

    def __init__(self, gemini_client):
        self.gemini_client = gemini_client

    def _strip_markdown(self, text: str) -> str:
        """Helper for cleaning up markdown fences from Gemini JSON output."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def analyze(self, job_description: str) -> dict:
        """
        Panggil Gemini dengan SEMIOTIC_SYSTEM_PROMPT + job_description.
        Parse response sebagai JSON.
        """
        prompt = f"{SEMIOTIC_SYSTEM_PROMPT}\\n\\n--- JOB DESCRIPTION ---\\n{job_description}"
        
        try:
            # Panggil Gemini (asumsi model chat standard)
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            raw_text = self._strip_markdown(response.text)
            parsed_json = json.loads(raw_text)
            
            # Validasi schema standar
            return {
                "work_culture_signal": parsed_json.get("work_culture_signal", []),
                "hidden_requirement": parsed_json.get("hidden_requirement", []),
                "tone_formality": parsed_json.get("tone_formality", "netral"),
                "red_flags": parsed_json.get("red_flags", [])
            }
        except Exception as e:
            # Graceful degradation bila LLM error atau JSON malformed
            print(f"[SemioticAnalyzer] Error: {str(e)}")
            return {
                "work_culture_signal": [],
                "hidden_requirement": [],
                "tone_formality": "netral",
                "red_flags": []
            }

    def batch_analyze(self, jobs: list[JobPosting]) -> None:
        """
        Dipanggil dari n8n sebagai batch job. 
        Menganalisis setiap job dan menempelkan tag ke attribut semiotic_tags.
        (Pada implementasi production, hasil tag ini di-upsert ke DB).
        """
        for job in jobs:
            # Hindari re-tag jika sudah ada
            if not job.semiotic_tags:
                tags = self.analyze(f"{job.title}\\n{job.description}\\n{job.requirements}")
                job.semiotic_tags = tags

    def apply_culture_filter(
        self, jobs: list[JobPosting], preferred_culture: str
    ) -> list[JobPosting]:
        """
        Memfilter/deprioritaskan job dengan work_culture_signal yang 
        bertentangan dengan preferensi user.
        """
        filtered_jobs = []
        preferred_lower = preferred_culture.lower()
        
        for job in jobs:
            culture_signals = job.semiotic_tags.get("work_culture_signal", []) if job.semiotic_tags else []
            # Logika scoring sederhana: jika ada sinyal budaya yang secara string matching berlawanan, skip
            # Pada implementasi canggih, LLM bisa digunakan lagi untuk mencocokkan konotasi 
            # Namun untuk efisiensi kita lakukan fuzzy keyword matching
            conflict = False
            for signal in culture_signals:
                # Contoh hardcoded (idealnya ini semantic check via embeddings):
                if "hustle" in signal.lower() and "santai" in preferred_lower:
                    conflict = True
                    break
            
            if not conflict:
                filtered_jobs.append(job)
                
        return filtered_jobs
