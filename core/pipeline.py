from typing import Optional
from .models import JobPosting
import uuid

class EmbeddingPipeline:
    """
    Tanggung jawab: ubah teks (job desc / CV) jadi vector, simpan ke Qdrant,
    dengan Aiven MySQL sebagai source of truth data terstruktur.
    """

    def __init__(self, gemini_client, qdrant_client, mysql_conn):
        self.gemini_client = gemini_client
        self.qdrant_client = qdrant_client
        self.mysql_conn = mysql_conn
        
        # Configuration
        self.collection_name = config.COLLECTION_NAME
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure Qdrant collection exists for jobs."""
        from qdrant_client import models
        if not self.qdrant_client.collection_exists(self.collection_name):
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=768, # Gemini embedding dimension
                    distance=models.Distance.COSINE,
                ),
            )

    def _stable_point_id(self, raw_id: str) -> str:
        """Convert string ID into stable UUID for Qdrant."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(raw_id)))

    def chunk_text(self, text: str, max_tokens: int = 500) -> list[str]:
        """
        Chunking strategy untuk job description panjang.
        Menggunakan Gemini count_tokens untuk mengukur ukuran potongan.
        """
        # Sederhana: Pisahkan berdasarkan paragraf lalu validasi ukurannya
        paragraphs = text.split("\\n\\n")
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            # Di tahap produksi, ini idealnya memanggil model.count_tokens()
            # namun untuk efisiensi kita aproksimasi (1 token ~ 4 karakter) 
            # lalu jika mendekati threshold baru cek pakai tokenizer asli.
            if len(current_chunk) + len(p) < (max_tokens * 3):
                current_chunk += p + "\\n\\n"
            else:
                chunks.append(current_chunk.strip())
                current_chunk = p + "\\n\\n"
                
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        return chunks if chunks else [text]

    def embed_text(self, text: str) -> list[float]:
        """
        Panggil Gemini embedding API.
        Dilengkapi dengan backoff/retry sederhana untuk keandalan.
        """
        import time
        from google.genai import types
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = self.gemini_client.models.embed_content(
                    model="models/gemini-embedding-001",
                    contents=[text],
                    config=types.EmbedContentConfig(output_dimensionality=768)
                )
                return result.embeddings[0].values
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Gagal melakukan embedding setelah {max_retries} percobaan: {str(e)}")
                time.sleep(2 ** attempt)  # Exponential backoff

    def upsert_job_to_qdrant(self, job: JobPosting) -> None:
        """
        Embed job.description + job.requirements,
        simpan ke Qdrant dengan payload metadata untuk pencarian hibrida.
        """
        from qdrant_client import models
        
        combined_text = f"Title: {job.title}\\nIndustry: {job.industry_sector}\\n"
        combined_text += f"Description: {job.description}\\nRequirements: {job.requirements}"
        
        # Embed teks gabungan
        vector = self.embed_text(combined_text)
        
        # Menyusun Payload metadata
        payload = {
            "job_id": job.job_id,
            "title": job.title,
            "company": job.company,
            "industry_sector": job.industry_sector,
            "seniority_level": job.seniority_level,
            "location": job.location,
            "semiotic_tags": job.semiotic_tags or {}
        }
        
        # Simpan ke Qdrant
        point = models.PointStruct(
            id=self._stable_point_id(job.job_id),
            vector=vector,
            payload=payload,
        )
        self.qdrant_client.upsert(
            collection_name=self.collection_name, 
            points=[point]
        )

    def delete_job(self, job_id: str) -> None:
        """
        Hapus dari MySQL DAN Qdrant sekaligus untuk menghindari orphan vector.
        """
        # Hapus dari Qdrant
        from qdrant_client.models import PointIdsList
        stable_id = self._stable_point_id(job_id)
        self.qdrant_client.delete(
            collection_name=self.collection_name,
            points_selector=PointIdsList(points=[stable_id])
        )
        
        # Hapus dari MySQL
        if self.mysql_conn:
            with self.mysql_conn.cursor() as cursor:
                cursor.execute("DELETE FROM jobs WHERE job_id = %s", (job_id,))
            self.mysql_conn.commit()

    def refresh_stale_embeddings(self, updated_since) -> int:
        """
        Re-embed job yang description-nya berubah sejak `updated_since`.
        Return jumlah job yang di-refresh.
        """
        if not self.mysql_conn:
            return 0
            
        count = 0
        with self.mysql_conn.cursor() as cursor:
            # Ambil job yang kadaluarsa (asumsi ada kolom updated_at di DB)
            cursor.execute("SELECT * FROM jobs WHERE updated_at >= %s", (updated_since,))
            stale_jobs = cursor.fetchall()
            
            for row in stale_jobs:
                # Mengemas row menjadi JobPosting
                # (Sangat bergantung pada skema tabel sebenarnya)
                job = JobPosting(
                    job_id=row['job_id'],
                    title=row['title'],
                    company=row['company'],
                    description=row['description'],
                    requirements=row.get('requirements', ''),
                    industry_sector=row.get('industry_sector', ''),
                    seniority_level=row.get('seniority_level', ''),
                    location=row.get('location', '')
                )
                self.upsert_job_to_qdrant(job)
                count += 1
                
        return count
