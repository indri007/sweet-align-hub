"""
SQL Agent — Converts natural language to SQL queries.
Uses OpenAI to generate SQL, then executes against the database.
"""

import config
from database import DatabaseManager
from llm_client import chat_completion

SYSTEM_PROMPT = """Kamu adalah SQL Query Generator. Tugasmu mengubah pertanyaan user tentang data lowongan pekerjaan menjadi SQL query.

Database schema:
Table: jobs
Columns:
- id (INTEGER, primary key)
- job_title (VARCHAR) — judul pekerjaan
- company_name (VARCHAR) — nama perusahaan
- location (VARCHAR) — lokasi kerja
- work_type (VARCHAR) — tipe: 'Full time', 'Paruh waktu', 'Kontrak/Temporer', 'Kasual'
- salary_raw (VARCHAR) — gaji dalam format text asli
- salary_min (FLOAT, nullable) — gaji minimum dalam Rupiah
- salary_max (FLOAT, nullable) — gaji maximum dalam Rupiah
- job_description (TEXT) — deskripsi pekerjaan
- scrape_timestamp (VARCHAR) — timestamp scraping

Rules:
1. Hanya generate SELECT queries (READ-ONLY). JANGAN buat INSERT, UPDATE, DELETE, DROP, ALTER.
2. Jawab HANYA dengan SQL query, tanpa penjelasan lain.
3. Gunakan LIKE untuk pencarian text (case-insensitive pakai LOWER()).
4. Limit results ke 20 jika tidak disebutkan.
5. Salary dalam Rupiah (contoh: 10000000 = Rp 10.000.000).
6. Untuk pertanyaan agregat, gunakan COUNT, AVG, MIN, MAX, GROUP BY sesuai kebutuhan."""


def generate_sql_query(natural_language_query: str) -> str:
    """
    Convert natural language question to SQL query using N8N or local LLM.
    Returns the SQL query string.
    """
    # Try N8N first
    if config.is_n8n_configured():
        try:
            from n8n_client import generate_sql_query_n8n
            sql = generate_sql_query_n8n(natural_language_query)
            if sql and not sql.startswith("Error") and not sql.startswith("Tidak dapat") and not sql.startswith("N8N"):
                return sql
        except Exception:
            pass

    if not config.is_llm_configured():
        return ""

    try:
        reply = chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": natural_language_query},
            ],
            temperature=0,
            max_tokens=500,
        )
        sql = reply.strip()
        # Clean up: remove markdown code blocks if present
        if sql.startswith("```"):
            lines = sql.split("\n")
            sql = "\n".join(lines[1:-1])
        return sql
    except Exception as e:
        return f"-- Error: {str(e)}"


def query_jobs_natural_language(question: str) -> dict:
    """
    Full pipeline: natural language → SQL → execute → format results.

    Returns dict with:
    - "question": original question
    - "sql_query": generated SQL
    - "results": list of result dicts
    - "ai_explanation": AI explanation of results
    """
    result = {
        "question": question,
        "sql_query": "",
        "results": [],
        "ai_explanation": None,
    }

    if not config.is_llm_configured() and not config.is_n8n_configured():
        result["ai_explanation"] = "⚠️ API key belum diatur. Masukkan GEMINI_API_KEY di file .env"
        return result

    # Step 1: Generate SQL
    sql_query = generate_sql_query(question)
    result["sql_query"] = sql_query

    if sql_query.startswith("-- Error"):
        result["ai_explanation"] = sql_query
        return result

    # Safety check: only allow SELECT
    if not sql_query.strip().upper().startswith("SELECT"):
        result["ai_explanation"] = "⚠️ Query yang di-generate bukan SELECT query. Ditolak untuk keamanan."
        return result

    # Step 2: Execute SQL
    db = DatabaseManager()
    results = db.execute_raw_sql(sql_query)
    result["results"] = results

    # Step 3: AI explanation
    if results and "error" not in results[0]:
        # Try N8N first
        if config.is_n8n_configured():
            try:
                from n8n_client import explain_sql_results_n8n
                ai_text = explain_sql_results_n8n(question, sql_query, results)
                if ai_text and not ai_text.startswith("Error") and not ai_text.startswith("Tidak dapat") and not ai_text.startswith("N8N"):
                    result["ai_explanation"] = ai_text
                    return result
            except Exception:
                pass

        # Fallback to local LLM
        if config.is_llm_configured():
            try:
                context = f"Pertanyaan: {question}\nSQL: {sql_query}\nHasil ({len(results)} rows): {str(results[:10])}"

                reply = chat_completion(
                    messages=[
                        {"role": "system", "content": "Kamu adalah data analyst. Jelaskan hasil query database ini dalam Bahasa Indonesia dengan ringkas dan informatif."},
                        {"role": "user", "content": context},
                    ],
                    temperature=0.5,
                    max_tokens=800,
                )
                result["ai_explanation"] = reply
            except Exception:
                result["ai_explanation"] = f"Ditemukan {len(results)} hasil."
        else:
            result["ai_explanation"] = f"Ditemukan {len(results)} hasil."

    return result
