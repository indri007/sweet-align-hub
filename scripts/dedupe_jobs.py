import json
import os

input_file = "dataset/jobs.jsonl"
output_file = "dataset/jobs_deduped.jsonl"

def dedupe():
    if not os.path.exists(input_file):
        print(f"Error: {input_file} tidak ditemukan.")
        return

    seen = set()
    unique_jobs = []
    duplicates = []

    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                job = json.loads(line)
                # Kunci unik: gabungan job_title, company_name, dan location
                title = job.get('job_title', '').strip().lower()
                company = job.get('company_name', '').strip().lower()
                location = job.get('location', '').strip().lower()
                
                key = f"{title}|{company}|{location}"
                
                if key in seen:
                    duplicates.append(job)
                else:
                    seen.add(key)
                    unique_jobs.append(job)
            except json.JSONDecodeError:
                print(f"Warning: Baris {line_num} bukan JSON valid, dilewati.")
                continue

    print(f"Total baris asli: {len(unique_jobs) + len(duplicates)}")
    print(f"Total baris unik: {len(unique_jobs)}")
    print(f"Total duplikat dihapus: {len(duplicates)}")

    if len(duplicates) > 0:
        # Tulis ulang file dengan data unik
        with open(input_file, 'w', encoding='utf-8') as f:
            for job in unique_jobs:
                f.write(json.dumps(job, ensure_ascii=False) + '\n')
        print(f"Berhasil menimpa {input_file} dengan data yang sudah dibersihkan.")
    else:
        print("Tidak ada duplikat yang ditemukan, file tidak diubah.")

if __name__ == "__main__":
    dedupe()
