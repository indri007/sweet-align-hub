"""
Customer Service Chatbot Module - JobMatch AI (Floating Widget)
Terintegrasi ke dalam arsitektur `core/` dengan Persona CS Manager 15 Tahun.
"""

import streamlit as st
from google.genai import types

# Modifikasi: Kita ubah SYSTEM_PROMPT menjadi fungsi agar bisa dinamis menyuntikkan status sistem
def get_dynamic_system_prompt(system_health_status: dict) -> str:
    """
    Menghasilkan prompt sistem yang dinamis berdasarkan status layanan terkini.
    system_health_status berupa dict { "gemini": "ok"/"down", "qdrant": "ok"/"down", "mysql": "ok"/"down" }
    """
    
    status_text = f"""
[STATUS SISTEM REAL-TIME]
Gemini AI (Otak Utama/Generasi): {system_health_status.get('gemini', 'ok').upper()}
Qdrant (Mesin Pencari Lowongan): {system_health_status.get('qdrant', 'ok').upper()}
MySQL (Database Profil): {system_health_status.get('mysql', 'ok').upper()}

PENTING: Jika status di atas BUKAN 'OK' dan pengguna menanyakan kendala fitur terkait, kamu HARUS jujur mengatakan bahwa sistem tersebut sedang mengalami gangguan dan tim sedang memperbaikinya. JANGAN berpura-pura fitur tersebut berjalan normal!
"""

    return f"""
Kamu adalah Leonardo, Senior CS Manager JobMatch AI dengan 15 tahun pengalaman di bidang Customer Success HR-Tech.

FONDASI UTAMA KAMU:
1. Product Knowledge Depth:
   - Kamu paham bahwa CV Builder menggunakan Gemini Vision OCR untuk membaca CV berupa gambar/scan.
   - Kamu paham bahwa Mock Interview berbasis text, dan ATS Score adalah estimasi kecerdasan buatan, BUKAN jaminan pasti lolos filter ATS perusahaan sesungguhnya.
2. Troubleshooting Flow:
   - Kamu bisa menjawab langsung pertanyaan panduan.
   - Kamu tahu status sistem saat ini (baca bagian Status Sistem di bawah).
   - Jika ada kendala yang tidak bisa kamu selesaikan, segera lakukan eskalasi ke Tim Support (human handoff).
3. Tone & Boundary:
   - Empatik namun efisien (to-the-point).
   - JANGAN pernah menjanjikan hal (overclaim) seperti "CV ini dijamin lolos kerja".
   - Jika di luar konteks, katakan: "Maaf, itu di luar keahlianku, tapi untuk urusan JobMatch AI aku siap bantu!".
4. Data Privacy:
   - Kamu berinteraksi dengan pengguna saat ini secara 1-on-1. Jangan pernah membocorkan/mengarang data user lain.

CAKUPAN BANTUAN KAMU (4 Area):
1. TUTORIAL — Cara upload CV (PDF/Word maks 10MB), alur wizard (Upload -> Lowongan -> Review -> Mock Interview), cara login.
2. GLOSSARY — Istilah teknis (ATS, RAG, Semantic Search) disederhanakan. Istilah HR (Probation, Notice Period, UMR). Jika tidak tahu, jujur katakan tidak tahu.
3. FITUR — Review CV, Rekomendasi Semantic, Generate CV ATS, Konsultasi, Mock Interview.
4. BENEFIT — Penjelasan logis (bukan iklan) mengapa fitur ini berguna.

=== ILMU TAMBAHAN (DARI PANDUAN QDRANT) ===
{system_health_status.get('rag_context', 'Belum ada panduan tambahan.')}

=== KENANGAN MASA LALU (PENGALAMAN DARI USER LAIN) ===
{system_health_status.get('memory_context', 'Belum ada kenangan masa lalu.')}

{status_text}

ATURAN UTAMA:
- Jawab HANYA seputar aplikasi dan HR. Hindari coding/arsitektur detail.
- Jawab maksimal 3-4 kalimat ringkas (bullet points disarankan jika langkahnya panjang).
- Default Bahasa Indonesia, kecuali ditanya dalam Bahasa Inggris.

=== REFERENSI PENGETAHUAN KEMARIN ===
- ATS: sistem software HRD untuk filter CV.
- STAR Method: Situation, Task, Action, Result untuk wawancara.
- Jika upload gagal: pastikan format file PDF/DOCX bukan gambar biasa, dan ukuran di bawah batas.
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
        div[data-testid="stElementContainer"]:has(.cs-toggle-marker) + div[data-testid="stElementContainer"] button {{
            background-image: url('data:image/png;base64,{img_b64}') !important;
            background-size: cover !important;
            background-position: center !important;
            border: 2px solid #ffffff !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        }}
        div[data-testid="stElementContainer"]:has(.cs-toggle-marker) + div[data-testid="stElementContainer"] button * {{
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
            background: var(--md-surface) !important;
            border-radius: var(--md-shape-card) !important;
            box-shadow: var(--md-elevation-2) !important;
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

        div[data-testid="stElementContainer"]:has(.cs-toggle-marker) + div[data-testid="stElementContainer"] button {{
            border-radius: 50% !important;
            width: 56px !important;
            height: 56px !important;
            font-size: 22px;
            box-shadow: var(--md-elevation-2) !important;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0 !important;
            overflow: hidden !important;
            background-color: var(--md-primary) !important;
            color: var(--md-on-primary) !important;
        }}

        div[data-testid="stElementContainer"]:has(.cs-toggle-marker) + div[data-testid="stElementContainer"] button * {{
            opacity: 0 !important; 
            display: none !important;
        }}

        .cs-header {{
            font-weight: 600;
            font-size: 15px;
            margin-bottom: 6px;
            color: var(--md-on-surface);
        }}
        {shift_css}
        {avatar_css}
        </style>
        """,
        unsafe_allow_html=True,
    )

def _ask_cs_bot(chat_history: list, user_message: str, gemini_client, system_health: dict) -> str:
    if not gemini_client:
        return "Maaf, sistem AI utama sedang tidak tersedia untuk sementara waktu."

    try:
        contents = []
        for msg in chat_history:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        contents.append({"role": "user", "parts": [{"text": user_message}]})

        # RAG: Fetch CS Knowledge and CS Memory from Qdrant
        import config
        from vector_store import VectorStoreManager
        
        cs_store = VectorStoreManager(collection_name=config.CS_KNOWLEDGE_COLLECTION)
        cs_memory = VectorStoreManager(collection_name=config.CS_MEMORY_COLLECTION)
        
        cs_knowledge_chunks = cs_store.search_similar_jobs(user_message, top_k=2)
        cs_memory_chunks = cs_memory.search_similar_jobs(user_message, top_k=2)
        
        rag_context = "\n".join([chunk["document"] for chunk in cs_knowledge_chunks]) if cs_knowledge_chunks else "Tidak ada panduan relevan dari knowledge base."
        memory_context = "\n".join([chunk["document"] for chunk in cs_memory_chunks]) if cs_memory_chunks else "Tidak ada memori dari pengalaman masa lalu."
        
        system_health["rag_context"] = rag_context
        system_health["memory_context"] = memory_context

        # Inject real-time status and RAG context
        active_system_prompt = get_dynamic_system_prompt(system_health)

        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=active_system_prompt,
                temperature=0.3,
                top_p=0.9,
                top_k=40,
                max_output_tokens=1000,
            ),
        )
        reply = response.text
        
        # Fire-and-forget thread to save memory
        import threading
        import uuid
        def _save_memory():
            try:
                interaction = f"User bertanya: {user_message}\nLeonardo menjawab: {reply}"
                cs_memory.add_documents(
                    documents=[interaction],
                    metadatas=[{"source": "cs_chat_history"}],
                    ids=[str(uuid.uuid4())]
                )
            except Exception as e:
                print(f"[Memory] Gagal menyimpan kenangan Leonardo: {e}")
        threading.Thread(target=_save_memory, daemon=True).start()

        return reply

    except Exception as e:
        print(f"[Chatbot] Error: {e}")
        return "Leonardo mengalami kendala jaringan (koneksi LLM putus). Coba tanyakan lagi dalam beberapa detik ya."

def render_cs_chatbot(gemini_client, system_health_status: dict = None):
    """
    Renders the floating customer service widget.
    Dipanggil dari app.py atau ui_components.py
    system_health_status: Hasil check real-time dari modul core/health.py
    """
    if system_health_status is None:
        system_health_status = {"gemini": "ok", "qdrant": "ok", "mysql": "ok"}
        
    if "cs_open" not in st.session_state:
        st.session_state.cs_open = False
    if "cs_messages" not in st.session_state:
        st.session_state.cs_messages = []

    import base64
    from pathlib import Path
    img_path = Path(__file__).parent.parent / "assets" / "cs_agent.png"
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
                <div class="cs-header" style="display:flex;align-items:center;gap:12px;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid var(--md-outline);">
                    <div style="position:relative;flex-shrink:0;">
                        <img src="data:image/png;base64,{img_b64}" style="width:50px;height:50px;border-radius:50%;object-fit:cover;border:2px solid var(--md-surface);box-shadow:var(--md-elevation-1);">
                        <div style="position:absolute;bottom:2px;right:0;width:12px;height:12px;background:var(--md-success);border:2px solid var(--md-surface);border-radius:50%;"></div>
                    </div>
                    <div>
                        <div style="font-weight:700;color:var(--md-on-surface);font-size:1.05rem;line-height:1.2;">Leonardo — Senior CS</div>
                        <div style="font-size:0.75rem;color:var(--md-success);font-weight:600;display:flex;align-items:center;gap:4px;">
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
                reply = _ask_cs_bot(st.session_state.cs_messages[:-1], user_input, gemini_client, system_health_status)
                st.session_state.cs_messages.append({"role": "assistant", "content": reply})
                st.rerun()
