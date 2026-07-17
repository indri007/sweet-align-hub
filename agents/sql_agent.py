"""
SQL Agent — Converts natural language to SQL queries.
Uses OpenAI to generate SQL, then executes against the database.
"""

import config
from database import DatabaseManager

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
    Convert natural language question to SQL query using OpenAI.
    Returns the SQL query string.
    """
    if not config.is_gemini_configured():
        return ""

    try:
        client = config.get_gemini_client()
        prompt = f"{SYSTEM_PROMPT}\n\n{natural_language_query}"
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
        )
        sql = response.text.strip()
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

    if not config.is_gemini_configured():
        result["ai_explanation"] = "⚠️ Gemini API key belum diatur. Masukkan API key di file .env"
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
        try:
            client = config.get_gemini_client()
            context = f"Pertanyaan: {question}\nSQL: {sql_query}\nHasil ({len(results)} rows): {str(results[:10])}"
            prompt = f"Kamu adalah data analyst. Jelaskan hasil query database ini dalam Bahasa Indonesia dengan ringkas dan informatif.\n\n{context}"
            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
            )
            result["ai_explanation"] = response.text
        except Exception as e:
            result["ai_explanation"] = f"Ditemukan {len(results)} hasil."

    return result
