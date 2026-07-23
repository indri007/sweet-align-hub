# Setup Project (Aiven MySQL + Google Gemini)

## 0. AI Provider: Google Gemini (pengganti OpenAI)
App ini sekarang bisa jalan pakai Gemini API key, tanpa OpenAI, untuk semua fitur teks
(review CV, chat career consultant, mock interview teks, SQL agent, job matching).

File `.env` sudah diisi dengan:
```
LLM_PROVIDER=gemini
GEMINI_API_KEY=<key kamu>
GEMINI_MODEL=gemini-2.5-flash
```

Catatan:
- Fitur **voice interview** (rekam suara + AI bicara) sudah **dinonaktifkan** karena itu
  murni fitur OpenAI (Whisper + TTS) yang tidak dipakai lagi. Interview sekarang teks saja.
- Kalau nanti mau balik ke OpenAI, tinggal ubah `LLM_PROVIDER=openai` dan isi `OPENAI_API_KEY`
  di `.env`, tidak perlu ubah kode.
- Karena key Gemini ini sudah pernah dikirim di chat, sebaiknya **rotate/hapus key ini**
  dari Google AI Studio (aistudio.google.com/apikey) setelah kamu buat key baru, lalu update `.env`.

## 1. Download CA Certificate (untuk Aiven MySQL)
Buka Aiven Console -> service MySQL kamu -> Overview -> bagian "CA certificate"
-> download, lalu simpan sebagai `ca.pem` di folder ini (sejajar dengan `database.py`).

## 2. File .env
File `.env` sudah disertakan di paket ini dengan DATABASE_URL berikut:

```
DATABASE_URL=mysql+pymysql://avnadmin:AVNS_PASSWORD_KAMU@job-assistant-mysql-digimetapesenan-d881.l.aivencloud.com:23799/defaultdb?ssl_ca=./ca.pem
```

Isi juga OPENAI_API_KEY di file .env sebelum menjalankan app.

PENTING: Karena password ini sudah pernah dikirim di chat, sebaiknya reset password
avnadmin dari Aiven Console (Service -> Users -> avnadmin -> Reset password) setelah
migrasi selesai, lalu update ulang .env dengan password baru.

## 3. Install dependencies
```
pip install -r requirements.txt
```

## 4. Test koneksi & buat tabel
```
python -c "from database import DatabaseManager; db = DatabaseManager(); db.create_tables(); print('OK, total jobs:', db.get_job_count())"
```

## 5. Migrasi data dari SQLite lokal ke Aiven
```
python migrate_to_aiven.py
```
Script ini akan membaca semua baris dari data/jobs.db dan menulisnya ke Aiven MySQL.

## 6. Jalankan aplikasi
```
streamlit run app.py
```
