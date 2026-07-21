"""
Patch script: ganti tema warna ke Zoom-blue + tambah efek ikon interaktif
+ avatar profil bergaya Google Account.
Jalankan sekali dari root project (~/cvatsjob).
"""
import re

# ─────────────────────────────────────────────────────────
# 1. Patch styles.css
# ─────────────────────────────────────────────────────────
with open("styles.css", "r") as f:
    css = f.read()

# Ganti blok :root warna lama -> Zoom blue theme
old_root_colors = """    --bg-primary: #f8fafc;
    --bg-secondary: #ffffff;
    --bg-card: #ffffff;
    --bg-card-hover: #f1f5f9;
    --accent-blue: #0f62fe;
    --accent-blue-hover: #0353e9;
    --accent-purple: #8a3ffc;
    --accent-emerald: #198038;
    --accent-amber: #b28600;
    --accent-rose: #da1e28;
    --text-primary: #161616;
    --text-secondary: #525252;
    --text-muted: #8d8d8d;
    --border-color: #dde1e6;
    --glass-bg: rgba(15, 98, 254, 0.05);
    --shadow-glow: 0 4px 24px rgba(15, 98, 254, 0.08);
    --gradient-primary: linear-gradient(135deg, #0f62fe, #002d9c);
    --gradient-success: linear-gradient(135deg, #24a148, #198038);
    --gradient-warm: linear-gradient(135deg, #f1c21b, #da1e28);"""

new_root_colors = """    --bg-primary: #f8fafc;
    --bg-secondary: #ffffff;
    --bg-card: #ffffff;
    --bg-card-hover: #eef5ff;
    --accent-blue: #2D8CFF;
    --accent-blue-rgb: 45, 140, 255;
    --accent-blue-hover: #0B5CFF;
    --accent-purple: #8a3ffc;
    --accent-emerald: #198038;
    --accent-amber: #b28600;
    --accent-rose: #da1e28;
    --text-primary: #161616;
    --text-secondary: #525252;
    --text-muted: #8d8d8d;
    --border-color: #dde1e6;
    --glass-bg: rgba(45, 140, 255, 0.06);
    --shadow-glow: 0 4px 24px rgba(45, 140, 255, 0.15);
    --gradient-primary: linear-gradient(135deg, #2D8CFF, #0B5CFF);
    --gradient-success: linear-gradient(135deg, #24a148, #198038);
    --gradient-warm: linear-gradient(135deg, #f1c21b, #da1e28);"""

if old_root_colors in css:
    css = css.replace(old_root_colors, new_root_colors, 1)
    print("OK: :root color palette diganti ke Zoom blue.")
else:
    print("WARNING: blok :root lama tidak ditemukan persis - cek manual.")

# Perbaiki semua rgba(0, 212, 255, X) (cyan lama, tidak konsisten) -> pakai var baru
def fix_rgba(match):
    alpha = match.group(1)
    return f"rgba(var(--accent-blue-rgb), {alpha})"

css, n = re.subn(r"rgba\(0,\s*212,\s*255,\s*([0-9.]+)\)", fix_rgba, css)
print(f"OK: {n} kemunculan rgba(0,212,255,x) lama diganti ke var(--accent-blue-rgb).")

# Tambahkan CSS baru: ikon interaktif + avatar profil, di akhir file
extra_css = """

/* ── Interactive Step Icons (Sidebar Nav) ────────────────── */
.step-item .step-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 1.15rem;
    margin-right: 10px;
    transition: transform 0.25s ease, filter 0.25s ease;
}

.step-item:hover .step-icon {
    transform: scale(1.18) rotate(-4deg);
    filter: drop-shadow(0 2px 6px rgba(var(--accent-blue-rgb), 0.45));
}

.step-item.active .step-icon {
    transform: scale(1.1);
    filter: drop-shadow(0 2px 8px rgba(var(--accent-blue-rgb), 0.55));
}

/* ── Google-style Profile Avatar ──────────────────────────── */
.gauth-avatar-wrap {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(var(--accent-blue-rgb), 0.06);
    border: 1px solid rgba(var(--accent-blue-rgb), 0.18);
    transition: all 0.25s ease;
    width: fit-content;
}

.gauth-avatar-wrap:hover {
    background: rgba(var(--accent-blue-rgb), 0.12);
    box-shadow: 0 2px 12px rgba(var(--accent-blue-rgb), 0.25);
}

.gauth-avatar-img {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid var(--accent-blue);
    box-shadow: 0 0 0 3px rgba(var(--accent-blue-rgb), 0.15);
    transition: box-shadow 0.25s ease;
}

.gauth-avatar-wrap:hover .gauth-avatar-img {
    box-shadow: 0 0 0 4px rgba(var(--accent-blue-rgb), 0.3);
}

.gauth-avatar-name {
    font-weight: 600;
    font-size: 0.92rem;
    color: var(--text-primary);
}
"""

if ".gauth-avatar-wrap" not in css:
    css += extra_css
    print("OK: CSS ikon interaktif + avatar profil ditambahkan.")
else:
    print("SKIP: CSS avatar sudah ada sebelumnya, tidak ditambah lagi.")

with open("styles.css", "w") as f:
    f.write(css)

# ─────────────────────────────────────────────────────────
# 2. Patch nav.py: bungkus icon dengan span class="step-icon"
#    (opsional info saja - nav.py generate HTML di app.py/nav.py,
#     kita cek dulu apakah ada tempat render step-item)
# ─────────────────────────────────────────────────────────
print("\nCatatan: pastikan HTML step-item di nav.py/app.py membungkus")
print("emoji ikon dengan <span class='step-icon'>...</span> agar")
print("efek hover ikon di atas aktif. Cek manual jika belum.")

# ─────────────────────────────────────────────────────────
# 3. Patch auth_setup.py: ganti st.image polos -> avatar bergaya Google
# ─────────────────────────────────────────────────────────
with open("auth_setup.py", "r") as f:
    auth = f.read()

old_badge = '''        picture = getattr(st.user, "picture", None)
        if picture:
            target.image(picture, width=32)
        target.markdown(f"**👋 {name}**")'''

new_badge = '''        picture = getattr(st.user, "picture", None)
        if picture:
            target.markdown(
                f"""
                <div class="gauth-avatar-wrap">
                    <img class="gauth-avatar-img" src="{picture}" />
                    <span class="gauth-avatar-name">👋 {name}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            target.markdown(f"**👋 {name}**")'''

if old_badge in auth:
    auth = auth.replace(old_badge, new_badge, 1)
    with open("auth_setup.py", "w") as f:
        f.write(auth)
    print("OK: auth_setup.py - avatar profil diganti ke gaya Google Account.")
elif "gauth-avatar-wrap" in auth:
    print("SKIP: auth_setup.py sudah dipatch sebelumnya.")
else:
    print("WARNING: blok badge lama di auth_setup.py tidak ditemukan persis - cek manual.")

print("\n=== SELESAI ===")
