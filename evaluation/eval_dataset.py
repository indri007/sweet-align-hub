"""
A small, fixed set of synthetic CV profiles used to evaluate the RAG job-matching
pipeline (agents/rag_agent.match_cv_to_jobs). Each one targets a job category that
actually exists in dataset/jobs.jsonl, so we have a reasonable expectation of what
"relevant" retrieval should look like — without needing hand-labeled ground truth
for every metric (Faithfulness / Response Relevancy / Context Precision all work
reference-free).

Feel free to add more profiles as the dataset grows.
"""

EVAL_CVS = [
    {
        "id": "software_engineer",
        "expected_category": "Software Engineer / Backend Developer",
        "cv_text": """
RIZKY PRATAMA
Software Engineer

RINGKASAN
Software Engineer dengan 4 tahun pengalaman membangun backend service dan API
menggunakan Python dan Go. Terbiasa bekerja dengan arsitektur microservices,
database relasional, dan deployment di cloud.

PENGALAMAN KERJA
Backend Engineer — PT Teknologi Nusantara (2021–sekarang)
- Membangun dan memelihara REST API menggunakan Python (FastAPI) dan Go
- Merancang skema database PostgreSQL untuk sistem pembayaran
- Implementasi CI/CD pipeline dengan Docker dan GitHub Actions

Software Engineer — StartUp Digital (2019–2021)
- Mengembangkan fitur backend untuk aplikasi e-commerce
- Optimasi query database yang mengurangi latency 40%

PENDIDIKAN
S1 Teknik Informatika, Institut Teknologi Bandung (2015–2019)

SKILLS
Python, Go, FastAPI, PostgreSQL, Docker, Kubernetes, Git, REST API, Microservices
""".strip(),
    },
    {
        "id": "data_scientist",
        "expected_category": "Data Scientist / Data Analyst",
        "cv_text": """
DIAN AYU LESTARI
Data Scientist

RINGKASAN
Data Scientist dengan pengalaman 3 tahun di bidang analytics dan machine learning,
fokus pada data transaksi dan prediksi churn pelanggan di industri finansial.

PENGALAMAN KERJA
Data Scientist — Bank Digital Indonesia (2022–sekarang)
- Membangun model prediksi churn menggunakan Python (scikit-learn, XGBoost)
- Membuat dashboard analytics dengan SQL dan Tableau untuk tim bisnis
- Melakukan A/B testing untuk fitur produk baru

Data Analyst — Fintech Corp (2020–2022)
- Analisis data transaksi menggunakan SQL dan Python (pandas)
- Membuat laporan mingguan untuk manajemen

PENDIDIKAN
S1 Statistika, Universitas Gadjah Mada (2016–2020)

SKILLS
Python, SQL, scikit-learn, XGBoost, Tableau, pandas, Machine Learning, Statistik
""".strip(),
    },
    {
        "id": "marketing",
        "expected_category": "Sales / Marketing",
        "cv_text": """
ANDRE WIJAYA
Marketing Executive

RINGKASAN
Marketing profesional dengan 5 tahun pengalaman di digital marketing dan sales,
terbiasa mengelola campaign multi-channel dan tim sales lapangan.

PENGALAMAN KERJA
Digital Marketing Strategist — PT Retail Maju (2021–sekarang)
- Mengelola campaign iklan digital (Meta Ads, Google Ads) dengan budget bulanan
  Rp 200 juta
- Meningkatkan konversi penjualan online sebesar 35% dalam 1 tahun
- Berkoordinasi dengan tim sales untuk strategi promosi produk

Sales Marketing — Distributor Elektronik (2018–2021)
- Mengelola relasi dengan distributor dan toko retail di area Jawa Timur
- Mencapai target penjualan 110% selama 3 tahun berturut-turut

PENDIDIKAN
S1 Manajemen Pemasaran, Universitas Airlangga (2014–2018)

SKILLS
Digital Marketing, Meta Ads, Google Ads, Sales Strategy, Negosiasi, Brand Management
""".strip(),
    },
    {
        "id": "hr",
        "expected_category": "Human Resources / Recruitment",
        "cv_text": """
SITI NURHALIZA
HR Generalist

RINGKASAN
HR profesional dengan pengalaman 4 tahun menangani rekrutmen, onboarding, dan
administrasi kepegawaian di perusahaan manufaktur dan retail.

PENGALAMAN KERJA
HR Staff — PT Manufaktur Sejahtera (2020–sekarang)
- Menangani proses rekrutmen end-to-end untuk posisi staff hingga supervisor
- Mengelola administrasi payroll dan BPJS untuk 300+ karyawan
- Menyusun program onboarding karyawan baru

Recruitment Staff — Retail Group (2019–2020)
- Melakukan screening CV dan interview kandidat entry-level
- Berkoordinasi dengan user department untuk kebutuhan rekrutmen

PENDIDIKAN
S1 Psikologi, Universitas Padjadjaran (2015–2019)

SKILLS
Recruitment, Onboarding, Payroll, HRIS, Employee Relations, Komunikasi
""".strip(),
    },
    {
        "id": "graphic_designer",
        "expected_category": "Graphic Designer / Creative Designer",
        "cv_text": """
SARI WULANDARI
Graphic Designer

RINGKASAN
Graphic Designer dengan 3 tahun pengalaman merancang materi visual untuk
branding, media sosial, dan kebutuhan cetak. Terbiasa bekerja end-to-end
dari konsep hingga produksi final menggunakan Adobe Creative Suite.

PENGALAMAN KERJA
Graphic Designer — PT Kreatif Visual Indonesia (2022–sekarang)
- Merancang materi visual untuk kampanye media sosial dan katalog produk
- Membuat identitas brand (logo, panduan warna, tipografi) untuk klien UMKM
- Kolaborasi dengan tim marketing untuk memastikan konsistensi visual brand

Junior Graphic Designer — Agensi Kreasi Digital (2020–2022)
- Mendesain materi promosi cetak dan digital (flyer, banner, konten Instagram)
- Menyiapkan file produksi siap cetak dengan spesifikasi vendor

PENDIDIKAN
D3 Desain Komunikasi Visual, Universitas Trisakti (2017–2020)

SKILLS
Adobe Photoshop, Adobe Illustrator, Adobe InDesign, Canva, Figma, Branding,
Layout Design, Typography, Social Media Content, Print Production
""".strip(),
    },
]