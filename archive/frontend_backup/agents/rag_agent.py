"""
RAG Agent — Matches CV content to job listings using vector similarity search.
Uses ChromaDB for retrieval and OpenAI for augmented generation.
"""

import config
from vector_store import VectorStoreManager
from llm_client import chat_completion


SYSTEM_PROMPT = """Kamu adalah AI Job Recommendation Expert yang membantu mencocokkan CV seseorang dengan lowongan pekerjaan yang tersedia.

Tugasmu:
1. Analisis profil/skill dari CV user
2. Lihat daftar lowongan pekerjaan yang ditemukan
3. Jelaskan kenapa setiap lowongan cocok dengan profil user
4. Beri ranking dan match score

Jawab dalam Bahasa Indonesia. Gunakan format yang jelas dan terstruktur."""


def match_cv_to_jobs(cv_text: str, top_k: int = 10) -> dict:
    """
    Match CV content to job listings via RAG.

    Returns:
        dict with keys:
        - "matches": list of job matches with similarity scores
        - "ai_summary": AI-generated recommendation narrative (if OpenAI available)
    """
    # Step 1: Vector search — find similar jobs
    vs = VectorStoreManager()
    matches = vs.match_cv_to_jobs(cv_text, top_k=top_k)

    result = {
        "matches": matches,
        "ai_summary": None,
    }

    # Step 2: Augmented generation — AI explains why jobs match
    if matches:
        # Build context from retrieved jobs
        jobs_context = ""
        for i, match in enumerate(matches[:5], 1):
            meta = match.get("metadata", {})
            jobs_context += f"\n--- Lowongan #{i} (Similarity: {match['similarity_score']}%) ---\n"
            jobs_context += f"Posisi: {meta.get('job_title', 'N/A')}\n"
            jobs_context += f"Perusahaan: {meta.get('company_name', 'N/A')}\n"
            jobs_context += f"Lokasi: {meta.get('location', 'N/A')}\n"
            jobs_context += f"Tipe: {meta.get('work_type', 'N/A')}\n"
            jobs_context += f"Gaji: {meta.get('salary', 'N/A')}\n"
            # Include short excerpt of job description
            doc = match.get("document", "")
            if doc and len(doc) > 500:
                doc = doc[:500] + "..."
            jobs_context += f"Deskripsi: {doc}\n"

        # Try N8N first
        if config.is_n8n_configured():
            try:
                from n8n_client import match_cv_to_jobs_n8n
                ai_text = match_cv_to_jobs_n8n(cv_text, jobs_context)
                if ai_text and not ai_text.startswith("Error") and not ai_text.startswith("Tidak dapat") and not ai_text.startswith("N8N"):
                    result["ai_summary"] = ai_text
                    return result
            except Exception:
                pass

        # Fallback to local LLM
        if config.is_llm_configured():
            try:
                user_prompt = f"""Berikut adalah CV user:
---
{cv_text[:3000]}
---

Berikut adalah lowongan pekerjaan yang ditemukan berdasarkan kecocokan:
{jobs_context}

Berikan analisis singkat:
1. Skill utama apa yang kamu lihat dari CV ini?
2. Untuk setiap lowongan, jelaskan dalam 1-2 kalimat kenapa cocok/tidak cocok
3. Rekomendasikan top 3 lowongan paling cocok beserta alasannya"""

                reply = chat_completion(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                )
                result["ai_summary"] = reply
            except Exception as e:
                result["ai_summary"] = f"Error generating AI summary: {str(e)}"

    return result


def search_jobs_by_query(query: str, top_k: int = 10) -> list[dict]:
    """
    Search jobs by natural language query.
    Returns list of matching jobs with similarity scores.
    """
    vs = VectorStoreManager()
    return vs.search_similar_jobs(query, top_k=top_k)
