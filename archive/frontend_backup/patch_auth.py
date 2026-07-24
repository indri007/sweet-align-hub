import re

with open("auth_setup.py", "r") as f:
    content = f.read()

new_block = '''def _get_secret(key: str) -> str:
    """Baca dari st.secrets dulu (Streamlit Cloud), fallback ke os.environ (lokal)."""
    try:
        if key in st.secrets:
            val = st.secrets[key]
            if val:
                return str(val)
    except Exception:
        pass
    return os.environ.get(key, "")


def _inject_auth_secrets():
    redirect_uri = _get_secret("AUTH_REDIRECT_URI")
    cookie_secret = _get_secret("AUTH_COOKIE_SECRET")
    client_id = _get_secret("GOOGLE_CLIENT_ID")
    client_secret = _get_secret("GOOGLE_CLIENT_SECRET")
    missing = [
        name
        for name, val in [
            ("AUTH_REDIRECT_URI", redirect_uri),
            ("AUTH_COOKIE_SECRET", cookie_secret),
            ("GOOGLE_CLIENT_ID", client_id),
            ("GOOGLE_CLIENT_SECRET", client_secret),
        ]
        if not val
    ]
    if missing:
        return False, missing
    secrets_singleton._secrets = {
        "auth": {
            "redirect_uri": redirect_uri,
            "cookie_secret": cookie_secret,
            "google": {
                "client_id": client_id,
                "client_secret": client_secret,
                "server_metadata_url": _GOOGLE_METADATA_URL,
            }
        }
    }
    return True, []


'''

pattern = re.compile(
    r"def _inject_auth_secrets\(\):.*?return True, \[\]\s*\n+(?=def require_google_login)",
    re.DOTALL,
)

new_content, n = pattern.subn(new_block, content)

if n == 0:
    print("GAGAL: pattern regex tidak match. Cek manual.")
elif n > 1:
    print(f"WARNING: match {n} kali, seharusnya cuma 1. Tidak ditulis, cek manual dulu.")
else:
    with open("auth_setup.py", "w") as f:
        f.write(new_content)
    print("SUKSES: fungsi berhasil di-patch dengan regex.")
