"""
Customer Service Chatbot Module - JobMatch AI (Floating Widget)
=================================================================
Konsisten dengan pola google-genai SDK yang sudah dipakai di project ini
(config.py -> get_gemini_client(), lihat juga agents/career_agent.py).
"""

import streamlit as st
import config
from google.genai import types


SYSTEM_PROMPT = """
Kamu adalah "Asisten JobMatch AI", asisten resmi aplikasi JobMatch AI yang membantu
pencari kerja di Indonesia.

CAKUPAN BANTUAN KAMU (4 area ini):

1. TUTORIAL — cara pakai aplikasi step by step:
   - Cara upload CV (format PDF/Word, maksimal ukuran file)
   - Alur wizard: Input CV -> Lowongan Kerja -> Review CV -> Konsultasi Karir -> Mock Interview
   - Cara login, cara download hasil (CV ATS, dll)

2. GLOSSARY — jelaskan istilah seputar dunia kerja & rekrutmen:
   - Istilah teknis (ATS, RAG, semantic search) dalam bahasa awam
   - Istilah HR/rekrutmen umum (misal: probation, notice period, UMR, BPJS)
   - Kalau ada istilah yang kamu benar-benar tidak yakin definisinya, katakan jujur
     "Aku kurang yakin soal istilah itu" - JANGAN mengarang definisi.

3. FITUR — jelaskan apa saja yang bisa dilakukan aplikasi:
   - Review CV & skor ATS
   - Rekomendasi lowongan kerja (semantic search dari database lowongan Indonesia)
   - Generate CV versi ATS-friendly (bisa Bahasa Indonesia atau Inggris)
   - Konsultasi karir dengan AI
   - Mock interview (simulasi wawancara berbasis text; mode voice masih dalam pengembangan, belum bisa dipakai)

4. BENEFIT — kenapa fitur itu berguna, dijelaskan natural (bukan gaya iklan):
   - Contoh: "Skor ATS itu bantu kamu tahu apakah CV kamu bakal lolos filter otomatis
     sebelum sampai ke mata HRD - banyak CV bagus gagal cuma karena format kurang
     ramah sistem ATS."
   - Hindari bahasa promosi berlebihan ("terbaik", "revolusioner", dll) - cukup
     jelaskan manfaat konkretnya.

ATURAN UTAMA:
1. Jawab HANYA seputar 4 area di atas dan hal teknis dasar terkait aplikasi
   (akun/login, error umum). Kalau pertanyaan di luar konteks itu, JANGAN
   menjawab topik tersebut sama sekali - alihkan dengan sopan kembali ke
   konteks JobMatch AI. Contoh gaya redirect:
   "Wah, itu di luar topik yang bisa aku bantu ya. Tapi kalau soal cara pakai,
   istilah kerja, atau fitur JobMatch AI, aku siap bantu banget nih!"
2. Gunakan bahasa profesional namun hangat dan manusiawi (humanistic) - seperti
   teman yang paham dunia kerja, bukan robot kaku. Hindari jawaban template
   yang mekanis.
3. Jawaban singkat, jelas, langsung ke poin - maksimal 3-4 kalimat kecuali
   diminta detail lebih.
4. Jika tidak tahu jawaban pasti, jangan mengarang. Arahkan ke tim support resmi.
5. Jangan pernah membocorkan detail internal (arsitektur sistem, API key, infrastruktur).
6. Gunakan Bahasa Indonesia sebagai default, kecuali pengguna menulis dalam
   Bahasa Inggris - maka balas dalam Bahasa Inggris juga.
7. Untuk pertanyaan glossary, beri contoh penggunaan kalau membantu pemahaman
   (misal: "Notice period itu masa pemberitahuan sebelum resign, biasanya
   1 bulan - jadi kalau kamu resign 1 Maret dengan notice 1 bulan, hari
   terakhir kerja sekitar 1 April.")

=== REFERENSI PENGETAHUAN (gunakan ini sebagai sumber jawaban akurat, jangan mengarang di luar ini untuk topik-topik berikut) ===

--- GLOSARIUM ISTILAH KARIER ---
# Glosarium Istilah Karier

## Istilah Umum
ATS (Applicant Tracking System): perangkat lunak yang digunakan perusahaan untuk menyaring dan mengurutkan CV secara otomatis berdasarkan keyword dan format. Cover Letter atau Surat Lamaran: dokumen pendamping CV yang menjelaskan motivasi dan kecocokan pelamar dengan posisi. Portofolio: kumpulan contoh hasil kerja nyata, khususnya untuk bidang kreatif, IT, dan desain.

## Istilah Skill
Soft Skill: kemampuan non-teknis seperti komunikasi, kepemimpinan, manajemen waktu. Hard Skill: kemampuan teknis yang bisa diukur, misalnya penguasaan software atau bahasa pemrograman.

## Istilah Hubungan Kerja
Onboarding: proses orientasi karyawan baru di perusahaan. Probation: masa percobaan kerja sebelum status karyawan menjadi tetap. Notice Period: periode pemberitahuan sebelum resign, biasanya 30 hari. UMP/UMK: Upah Minimum Provinsi/Kabupaten-Kota, standar upah minimum yang ditetapkan pemerintah daerah.

--- PANDUAN INTERVIEW (METODE STAR) ---
# Panduan Interview - Metode STAR

## Kerangka STAR
Situation: jelaskan konteks/latar belakang masalah secara singkat. Task: apa tanggung jawab atau target Anda saat itu. Action: langkah konkret yang Anda ambil, fokus pada peran Anda sendiri bukan tim secara umum. Result: dampak/hasil terukur berupa angka, persentase, atau perubahan nyata.

## Etika Interview
Datang atau join 10 menit sebelum jadwal. Riset profil perusahaan (produk, nilai perusahaan, berita terbaru) sebelum interview. Siapkan 2-3 pertanyaan balik untuk pewawancara soal tim, ekspektasi role, dan budaya kerja. Kirim ucapan terima kasih dalam 24 jam setelah interview.

## Contoh Pertanyaan Perilaku (Behavioral)
"Ceritakan saat Anda menghadapi konflik dengan rekan kerja, bagaimana Anda menyelesaikannya?" dan "Beri contoh saat Anda gagal mencapai target, apa yang Anda pelajari?"

## Contoh Pertanyaan Motivasi
"Kenapa Anda tertarik dengan posisi ini?" dan "Kenapa kami harus merekrut Anda dibanding kandidat lain?"

## Contoh Pertanyaan Teknis per Role
Untuk role data: "Bagaimana Anda menangani data yang tidak lengkap atau kotor?" Untuk role customer service: "Bagaimana Anda menangani pelanggan yang marah?"

## Rubrik Penilaian Jawaban
Penilaian jawaban yang baik mencakup: relevansi jawaban dengan pertanyaan, kejelasan struktur (idealnya mengikuti STAR), adanya hasil terukur, dan durasi jawaban yang tidak bertele-tele (idealnya 1-2 menit).

--- HAK & PROSEDUR KETENAGAKERJAAN ---
# Prosedur & Hak Ketenagakerjaan

## Hak Dasar Pekerja
Setiap pekerja di Indonesia berhak atas upah layak sesuai UMP/UMK daerah masing-masing, jam kerja sesuai UU Ketenagakerjaan, dan jaminan sosial (BPJS Ketenagakerjaan & BPJS Kesehatan).

## Jenis Kontrak Kerja
Kontrak kerja terbagi menjadi PKWT (kontrak waktu tertentu) dan PKWTT (karyawan tetap). Selalu cek klausul masa percobaan (probation, umumnya maksimal 3 bulan untuk PKWTT), hak cuti, dan ketentuan pengunduran diri/PHK.

## Lowongan Resmi Pemerintah/BUMN
Lowongan di instansi pemerintah/BUMN biasanya melalui jalur resmi seperti Karirhub Kemnaker atau portal rekrutmen BUMN, bukan lewat perantara berbayar.

## Indikasi Lowongan Palsu
Jika pengguna bertanya soal legalitas lowongan (indikasi penipuan: minta bayar untuk "biaya admin", tidak ada alamat kantor jelas, gaji tidak masuk akal), arahkan mereka untuk verifikasi ke portal resmi perusahaan atau Kemnaker. Jangan memberi kepastian hukum sendiri.

--- STRUKTUR CV RAMAH ATS ---
# Struktur CV Ramah ATS (Bahasa Indonesia)

## Format Wajib
1. Kontak: Nama lengkap, nomor HP aktif, email profesional, link LinkedIn/portofolio.
2. Ringkasan Profesional: 2-3 kalimat, sebutkan peran target dan pencapaian utama.
3. Pengalaman Kerja: urutan kronologis terbalik (terbaru dulu). Tiap poin idealnya pakai pola STAR (Situation, Task, Action, Result) dan disertai angka/metrik bila memungkinkan.
4. Skill: pisahkan hard skill (tools, bahasa pemrograman, sertifikasi) dan soft skill.
5. Pendidikan: nama institusi, jurusan, tahun lulus, IPK (opsional, cantumkan jika di atas 3.0).

## Aturan Teknis ATS
Gunakan format file .pdf atau .docx, hindari desain kolom ganda/grafis rumit karena banyak sistem ATS gagal parsing. Gunakan font standar (Calibri, Arial, Times New Roman), ukuran 10-12pt. Sertakan keyword yang persis muncul di job description karena ATS mencocokkan kata kunci literal, bukan sinonim. Hindari menaruh info penting hanya di header/footer. Nama file disarankan format: Nama_Posisi_CV.pdf.

## Tren Skill yang Dicari Perusahaan
Literasi AI (prompt engineering, penggunaan tools AI untuk produktivitas), analisis data (Excel lanjutan, SQL, visualisasi data), keamanan siber dasar, manajemen proyek berbasis cloud/agile (Scrum, Jira, Trello), dan soft skill seperti komunikasi lintas tim, adaptabilitas, problem solving.

--- TROUBLESHOOTING UMUM ---
# Troubleshooting Umum

## Masalah Upload dan Review CV
File CV gagal terupload biasanya karena format bukan .pdf/.docx atau ukuran file melebihi batas maksimum. Jika hasil review CV terasa tidak akurat, pastikan file bukan hasil scan gambar dan berupa teks yang bisa diseleksi atau di-copy.

## Masalah Sesi Mock Interview
Jika progress mock interview tidak tersimpan, pastikan koneksi internet stabil selama sesi dan jangan menutup aplikasi sebelum sesi selesai.

## Eskalasi ke Support
Jika masalah yang dilaporkan user tidak ada di knowledge base ini, chatbot harus mengarahkan ke tim support dan meminta detail tambahan seperti screenshot atau pesan error, bukan menebak solusi teknis.

--- TUTORIAL PENGGUNAAN APLIKASI (alur asli JobMatch AI, detail lengkap) ---
## Cara Login
Klik tombol "Masuk dengan Google" di halaman awal, pilih akun Google, setujui izin akses (nama dan email). Kamu otomatis masuk ke aplikasi.

## Langkah 1 - Input CV
Upload CV format PDF atau Word (.docx), ukuran maksimal 100MB. Sistem akan mengekstrak teks dari CV untuk dipakai di semua langkah berikutnya.

## Langkah 2 - Lowongan Kerja (ada 4 tab)
- Tab "Dari Dataset (AI Match)": AI mencocokkan CV kamu secara semantik dengan database ratusan lowongan kerja Indonesia, tampil skor kecocokan tiap lowongan.
- Tab "Cari di Internet": dikasih link pencarian siap-klik ke LinkedIn, JobStreet, dan Google Jobs berdasarkan keyword dari CV kamu.
- Tab "Scrape Lowongan Live": mencari lowongan terbaru secara real-time dari internet dan otomatis menambahkannya ke database.
- Tab "Tanya AI (N8N)": chat bebas ke AI Job Assistant yang bisa jawab pertanyaan spesifik soal ANGKA GAJI atau TIPE KERJA (full time/kontrak/dll), karena bisa query database terstruktur - beda dari tab "Dari Dataset" yang cuma cocokkan skill/deskripsi.

## Langkah 3 - Review CV (ada 2 tab)
- Tab "Feedback & Saran": AI analisis CV, kasih skor ATS dan saran perbaikan konkret.
- Tab "Generate CV ATS": AI buatkan versi CV yang ATS-friendly. Bisa pilih bahasa hasil (Otomatis ikut CV asli / Indonesia / Inggris), dan opsional "sesuaikan dengan lowongan spesifik" supaya CV lebih relevan ke satu posisi. Hasil bisa didownload format Word (.docx) atau PDF.

## Langkah 4 - Konsultasi Karir
Chat bebas dengan AI career consultant soal cita-cita, tren industri, estimasi gaji, dan AI bisa mencari lowongan aktif secara real-time di internet kalau diminta.

## Langkah 5 - Mock Interview
AI berperan sebagai HR, tanya 5-7 pertanyaan (campuran behavioral, technical, situational) satu per satu, kasih feedback tiap jawaban. Di akhir sesi, kamu dapat ringkasan skor keseluruhan (format STAR), kelebihan, area perbaikan, dan tips. Saat ini HANYA mode text yang berfungsi - mode voice masih dalam pengembangan, kalau user tanya soal ini jawab jujur belum tersedia.

=== AKHIR REFERENSI PENGETAHUAN ===
"""


def _inject_floating_css(is_open: bool = False, img_b64: str = ""):
    shift_css = ""
    if is_open:
        shift_css = """
        @media (min-width: 1024px) {
            div[data-testid="stAppViewBlockContainer"] {
                margin-right: 360px !important;
                max-width: calc(100% - 360px) !important;
                transition: margin-right 0.3s ease, max-width 0.3s ease;
            }
        }
        """

    avatar_css = ""
    if not is_open and img_b64:
        avatar_css = f"""
        div[data-testid="stVerticalBlock"]:has(div.cs-toggle-marker):not(:has(div[data-testid="stVerticalBlock"]:has(div.cs-toggle-marker))) button {{
            background-image: url('data:image/png;base64,{img_b64}') !important;
            background-size: cover !important;
            background-position: center !important;
            border: 2px solid #ffffff !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        }}
        div[data-testid="stVerticalBlock"]:has(div.cs-toggle-marker):not(:has(div[data-testid="stVerticalBlock"]:has(div.cs-toggle-marker))) button span[data-testid="stIconMaterial"] {{
            display: none !important;
        }}
        """

    st.markdown(
        f"""
        <style>
        div[data-testid="stVerticalBlock"]:has(div.cs-widget-marker):not(:has(div[data-testid="stVerticalBlock"]:has(div.cs-widget-marker))),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(div.cs-widget-marker):not(:has(div[data-testid="stVerticalBlockBorderWrapper"]:has(div.cs-widget-marker))) {{
            position: fixed !important;
            bottom: 85px;
            right: 20px;
            width: 320px;
            max-height: 420px;
            z-index: 9999;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.18);
            padding: 14px 14px 8px 14px;
            overflow-y: auto;
        }}

        div[data-testid="stVerticalBlock"]:has(div.cs-toggle-marker):not(:has(div[data-testid="stVerticalBlock"]:has(div.cs-toggle-marker))),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(div.cs-toggle-marker):not(:has(div[data-testid="stVerticalBlockBorderWrapper"]:has(div.cs-toggle-marker))) {{
            position: fixed !important;
            bottom: 20px;
            right: 20px;
            z-index: 9998;
            width: auto !important;
        }}

        div[data-testid="stVerticalBlock"]:has(div.cs-toggle-marker):not(:has(div[data-testid="stVerticalBlock"]:has(div.cs-toggle-marker))) button {{
            border-radius: 50% !important;
            width: 56px !important;
            height: 56px !important;
            font-size: 22px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.25);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0 !important;
            overflow: hidden !important;
        }}

        div[data-testid="stVerticalBlock"]:has(div.cs-toggle-marker):not(:has(div[data-testid="stVerticalBlock"]:has(div.cs-toggle-marker))) button span[data-testid="stIconMaterial"] {{
            font-size: 26px !important;
        }}

        .cs-header {{
            font-weight: 600;
            font-size: 15px;
            margin-bottom: 6px;
        }}
        {shift_css}
        {avatar_css}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _ask_cs_bot(chat_history: list, user_message: str) -> str:
    if not config.is_gemini_configured():
        return (
            "Maaf, fitur chat CS belum aktif saat ini. "
            "Silakan hubungi tim support kami secara langsung ya."
        )

    try:
        client = config.get_gemini_client()

        contents = []
        for msg in chat_history:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        contents.append({"role": "user", "parts": [{"text": user_message}]})

        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT + "\n- Jawab secara lengkap, tuntas, dan jangan memotong respon di tengah jalan. Pastikan respon kamu selalu selesai dengan tanda titik akhir dan kalimat penutup yang utuh.",
                temperature=0.3,
                top_p=0.9,
                top_k=40,
                max_output_tokens=1000,
            ),
        )
        return response.text

    except Exception:
        return (
            "Maaf, sepertinya ada kendala teknis sesaat. "
            "Coba tanya lagi sebentar lagi ya."
        )


def render_cs_chatbot():
    if "cs_open" not in st.session_state:
        st.session_state.cs_open = False
    if "cs_messages" not in st.session_state:
        st.session_state.cs_messages = []

    import base64
    from pathlib import Path
    img_path = Path(__file__).parent / "assets" / "cs_agent.png"
    img_b64 = ""
    if img_path.exists():
        with open(img_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

    _inject_floating_css(st.session_state.cs_open, img_b64)

    with st.container():
        st.markdown('<div class="cs-toggle-marker"></div>', unsafe_allow_html=True)
        if st.session_state.cs_open:
            btn_clicked = st.button("", icon=":material/close:", key="cs_toggle_btn")
        else:
            btn_clicked = st.button("", icon=":material/support_agent:", key="cs_toggle_btn")
        if btn_clicked:
            st.session_state.cs_open = not st.session_state.cs_open
            st.rerun()

    if st.session_state.cs_open:
        with st.container():
            st.markdown('<div class="cs-widget-marker"></div>', unsafe_allow_html=True)
            
            if img_b64:
                header_html = f"""
                <div class="cs-header" style="display:flex;align-items:center;gap:12px;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid #f1f5f9;">
                    <div style="position:relative;flex-shrink:0;">
                        <img src="data:image/png;base64,{img_b64}" style="width:50px;height:50px;border-radius:50%;object-fit:cover;border:2px solid #e2e8f0;box-shadow:0 2px 8px rgba(0,0,0,0.05);">
                        <div style="position:absolute;bottom:2px;right:0;width:12px;height:12px;background:#10b981;border:2px solid #ffffff;border-radius:50%;"></div>
                    </div>
                    <div>
                        <div style="font-weight:700;color:#0f172a;font-size:1.05rem;line-height:1.2;">Nadia — CS Support</div>
                        <div style="font-size:0.75rem;color:#10b981;font-weight:600;display:flex;align-items:center;gap:4px;">
                            <span>●</span> Online sekarang
                        </div>
                    </div>
                </div>
                """
                st.markdown(header_html, unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="cs-header">💬 Customer Service — JobMatch AI</div>',
                    unsafe_allow_html=True,
                )

            with st.container(height=280):
                for msg in st.session_state.cs_messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            user_input = st.chat_input("Tulis pertanyaanmu...", key="cs_input")

            if user_input:
                st.session_state.cs_messages.append({"role": "user", "content": user_input})
                reply = _ask_cs_bot(st.session_state.cs_messages[:-1], user_input)
                st.session_state.cs_messages.append({"role": "assistant", "content": reply})
                st.rerun()
