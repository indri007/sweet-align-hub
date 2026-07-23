import sys
from database import DatabaseManager, HrdTranscript
import uuid

def main():
    try:
        print("Connecting to DB and checking tables...")
        db = DatabaseManager()
        db.create_tables()
        print("Tables checked/created.")

        test_session_id = f"test_{uuid.uuid4()}"[:36]
        print(f"Testing insert for session {test_session_id}...")
        
        with db.Session() as session:
            new_record = HrdTranscript(
                session_id=test_session_id,
                email="test@example.com",
                posisi="QA Test",
                transcript_json={"messages": ["Halo", "Tes 123"]},
                evaluation_result={"score": 100},
                completed=False
            )
            session.add(new_record)
            session.commit()
            print("Insert successful.")
        
        print("Testing read...")
        with db.Session() as session:
            record = session.query(HrdTranscript).filter_by(session_id=test_session_id).first()
            if record:
                print(f"Read successful: {record.email} - {record.posisi}")
                # Cleanup
                session.delete(record)
                session.commit()
                print("Test record cleaned up.")
            else:
                print("Read failed!")
                sys.exit(1)
        
        print("Verifikasi Streamlit Session ke SQL DB BERHASIL! ✅")
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
