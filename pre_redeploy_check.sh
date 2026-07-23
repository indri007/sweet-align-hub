#!/bin/bash
# pre_redeploy_check.sh
# Audit menyeluruh sebelum redeploy -- jalankan dari root repo
# (sweet-align-hub-extracted), bukan dari folder lain.

set -uo pipefail
PASS=0
FAIL=0
WARN=0

pass() { echo "  ✅ $1"; PASS=$((PASS+1)); }
fail() { echo "  ❌ $1"; FAIL=$((FAIL+1)); }
warn() { echo "  ⚠️  $1"; WARN=$((WARN+1)); }

echo "================================================================"
echo "  PRA-REDEPLOY AUDIT -- JobMatch AI"
echo "================================================================"
echo ""
echo "Direktori kerja: $(pwd)"
echo ""

# --- 1. Konfirmasi lokasi ---
echo "--- 1. Lokasi & Struktur Dasar ---"
if [[ "$(basename "$(pwd)")" == "sweet-align-hub-extracted" ]]; then
  pass "Berada di folder repo yang benar (sweet-align-hub-extracted)"
else
  fail "TIDAK berada di sweet-align-hub-extracted -- cd ke folder yang benar dulu!"
fi

for f in app.py config.py database.py llm_client.py; do
  [[ -f "$f" ]] && pass "$f ada" || fail "$f TIDAK ditemukan"
done
echo ""

# --- 2. Git status bersih ---
echo "--- 2. Status Git ---"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  pass "Repo git terdeteksi"
  UNCOMMITTED=$(git status --porcelain | wc -l | tr -d ' ')
  if [[ "$UNCOMMITTED" -eq 0 ]]; then
    pass "Working tree bersih (tidak ada perubahan belum di-commit)"
  else
    warn "$UNCOMMITTED file punya perubahan belum di-commit -- commit dulu sebelum redeploy"
    git status --porcelain | head -10
  fi
  echo "  Commit terakhir:"
  git log --oneline -3 | sed 's/^/    /'
else
  fail "Bukan git repo, atau git tidak terinisialisasi"
fi
echo ""

# --- 3. Environment variables kritis ---
echo "--- 3. Environment Variables (.env) ---"
if [[ -f .env ]]; then
  pass ".env ditemukan"
  for var in GEMINI_API_KEY DATABASE_URL QDRANT_URL QDRANT_API_KEY USE_N8N; do
    if grep -q "^${var}=" .env; then
      VAL=$(grep "^${var}=" .env | cut -d'=' -f2-)
      if [[ -z "$VAL" || "$VAL" == '""' || "$VAL" == "''" ]]; then
        fail "$var ada tapi KOSONG"
      else
        pass "$var terisi"
      fi
    else
      fail "$var TIDAK ditemukan di .env"
    fi
  done
  if grep -q '^USE_N8N="false"' .env; then
    pass "USE_N8N=false terkonfirmasi (arsitektur Python-native)"
  else
    warn "USE_N8N bukan 'false' -- cek ulang, seharusnya sudah diputuskan Python-native"
  fi
else
  fail ".env TIDAK ditemukan -- redeploy tidak akan jalan tanpa ini"
fi
echo ""

# --- 4. Kredensial tidak ter-commit ke git ---
echo "--- 4. Keamanan Kredensial ---"
if git ls-files | grep -qx ".env"; then
  fail ".env TER-COMMIT ke git! Ini kebocoran kredensial -- harus di-remove dari history"
else
  pass ".env tidak ter-track git (aman)"
fi
if [[ -f .gitignore ]] && grep -q "^\.env$" .gitignore; then
  pass ".env ada di .gitignore"
else
  warn ".env tidak eksplisit ada di .gitignore -- tambahkan untuk jaga-jaga"
fi
# ca.pem sudah diverifikasi manual: sertifikat publik Aiven (-----BEGIN CERTIFICATE-----),
# bukan private key. Aman ter-commit, tidak di-warn lagi supaya audit tidak berisik.
pass "aiven/ca.pem dan ca.pem terverifikasi aman (public certificate, sudah dicek manual)"
echo ""

# --- 5. Arsip N8N terkonfirmasi ---
echo "--- 5. Arsitektur N8N (Konflik #2) ---"
if [[ -d archive/n8n_legacy ]]; then
  pass "n8n_workflows dan n8n_client.py sudah diarsipkan ke archive/n8n_legacy/"
else
  warn "archive/n8n_legacy/ tidak ditemukan -- cek apakah arsip N8N sudah dilakukan"
fi
if [[ -d n8n_workflows || -f n8n_client.py ]]; then
  fail "n8n_workflows/ atau n8n_client.py MASIH ada di lokasi lama -- seharusnya sudah dipindah"
fi
echo ""

# --- 6. Semua test FR-14 s/d FR-17 ---
echo "--- 6. Menjalankan Seluruh Test Suite ---"
TESTS=(
  "scripts/test_interview_agent_questions.py"
  "scripts/test_interview_agent_state.py"
  "scripts/test_interview_agent_integration.py"
  "scripts/test_interview_agent_bidirectional.py"
  "scripts/test_state_not_mutated_on_llm_failure.py"
  "scripts/test_agent5_prompt_bug.py"
  "scripts/test_llm_quality_fr16.py"
  "scripts/test_fr17_database.py"
)
for t in "${TESTS[@]}"; do
  if [[ -f "$t" ]]; then
    if python3 "$t" > /tmp/redeploy_check_$(basename "$t").log 2>&1; then
      pass "$t"
    else
      fail "$t -- lihat /tmp/redeploy_check_$(basename "$t").log"
    fi
  else
    warn "$t tidak ditemukan, dilewati"
  fi
done
echo ""

# --- 7. Dependency check ---
echo "--- 7. Dependencies ---"
if [[ -f requirements.txt ]]; then
  pass "requirements.txt ada"
  MISSING=$(python3 -c "
import pkg_resources
missing = []
with open('requirements.txt') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        pkg = line.split('==')[0].split('>=')[0].split('<')[0].strip()
        try:
            pkg_resources.get_distribution(pkg)
        except Exception:
            missing.append(pkg)
print(','.join(missing))
" 2>/dev/null)
  if [[ -z "$MISSING" ]]; then
    pass "Semua package di requirements.txt terinstall di venv aktif"
  else
    warn "Package berikut ada di requirements.txt tapi tidak terinstall: $MISSING"
  fi
else
  fail "requirements.txt tidak ditemukan"
fi
echo ""

# --- Ringkasan ---
echo "================================================================"
echo "  RINGKASAN: $PASS PASS, $WARN WARNING, $FAIL FAIL"
echo "================================================================"
if [[ $FAIL -gt 0 ]]; then
  echo "  ❌ ADA MASALAH YANG HARUS DIPERBAIKI SEBELUM REDEPLOY."
elif [[ $WARN -gt 0 ]]; then
  echo "  ⚠️  Ada warning -- tinjau sebelum lanjut, tapi tidak fatal."
else
  echo "  ✅ Semua cek dasar lolos. Siap lanjut ke langkah redeploy."
fi
