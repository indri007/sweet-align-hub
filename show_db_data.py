import sys
from database import DatabaseManager, Job, HrdTranscript

def main():
    try:
        print("Mengkoneksikan ke database Aiven MySQL...")
        db = DatabaseManager()
        
        with db.Session() as session:
            # Check Jobs table
            jobs_count = session.query(Job).count()
            print(f"\nTotal Data Lowongan Pekerjaan (Jobs): {jobs_count}")
            
            if jobs_count > 0:
                print("--- Sampel 2 Data Lowongan Pekerjaan ---")
                sample_jobs = session.query(Job).limit(2).all()
                for job in sample_jobs:
                    print(f"- Posisi: {job.job_title}")
                    print(f"  Perusahaan: {job.company_name}")
                    print(f"  Lokasi: {job.location}")
                    print(f"  Gaji: {job.salary_raw}")
                    print("  ---")

            # Check Transcripts table
            transcripts_count = session.query(HrdTranscript).count()
            print(f"\nTotal Data Sesi Interview (HRD Transcripts): {transcripts_count}")
            
            if transcripts_count > 0:
                print("--- Sampel Data Sesi Interview ---")
                sample_transcripts = session.query(HrdTranscript).limit(2).all()
                for t in sample_transcripts:
                    print(f"- Email User: {t.email}")
                    print(f"  Posisi yang dilamar: {t.posisi}")
                    print(f"  Selesai: {t.completed}")
                    print(f"  Tanggal: {t.created_at}")
                    print("  ---")
                    
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
