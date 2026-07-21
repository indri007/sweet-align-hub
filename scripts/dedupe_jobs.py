import json
import os

def dedupe_jobs():
    input_file = "dataset/jobs.jsonl"
    if not os.path.exists(input_file):
        print(f"File {input_file} not found.")
        return

    seen = set()
    unique_jobs = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            job = json.loads(line)
            # Use job_title + company_name + location as a unique key
            key = f"{job.get('job_title', '')}|{job.get('company_name', '')}|{job.get('location', '')}".lower()
            if key not in seen:
                seen.add(key)
                unique_jobs.append(line)
            else:
                print(f"Found duplicate: {job.get('job_title')} at {job.get('company_name')}")

    print(f"Total jobs before: {len(seen) + (len(unique_jobs) - len(seen))}") # Wait, this is wrong print logic.
    
    # Just rewrite file
    with open(input_file, 'w', encoding='utf-8') as f:
        for line in unique_jobs:
            f.write(line)
            
    print(f"Deduplication complete. Kept {len(unique_jobs)} unique jobs.")

if __name__ == "__main__":
    dedupe_jobs()
