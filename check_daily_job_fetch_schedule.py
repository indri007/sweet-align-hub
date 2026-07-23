#!/usr/bin/env python3
"""
check_daily_job_fetch_schedule.py

Cek apakah Cloud Run Job "daily-job-fetch" benar-benar dijadwalkan jalan
setiap hari jam 9 pagi, dan pastikan "konektornya" (Cloud Scheduler ->
Cloud Run Job) berfungsi dengan baik.

Yang dicek:
1. Cloud Scheduler job yang men-trigger "daily-job-fetch" - jadwal cron,
   timezone, status aktif/paused, dan target (harus mengarah ke job yang
   benar).
2. Riwayat eksekusi Cloud Run Job - kapan terakhir jalan, sukses/gagal,
   dan apakah jam-nya konsisten dengan jadwal yang diharapkan.
3. (Opsional) Trigger eksekusi manual untuk test koneksi end-to-end,
   HANYA jika user mengonfirmasi dengan flag --trigger-test.

PENTING - jalankan di laptop Anda sendiri (Kiro / terminal Mac), bukan di
sandbox Claude, karena butuh `gcloud` CLI yang sudah login ke akun & project
GCP Anda.

Cara pakai:
    # Cek jadwal & riwayat eksekusi saja (read-only, aman)
    python3 check_daily_job_fetch_schedule.py

    # Cek jadwal + langsung trigger 1x eksekusi manual untuk test koneksi
    # (ini AKAN benar-benar menjalankan job, pakai quota JSearch API asli)
    python3 check_daily_job_fetch_schedule.py --trigger-test

    # Custom job/region/project
    python3 check_daily_job_fetch_schedule.py --job daily-job-fetch \
        --region asia-southeast2 --project heaven-493814
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

DEFAULT_PROJECT = "heaven-493814"
DEFAULT_REGION = "asia-southeast2"
DEFAULT_JOB = "daily-job-fetch"
EXPECTED_HOUR = 9  # jam 9 pagi yang diharapkan
JAKARTA_TZ = ZoneInfo("Asia/Jakarta")


def run_gcloud_json(cmd: list[str]):
    """Jalankan gcloud command dengan --format=json, kembalikan hasil parse."""
    full_cmd = cmd + ["--format=json"]
    proc = subprocess.run(full_cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return None, proc.stderr.strip()
    try:
        return json.loads(proc.stdout) if proc.stdout.strip() else [], None
    except json.JSONDecodeError as e:
        return None, f"Gagal parse JSON: {e}"


def check_gcloud_available():
    import shutil
    if shutil.which("gcloud") is None:
        print("❌ gcloud CLI tidak ditemukan. Install dulu / pastikan sudah login.")
        sys.exit(1)


def find_scheduler_jobs(project: str, job_name: str, location: str):
    """Cari semua Cloud Scheduler job yang target-nya mengarah ke Cloud Run Job ini.

    Cloud Scheduler itu resource per-lokasi (beda dengan Cloud Run yang
    pakai --region tapi listable lintas region dalam 1 project), jadi kalau
    tidak ketemu di 'location' yang diberikan, coba juga lokasi lain yang
    umum dipakai supaya tidak salah simpul cuma karena beda lokasi.
    """
    print(f"[1/3] Mencari Cloud Scheduler job yang men-trigger '{job_name}' ...")

    locations_to_try = [location]
    for fallback_loc in ["asia-southeast1", "asia-southeast2", "us-central1"]:
        if fallback_loc not in locations_to_try:
            locations_to_try.append(fallback_loc)

    all_matches = []
    for loc in locations_to_try:
        data, err = run_gcloud_json([
            "gcloud", "scheduler", "jobs", "list",
            "--project", project,
            "--location", loc,
        ])
        if err:
            print(f"      ⚠️  [{loc}] Gagal ambil daftar scheduler job: {err}")
            continue

        if not data:
            print(f"      [{loc}] Tidak ada scheduler job sama sekali di lokasi ini.")
            continue

        matches = []
        for j in data:
            uri = ""
            if "httpTarget" in j:
                uri = j["httpTarget"].get("uri", "")
            blob = json.dumps(j)
            if job_name in uri or job_name in blob:
                matches.append(j)

        if matches:
            print(f"      ✅ [{loc}] Ditemukan {len(matches)} scheduler job yang match.")
            all_matches.extend(matches)
        else:
            print(f"      [{loc}] Ada {len(data)} scheduler job, tapi tidak ada yang "
                  f"match nama '{job_name}':")
            for j in data:
                print(f"        - {j.get('name', '?').rsplit('/', 1)[-1]} "
                      f"(schedule: {j.get('schedule', '?')}, state: {j.get('state', '?')})")

    return all_matches

    matches = []
    for j in data:
        # Target URI biasanya mengandung nama job Cloud Run
        uri = ""
        if "httpTarget" in j:
            uri = j["httpTarget"].get("uri", "")
        blob = json.dumps(j)
        if job_name in uri or job_name in blob:
            matches.append(j)

    if not matches:
        print(f"      ⚠️  Tidak ada Cloud Scheduler job yang match nama '{job_name}'.")
        print("      Semua scheduler job yang ada di project ini:")
        for j in data:
            print(f"        - {j.get('name', '?').rsplit('/', 1)[-1]} "
                  f"(schedule: {j.get('schedule', '?')}, state: {j.get('state', '?')})")
    return matches


def describe_scheduler_job(match: dict):
    name = match.get("name", "?").rsplit("/", 1)[-1]
    schedule = match.get("schedule", "?")
    tz = match.get("timeZone", "UTC")
    state = match.get("state", "?")

    print(f"\n      📅 Scheduler job: {name}")
    print(f"         Cron schedule : {schedule}")
    print(f"         Timezone      : {tz}")
    print(f"         Status        : {state}")

    # Parse cron sederhana: menit jam * * * -> cek apakah jam == EXPECTED_HOUR
    parts = schedule.split()
    if len(parts) >= 2:
        minute, hour = parts[0], parts[1]
        try:
            hour_int = int(hour)
            if hour_int == EXPECTED_HOUR:
                print(f"         ✅ Jadwal jalan jam {hour}:{minute.zfill(2)} "
                      f"({tz}) - sesuai target jam {EXPECTED_HOUR} pagi.")
            else:
                print(f"         ⚠️  Jadwal jalan jam {hour}:{minute.zfill(2)} "
                      f"({tz}) - BUKAN jam {EXPECTED_HOUR} seperti yang diharapkan.")
        except ValueError:
            print(f"         ℹ️  Format jam tidak standar ({hour}), cek manual: {schedule}")

    if state != "ENABLED":
        print(f"         🚨 Status scheduler bukan ENABLED (saat ini: {state}) "
              f"- job TIDAK akan jalan otomatis!")

    return schedule, tz, state


def list_executions(project: str, region: str, job_name: str, limit: int = 10):
    print(f"\n[2/3] Mengambil riwayat eksekusi Cloud Run Job '{job_name}' "
          f"(region: {region}) ...")
    data, err = run_gcloud_json([
        "gcloud", "run", "jobs", "executions", "list",
        "--job", job_name,
        "--region", region,
        "--project", project,
        "--limit", str(limit),
    ])
    if err:
        print(f"      ⚠️  Gagal ambil riwayat eksekusi: {err}")
        return []
    return data


def summarize_executions(executions: list):
    if not executions:
        print("      Tidak ada riwayat eksekusi ditemukan.")
        return

    print(f"      Ditemukan {len(executions)} eksekusi terakhir:\n")
    print(f"      {'Waktu mulai (Jakarta)':<24} {'Status':<10} {'Durasi'}")
    print(f"      {'-'*24} {'-'*10} {'-'*10}")

    for ex in executions:
        status = ex.get("status", {})
        conditions = status.get("conditions", [])
        succeeded = any(
            c.get("type") == "Completed" and c.get("status") == "True"
            for c in conditions
        )
        failed = any(
            c.get("type") == "Completed" and c.get("status") == "False"
            for c in conditions
        )
        state = "✅ SUKSES" if succeeded else ("❌ GAGAL" if failed else "⏳ ?")

        start_time_str = status.get("startTime") or ex.get("metadata", {}).get("creationTimestamp")
        completion_time_str = status.get("completionTime")

        start_local = "-"
        duration = "-"
        if start_time_str:
            try:
                start_dt = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                start_local_dt = start_dt.astimezone(JAKARTA_TZ)
                start_local = start_local_dt.strftime("%Y-%m-%d %H:%M:%S")
                if completion_time_str:
                    end_dt = datetime.fromisoformat(completion_time_str.replace("Z", "+00:00"))
                    duration = str(end_dt - start_dt).split(".")[0]
            except (ValueError, TypeError):
                pass

        print(f"      {start_local:<24} {state:<10} {duration}")


def check_consistency(executions: list):
    """Cek apakah eksekusi terjadi konsisten sekitar jam 9 pagi tiap hari."""
    if not executions:
        return

    print("\n      Analisis konsistensi jadwal:")
    hours_seen = []
    for ex in executions:
        status = ex.get("status", {})
        start_time_str = status.get("startTime") or ex.get("metadata", {}).get("creationTimestamp")
        if not start_time_str:
            continue
        try:
            start_dt = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            start_local = start_dt.astimezone(JAKARTA_TZ)
            hours_seen.append(start_local.hour)
        except (ValueError, TypeError):
            continue

    if not hours_seen:
        print("      Tidak cukup data untuk analisis.")
        return

    consistent = all(abs(h - EXPECTED_HOUR) <= 1 for h in hours_seen)
    if consistent:
        print(f"      ✅ Semua eksekusi terjadi di sekitar jam {EXPECTED_HOUR} pagi "
              f"(WIB) - jadwal berjalan konsisten.")
    else:
        distinct_hours = sorted(set(hours_seen))
        print(f"      ⚠️  Jam eksekusi bervariasi: {distinct_hours} (WIB) - "
              f"tidak konsisten dengan target jam {EXPECTED_HOUR} pagi.")


def trigger_test_execution(project: str, region: str, job_name: str):
    print(f"\n[3/3] Trigger eksekusi manual untuk test koneksi end-to-end ...")
    print("      ⚠️  Ini akan benar-benar menjalankan job (memakai quota API asli).")
    confirm = input("      Ketik 'ya' untuk lanjut, atau Enter untuk batal: ").strip().lower()
    if confirm != "ya":
        print("      Dibatalkan.")
        return

    proc = subprocess.run([
        "gcloud", "run", "jobs", "execute", job_name,
        "--region", region,
        "--project", project,
        "--wait",
    ], capture_output=True, text=True)

    print(proc.stdout)
    if proc.returncode == 0:
        print("      ✅ Eksekusi manual berhasil - konektor Cloud Scheduler → "
              "Cloud Run Job berfungsi normal.")
    else:
        print(f"      ❌ Eksekusi manual gagal:\n{proc.stderr}")


def main():
    global EXPECTED_HOUR

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--job", default=DEFAULT_JOB)
    parser.add_argument("--expected-hour", type=int, default=EXPECTED_HOUR)
    parser.add_argument("--limit", type=int, default=10,
                         help="Jumlah riwayat eksekusi terakhir yang dicek.")
    parser.add_argument("--trigger-test", action="store_true",
                         help="Trigger 1x eksekusi manual untuk test koneksi (butuh konfirmasi).")
    args = parser.parse_args()

    EXPECTED_HOUR = args.expected_hour

    check_gcloud_available()

    print("=" * 60)
    print(f"CEK JADWAL & KONEKTOR: Cloud Run Job '{args.job}'")
    print("=" * 60)

    scheduler_matches = find_scheduler_jobs(args.project, args.job, args.region)
    for m in scheduler_matches:
        describe_scheduler_job(m)
    if not scheduler_matches:
        print("\n      🚨 TIDAK ADA Cloud Scheduler job yang mengarah ke "
              f"'{args.job}' di lokasi manapun yang dicek.")
        print("      Artinya job ini kemungkinan besar TIDAK dijadwalkan "
              "jalan otomatis sama sekali - trigger-nya harus dicari manual")
        print("      (bisa jadi Cloud Tasks, Workflows, cron eksternal, atau "
              "memang belum pernah di-setup).")

    executions = list_executions(args.project, args.region, args.job, args.limit)
    summarize_executions(executions)
    check_consistency(executions)

    if not executions:
        print("\n      🚨 RIWAYAT EKSEKUSI KOSONG - job ini belum pernah "
              "dijalankan sama sekali (baik manual maupun otomatis).")
        print("      Ini konsisten dengan tidak ditemukannya Cloud Scheduler "
              "trigger di atas.")
        print("      Data di Dataset/jobs.jsonl (473 record) BUKAN berasal "
              "dari eksekusi job ini - itu hasil run manual scraper.py "
              "yang berbeda mekanisme.")

    if args.trigger_test:
        trigger_test_execution(args.project, args.region, args.job)

    print("\n" + "=" * 60)
    print("Selesai.")
    print("=" * 60)


if __name__ == "__main__":
    main()
