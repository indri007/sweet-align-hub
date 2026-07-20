content = open("config.py").read()

func_def = '''def _cfg(key, default=""):
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val: return str(val)
    except Exception:
        pass
    return os.getenv(key, default)


'''

# Hapus definisi _cfg() yang ada di posisi salah (di tengah)
old_misplaced = '''
# ─── Google Gemini ────────────────────────────────────────
def _cfg(key, default=""):
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val: return str(val)
    except Exception:
        pass
    return os.getenv(key, default)

'''
new_misplaced = '''
# ─── Google Gemini ────────────────────────────────────────
'''

if old_misplaced not in content:
    print("GAGAL: blok _cfg() lama tidak ketemu persis, cek manual dengan sed -n '15,25p' config.py")
else:
    content = content.replace(old_misplaced, new_misplaced)
    # Sisipkan _cfg() di atas, tepat setelah load_dotenv(...)
    anchor = 'load_dotenv(BASE_DIR / ".env")\n'
    if anchor not in content:
        print("GAGAL: anchor load_dotenv tidak ketemu")
    else:
        content = content.replace(anchor, anchor + "\n" + func_def, 1)
        open("config.py", "w").write(content)
        print("SUKSES: _cfg() dipindah ke atas sebelum dipakai")
