# Setup Koneksi ke Aiven MySQL

## 1. Download CA Certificate
Buka Aiven Console -> service MySQL kamu -> Overview -> bagian "CA certificate"
-> download, lalu simpan sebagai `ca.pem` di folder ini (sejajar dengan `database.py`).

## 2. File .env
File `.env` sudah disertakan di paket ini dengan DATABASE_URL berikut:

```
DATABASE_URL=mysql+pymysql://avnadmin:YOUR_PASSWORD@your-host.aivencloud.com:PORT/defaultdb
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
