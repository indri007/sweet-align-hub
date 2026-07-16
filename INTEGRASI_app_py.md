# Integrasi Tahap 4 (Observability) ke app.py

## 1. Tambahan requirements.txt
```
sentry-sdk
```
(4 file lainnya tidak butuh dependency baru — cuma pakai stdlib + sqlalchemy/qdrant client yang sudah ada)

## 2. Paling atas app.py — Sentry + logger + health server

```python
import os
import sentry_sdk

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN", ""),
    traces_sample_rate=0.2,       # 20% transaksi buat performance tracing
    environment=os.environ.get("ENVIRONMENT", "production"),
    send_default_pii=False,       # jangan kirim data pribadi user ke Sentry
)

from logger import get_logger
from health_server import start_health_server

logger = get_logger(__name__)

# Streamlit re-run script tiap interaksi user — pakai session_state biar
# health server cuma start sekali per container, bukan tiap rerun
if "health_server_started" not in st.session_state:
    start_health_server(port=8081)
    st.session_state["health_server_started"] = True
    logger.info("App startup complete")
```

## 3. Pakai logger + metrics di flow CV upload (contoh, sesuaikan nama variabel)

```python
from metrics import record_event, track_duration

uploaded_file = st.file_uploader("Upload CV", type=["pdf", "docx"])
if uploaded_file:
    try:
        with track_duration("cv_processing", format=uploaded_file.type):
            text = extract_cv_text(uploaded_file.getvalue(), uploaded_file.name)
        record_event("cv_upload_success")
        logger.info("CV processed", extra={"filename": uploaded_file.name})
    except Exception as e:
        record_event("cv_upload_failure", reason=type(e).__name__)
        logger.error("CV processing failed", extra={"error": str(e), "filename": uploaded_file.name})
        sentry_sdk.capture_exception(e)
        st.error(f"Gagal memproses CV: {e}")
```

## 4. Set env var Sentry di Cloud Run

```bash
gcloud run services update job-search-app \
  --region=REGION \
  --update-env-vars SENTRY_DSN=https://xxxx@xxx.ingest.sentry.io/xxxx,ENVIRONMENT=production
```
(Bikin project baru dulu di sentry.io kalau belum punya, gratis untuk 5k events/bulan)

## 5. Cara cek health check

- **Liveness dasar (publik, built-in Streamlit):**
  `curl https://job-search-app-xxx.run.app/_stcore/health` → `ok`

- **Deep check (internal only, port 8081):**
  Tidak bisa langsung dari internet. Cara akses:
  ```bash
  gcloud run services proxy job-search-app --region=REGION --port=8080
  # lalu di terminal lain:
  curl http://localhost:8081/health/deep
  ```
  Atau daftarkan sebagai startup/liveness probe di service YAML kalau mau
  Cloud Run otomatis restart container saat dependency down:
  ```yaml
  livenessProbe:
    httpGet:
      path: /health/deep
      port: 8081
    periodSeconds: 30
  ```

## 6. Log-based metrics di Cloud Console (sekali setup, no code)

Logging → Log-based Metrics → Create Metric
- Filter: `jsonPayload.metric_type="cv_upload_success"` → counter
- Filter: `jsonPayload.metric_type="cv_processing_duration_ms"` → distribution
Lalu bisa dipasang jadi chart di Cloud Monitoring dashboard atau alert
(misal alert kalau `cv_upload_failure` > 5 dalam 10 menit).
