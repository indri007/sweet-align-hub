import sys

file_path = "/Users/jevin/Downloads/sweet-align-hub-main/auth_setup.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Let's locate the index directly to avoid string matching issues
lines = content.splitlines()

start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if "# ─── Final CTA ───" in line:
        start_idx = i
    if "st.login(\"google\")" in line and start_idx is not None and i > start_idx and end_idx is None:
        # Check if the next non-empty line or surrounding lines indicate it's the end of the button block
        end_idx = i + 1

if start_idx is not None and end_idx is not None:
    new_cta_lines = [
        "        # ─── Final CTA ───",
        "        st.markdown(",
        "            \"\"\"",
        "            <div style=\"max-width:960px;margin:40px auto 30px auto;padding:0 20px;font-family:\'Inter\',sans-serif;\">",
        "                <div style=\"background:#0f172a;border-radius:32px;padding:60px 40px;text-align:center;position:relative;overflow:hidden;\">",
        "                    <div style=\"position:absolute;top:0;right:0;width:250px;height:250px;background:#4285F4;opacity:0.12;border-radius:50%;filter:blur(80px);\"></div>",
        "                    <div style=\"position:absolute;bottom:0;left:0;width:250px;height:250px;background:#34A853;opacity:0.12;border-radius:50%;filter:blur(80px);\"></div>",
        "                    <h2 style=\"font-size:2.4rem;font-weight:800;color:white;margin:0 0 14px 0;position:relative;letter-spacing:-0.02em;\">Stop Guessing Why Your CV Gets Rejected</h2>",
        "                    <p style=\"color:#94a3b8;font-size:1.1rem;max-width:560px;margin:0 auto 20px auto;line-height:1.65;position:relative;\">Ribuan job seekers udah pakai JobMatch AI buat pass first screening.</p>",
        "                </div>",
        "            </div>",
        "            \"\"\",",
        "            unsafe_allow_html=True,",
        "        )",
        "        _cta1, _cta_b1, _cta_b2, _cta3 = st.columns([0.8, 1.2, 1.3, 0.8])",
        "        with _cta_b1:",
        "            if st.button(\"Start Free Now  →\", type=\"primary\", use_container_width=True, key=\"final_cta_btn\"):",
        "                st.login(\"google\")",
        "        with _cta_b2:",
        "            if st.button(\"Sign in with Google\", type=\"secondary\", use_container_width=True, key=\"final_google_btn\", icon=\":material/login:\"):",
        "                st.login(\"google\")",
        "",
        "        st.markdown(",
        "            \"\"\"",
        "            <div style=\"text-align:center;margin-top:16px;margin-bottom:40px;font-family:\'Inter\',sans-serif;color:#64748b;font-size:0.88rem;\">",
        "                Start for free · No credit card required",
        "            </div>",
        "            \"\"\",",
        "            unsafe_allow_html=True,",
        "        )"
    ]
    
    lines[start_idx:end_idx] = new_cta_lines
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("Success index-based replacement")
else:
    print(f"Indices not found. start: {start_idx}, end: {end_idx}")
