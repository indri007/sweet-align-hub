"""
Script perbaikan: ambil lowongan yang ada di database SQL tapi belum
punya vektor di Qdrant, lalu generate vektornya dan masukkan ke Qdrant.
"""
import config
from database import DatabaseManager, Job
from vector_store import VectorStoreManager

def prepare_rag_document(job) -> str:
    parts = [
        f"Job Title: {job.job_title or 'N/A'}",
        f"Company: {job.company_name or 'N/A'}",
        f"Location: {job.location or 'N/A'}",
        f"Work Type: {job.work_type or 'N/A'}",
    ]
    if job.salary_raw and job.salary_raw != "None":
        parts.append(f"Salary: {job.salary_raw}")
    parts.append("")
    parts.append(job.job_description or "")
    return "\n".join(parts)

def main():
    print("EMBEDDING_MODEL aktif:", config.EMBEDDING_MODEL)

    db = DatabaseManager()
    session = db.Session()
    all_jobs = session.query(Job).all()
    session.close()
    print(f"Total lowongan di database SQL: {len(all_jobs)}")

    vs = VectorStoreManager()
    existing_count = vs.get_collection_count()
    print(f"Total data di Qdrant sebelum perbaikan: {existing_count}")

    # Ambil ID yang sudah ada di Qdrant
    existing_ids = set()
    try:
        scroll_result = vs.client.scroll(
            collection_name=config.COLLECTION_NAME,
            limit=10000,
            with_payload=False,
            with_vectors=False,
        )
        points = scroll_result[0]
        for p in points:
            existing_ids.add(str(p.id))
    except Exception as e:
        print("Gagal ambil daftar ID dari Qdrant:", e)
        return

    from vector_store import _stable_point_id
    missing_jobs = []
    for job in all_jobs:
        job_id_str = f"job_{job.id}"
        stable_id = _stable_point_id(job_id_str)
        if stable_id not in existing_ids:
            missing_jobs.append(job)

    print(f"Lowongan yang belum punya vektor: {len(missing_jobs)}")

    if not missing_jobs:
        print("Tidak ada yang perlu diperbaiki.")
        return

    documents, metadatas, ids = [], [], []
    for job in missing_jobs:
        documents.append(prepare_rag_document(job))
        metadatas.append({
            "job_title": job.job_title or "",
            "company_name": job.company_name or "",
            "location": job.location or "",
            "work_type": job.work_type or "",
            "salary": job.salary_raw or "None",
        })
        ids.append(f"job_{job.id}")

    vs.add_documents(documents, metadatas, ids)
    print(f"Berhasil menambahkan {len(missing_jobs)} vektor baru ke Qdrant.")

    final_count = vs.get_collection_count()
    print(f"Total data di Qdrant setelah perbaikan: {final_count}")

if __name__ == "__main__":
    main()
