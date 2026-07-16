# Menjalankan dengan Docker

## 1. Siapkan `.env`
Pastikan file `.env` sudah terisi (lihat `.env.example`), minimal:
```
GEMINI_API_KEY=your-key-here
```

## 2. Build & jalankan
```bash
docker compose up --build
```

App akan tersedia di http://localhost:8501

## 3. Data lokal (SQLite + ChromaDB)
Saat container pertama kali start, `entrypoint.sh` otomatis menjalankan
`data_preparation.py` untuk mengisi database & vector store dari
`dataset/jobs.jsonl` — proses ini idempotent (aman dijalankan ulang, akan
di-skip kalau data sudah ada). Data disimpan di folder `./data` di host
(lewat volume mount), jadi tidak hilang saat container di-restart.

Kalau kamu pakai backend cloud (Aiven MySQL / Qdrant Cloud, sesuai
`AIVEN_SETUP.md`), volume `./data` tetap aman untuk di-mount tapi tidak
akan terpakai untuk penyimpanan utama.

## 4. Menjalankan tanpa docker-compose
```bash
docker build -t jobmatch-ai .
docker run -p 8501:8501 --env-file .env -v $(pwd)/data:/app/data jobmatch-ai
```

## 5. Menghentikan
```bash
docker compose down
```
Data di `./data` tetap ada di host setelah container dihentikan.
