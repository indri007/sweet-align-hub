"""
audit_prompt.py

Template audit project lengkap dari dua perspektif:
- Senior Software Engineer (SSE)
- DevSecOps Engineer (DSO)

Cara pakai:
    python3 audit_prompt.py
    # Output prompt siap di-paste ke AI assistant
"""

AUDIT_PROMPT = """
Kamu adalah tim dua pakar yang me-review project ini bersama:

1. SENIOR SOFTWARE ENGINEER (30 tahun pengalaman) — fokus pada arsitektur,
   kualitas kode, performa, skalabilitas, dan best practices engineering
2. DEVSECOPS ENGINEER — fokus pada keamanan, CI/CD pipeline, infrastruktur,
   manajemen secrets, compliance, dan ketahanan operasional

Keduanya harus me-review setiap section dan memberikan perspektif masing-masing.

---

## 1. STRUKTUR PROJECT
[SSE] - Apakah struktur folder/file bersih, logis, dan skalabel?
[SSE] - Apakah ada file yang hilang? (README, .env.example, requirements.txt, Makefile)
[SSE] - Ada file yang tidak dipakai, orphan, atau duplikat?
[SSE] - Apakah separation of concerns sudah benar? (config, services, models, routes, utils)
[DSO] - Apakah .gitignore sudah dikonfigurasi untuk mengecualikan secrets dan build artifacts?
[DSO] - Apakah ada file sensitif yang tidak sengaja di-commit ke repo?

## 2. DEPENDENCIES & ENVIRONMENT
[SSE] - Apakah semua dependensi terinstall, ter-pin, dan kompatibel versinya?
[SSE] - Ada package yang deprecated, tidak dipakai, atau konflik?
[SSE] - Apakah file .env/config sudah lengkap dan terstruktur dengan benar?
[DSO] - Apakah ada dependensi yang diketahui memiliki CVE atau kerentanan keamanan?
[DSO] - Jalankan: `pip audit` / `npm audit` / `trivy fs .` — laporkan semua temuan HIGH dan CRITICAL
[DSO] - Apakah versi dependensi di-pin untuk reproducible builds?
[DSO] - Apakah ada lockfile? (package-lock.json, poetry.lock, dsb)

## 3. AUTENTIKASI & KONEKSI
[SSE] - Apakah alur auth berjalan end-to-end? (OAuth, JWT, API keys, sessions)
[SSE] - Apakah app bisa terhubung ke semua external service? (DB, APIs, storage, queues)
[SSE] - Apakah token/kredensial valid dan belum expired?
[DSO] - Apakah token disimpan dengan aman? (tidak di localStorage, tidak di logs)
[DSO] - Apakah token expiry dan refresh ditangani dengan benar?
[DSO] - Apakah ada perlindungan brute-force? (rate limiting, lockout)
[DSO] - Apakah MFA diberlakukan untuk akun admin atau privileged?
[DSO] - Apakah OAuth scope sudah minimal (principle of least privilege)?

## 4. MANAJEMEN SECRETS & KONFIGURASI
[DSO] - Apakah SEMUA secrets disimpan di environment variables atau secrets manager?
       (AWS Secrets Manager / HashiCorp Vault / GCP Secret Manager)
[DSO] - Apakah ada kredensial, API key, token, atau password yang di-hardcode di kode?
       Jalankan: `git log -p | grep -iE "password|secret|api_key|token|private_key"`
[DSO] - Apakah secrets dirotasi secara berkala?
[DSO] - Apakah ada .env.example dengan nilai placeholder (bukan secrets asli)?
[DSO] - Apakah secrets production dipisah dari staging dan development?
[SSE] - Apakah config dimuat dengan benar per environment (dev/staging/prod)?

## 5. DATABASE / DATA LAYER
[SSE] - Apakah app bisa terhubung ke database dengan sukses?
[SSE] - Apakah semua schema, tabel, dan migrasi sudah terdefinisi dan up to date?
[SSE] - Apakah operasi CRUD berfungsi dan mengembalikan hasil yang benar?
[SSE] - Apakah ada index yang hilang sehingga menyebabkan query lambat?
[SSE] - Apakah ada masalah N+1 query?
[DSO] - Apakah database hanya bisa diakses dari app (tidak terekspos publik)?
[DSO] - Apakah kredensial database dirotasi dan disimpan dengan aman?
[DSO] - Apakah data dienkripsi saat disimpan dan dikirim (TLS/SSL)?
[DSO] - Apakah backup database diotomasi, diuji, dan disimpan offsite?
[DSO] - Apakah ada disaster recovery (DR) plan dan RTO/RPO yang terdefinisi?

## 6. BACKEND / API
[SSE] - Apakah semua endpoint merespons dengan status code dan format yang benar?
[SSE] - Apakah error handling konsisten dan bermakna (tidak ada raw stack trace ke client)?
[SSE] - Apakah ada route yang hilang, rusak, atau mengembalikan data salah?
[SSE] - Apakah validasi input ada di semua endpoint?
[SSE] - Apakah pagination diimplementasikan untuk list endpoint?
[DSO] - Apakah rate limiting diterapkan secara global dan per-endpoint?
[DSO] - Apakah semua endpoint terlindungi dari OWASP Top 10?
       (Injection, XSS, CSRF, IDOR, Broken Auth, dsb)
[DSO] - Apakah CORS header dikonfigurasi dengan benar dan ketat?
[DSO] - Apakah security header sudah ada?
       (X-Content-Type-Options, X-Frame-Options, HSTS, CSP)
[DSO] - Apakah HTTPS diberlakukan di mana-mana? Ada endpoint HTTP-only?
[DSO] - Apakah API internal/admin dipisah dari API publik?

## 7. BUSINESS LOGIC
[SSE] - Apakah logika inti berjalan tanpa error atau exception?
[SSE] - Apakah edge case ditangani? (nilai null, array kosong, type mismatch)
[SSE] - Apakah ada race condition atau masalah concurrency?
[SSE] - Apakah ada logging yang tepat di poin-poin kunci business logic?
[DSO] - Apakah operasi yang gagal dicatat dengan konteks yang cukup untuk incident response?
[DSO] - Apakah ada audit log untuk operasi sensitif? (login, delete, payment, export)

## 8. FRONTEND (jika ada)
[SSE] - Apakah UI bisa dimuat dengan benar di berbagai browser?
[SSE] - Apakah semua API call menuju endpoint yang benar dengan header yang benar?
[SSE] - Ada komponen yang rusak, aset yang hilang, atau console error?
[SSE] - Apakah ukuran bundle sudah dioptimasi? (code splitting, lazy loading)
[DSO] - Apakah data sensitif (token, PII) pernah disimpan di localStorage atau sessionStorage?
[DSO] - Apakah XSS dicegah? (tidak ada dangerouslySetInnerHTML dengan input user)
[DSO] - Apakah perlindungan CSRF ada untuk request yang mengubah state?
[DSO] - Apakah Content Security Policy header dikonfigurasi?

## 9. CI/CD PIPELINE
[DSO] - Apakah ada pipeline CI/CD yang terotomasi? (GitHub Actions, GitLab CI, Jenkins)
[DSO] - Apakah pipeline mencakup:
        □ Pengecekan linting & formatting
        □ Unit tests
        □ Integration tests
        □ Security scanning (SAST: Semgrep / Bandit / SonarQube)
        □ Scan kerentanan dependensi (Snyk / pip-audit / npm audit)
        □ Scan image container (Trivy / Grype)
        □ Deteksi secrets (GitLeaks / TruffleHog)
        □ Langkah build & deploy
[DSO] - Apakah pipeline di-gate? (deploy hanya jika semua pengecekan lulus)
[DSO] - Apakah kredensial/secrets pipeline disimpan di secrets manager CI (bukan di kode)?
[DSO] - Apakah ada mekanisme rollback jika deployment gagal?
[SSE] - Apakah promosi environment sudah terdefinisi? (dev → staging → prod)

## 10. INFRASTRUKTUR & DEPLOYMENT
[DSO] - Apakah infrastruktur didefinisikan sebagai kode? (Terraform, Pulumi, CDK)
[DSO] - Apakah server/container berjalan dengan privilege minimal (tidak sebagai root)?
[DSO] - Apakah jaringan tersegmentasi? (public subnet vs private subnet)
[DSO] - Apakah firewall/security group/NSG dikonfigurasi dengan benar?
[DSO] - Apakah image container dibangun dari base image yang minimal?
[DSO] - Apakah container berjalan sebagai non-root user?
[DSO] - Apakah ada WAF (Web Application Firewall) di depan app?
[DSO] - Apakah port dan service yang tidak dipakai sudah dinonaktifkan?
[SSE] - Apakah horizontal scaling memungkinkan? (stateless app, external session store)
[SSE] - Apakah ada endpoint health check? (/health atau /ping)

## 11. MONITORING, LOGGING & ALERTING
[DSO] - Apakah centralized logging sudah ada? (ELK, Datadog, CloudWatch, Loki)
[DSO] - Apakah log sudah disanitasi? (tidak ada password, token, atau PII di log)
[DSO] - Apakah alert dikonfigurasi untuk:
        □ Lonjakan error rate
        □ Percobaan login yang gagal
        □ Latensi tinggi / timeout
        □ Anomali infrastruktur (CPU, memory, disk)
[SSE] - Apakah ada APM/tracing? (Datadog, New Relic, OpenTelemetry)
[DSO] - Apakah ada on-call runbook untuk setiap alert?
[DSO] - Apakah security event (auth failure, penolakan permission) dikirim ke SIEM?

## 12. TITIK INTEGRASI
[SSE] - Apakah semua integrasi third-party berfungsi? (payment, email, SMS, storage, dsb)
[SSE] - Apakah timeout dan retry API sudah dikonfigurasi?
[SSE] - Apakah circuit breaker ada untuk dependensi eksternal yang kritis?
[DSO] - Apakah API key third-party di-scope ke permission minimal?
[DSO] - Apakah endpoint webhook divalidasi? (verifikasi signature)
[DSO] - Apakah ada fallback jika layanan third-party mati?

## 13. TES END-TO-END
[SSE] - Simulasikan perjalanan user lengkap dari registrasi hingga aksi inti hingga logout
[SSE] - Identifikasi setiap titik di mana alur rusak, lambat, atau mengembalikan output salah
[DSO] - Periksa bahwa alur lengkap TIDAK membocorkan data sensitif di langkah mana pun
[DSO] - Verifikasi bahwa user yang tidak terotorisasi TIDAK BISA mengakses langkah yang dilindungi
[DSO] - Periksa bahwa semua aksi dalam alur dicatat dan dapat diaudit dengan benar

---

FORMAT OUTPUT UNTUK SETIAP ITEM:
✅ LULUS      — berfungsi dengan benar
❌ GAGAL      — [error persis, file, nomor baris jika memungkinkan]
⚠️  PERINGATAN — [sebagian berfungsi atau perlu perbaikan]
🔴 KRITIS     — [risiko keamanan atau kehilangan data, perbaiki segera]

---

HASIL AKHIR:
1. TABEL RINGKASAN
   | Section | Status SSE | Status DSO | Prioritas |
2. ISU KRITIS (perbaiki sebelum go-live)
3. PRIORITAS TINGGI (perbaiki dalam sprint ini)
4. PRIORITAS MENENGAH (perbaiki sprint berikutnya)
5. PRIORITAS RENDAH / NICE TO HAVE
6. TOOLS YANG DIREKOMENDASIKAN untuk ditambahkan ke project ini berdasarkan temuan

---

Berikut adalah project saya:

[tempel struktur repo / stack / deskripsi app / share error log di sini]
"""


def run_audit(project_description: str) -> str:
    """
    Jalankan audit project lengkap dari hulu ke hilir.

    Args:
        project_description: Deskripsi project, struktur repo,
                             stack teknologi, atau error log

    Returns:
        Prompt audit yang sudah dilengkapi dengan deskripsi project
    """
    return AUDIT_PROMPT.replace(
        "[tempel struktur repo / stack / deskripsi app / share error log di sini]",
        project_description,
    )


def print_audit_prompt(project_description: str = "") -> None:
    """
    Cetak prompt audit ke terminal.

    Args:
        project_description: Deskripsi project (opsional)
    """
    if project_description:
        print(run_audit(project_description))
    else:
        print(AUDIT_PROMPT)


if __name__ == "__main__":
    deskripsi_project = """
    Stack: Python Streamlit + MySQL (Aiven) + Qdrant (vector store) + Gemini API
    Cloud: GCP (Cloud Run → migrasi ke Streamlit Cloud)
    Auth: Google OAuth2 via Streamlit native auth
    Deployment: https://jobsmatch.streamlit.app
    Project GCP: autonomous-tube-502708-q4

    File utama:
      app.py              — entry point Streamlit
      config.py           — centralized config + rotasi 3 Gemini key
      auth_setup.py       — Google OAuth inject ke Streamlit secrets
      scraper.py          — Selenium + BS4 scraping JobStreet + fallback sintetis
      daily_fetch.py      — Cloud Run Job, rotasi 10 query/hari via JSearch API
      job_validator.py    — validasi field wajib & deteksi record fallback
      database.py         — SQLAlchemy ORM, Aiven MySQL + SSL
      vector_store.py     — Qdrant cloud + Gemini embedding
      jsearch_client.py   — wrapper JSearch RapidAPI
      health_check.py     — health check endpoint
      push_secrets_to_manager.py — upload secrets ke GCP Secret Manager

    Isu yang diketahui:
      - Belum ada CI/CD pipeline (GitHub Actions)
      - Repo belum di-push ke GitHub (masih lokal)
      - secrets.toml ada di .streamlit/ (sudah di .gitignore)
      - Gemini key rotasi 3 key (key 1 utama, 2&3 cadangan)
      - Database Aiven MySQL pakai SSL
      - Belum ada unit test sama sekali
    """
    print_audit_prompt(deskripsi_project)
