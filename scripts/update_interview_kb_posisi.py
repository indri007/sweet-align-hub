import sys
import os
import argparse

sys.path.insert(0, os.path.abspath("."))

import config
from qdrant_client import QdrantClient, models

COLLECTION_NAME = "interview_questions_bank"

KOMPETENSI_MAP = {
    "Orientasi pada Kualitas Kerja Prima": {
        "kategori_posisi": "Umum",
        "posisi_relevan": ["Umum"],
    },
    "Kemampuan Memecahkan Masalah (Problem Solving)": {
        "kategori_posisi": "Analitis",
        "posisi_relevan": ["Data Analyst", "Software Engineer", "Product Manager", "Umum"],
    },
    "Perencanaan Kerja (Planning)": {
        "kategori_posisi": "Manajerial",
        "posisi_relevan": ["Project Manager", "Product Manager", "Operations", "Umum"],
    },
    "Kerjasama (Teamwork)": {
        "kategori_posisi": "Umum",
        "posisi_relevan": ["Umum"],
    },
    "Inisiatif": {
        "kategori_posisi": "Umum",
        "posisi_relevan": ["Umum"],
    },
    "Leadership": {
        "kategori_posisi": "Manajerial",
        "posisi_relevan": ["Team Lead", "Manager", "Supervisor"],
    },
    "Negosiasi (Negotiation Skills)": {
        "kategori_posisi": "Komersial",
        "posisi_relevan": ["Sales", "Business Development", "Procurement"],
    },
    "Learning Skills": {
        "kategori_posisi": "Umum",
        "posisi_relevan": ["Umum"],
    },
    "Mentoring (Mentor)": {
        "kategori_posisi": "Manajerial",
        "posisi_relevan": ["Senior Staff", "Team Lead", "Manager"],
    },
    "Communication Skills": {
        "kategori_posisi": "Umum",
        "posisi_relevan": ["Umum"],
    },
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Tampilkan rencana update tanpa menulis ke Qdrant")
    args = parser.parse_args()

    client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)

    if not client.collection_exists(COLLECTION_NAME):
        print(f"Collection '{COLLECTION_NAME}' tidak ditemukan. Jalankan build_interview_kb.py dulu.")
        sys.exit(1)

    total_before = client.count(COLLECTION_NAME).count
    print(f"Collection '{COLLECTION_NAME}' berisi {total_before} point.")

    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="kompetensi",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
        import time
        time.sleep(1) # wait for index to be built
    except Exception as e:
        print("Payload index creation note:", e)

    unmapped = []
    updated_count = 0

    for kompetensi, meta in KOMPETENSI_MAP.items():
        query_filter = models.Filter(
            must=[models.FieldCondition(key="kompetensi", match=models.MatchValue(value=kompetensi))]
        )

        match_count = client.count(COLLECTION_NAME, count_filter=query_filter).count
        print(f"  - {kompetensi!r}: {match_count} point cocok -> kategori_posisi={meta['kategori_posisi']!r}, posisi_relevan={meta['posisi_relevan']}")

        if match_count == 0:
            unmapped.append(kompetensi)
            continue

        if not args.dry_run:
            client.set_payload(
                collection_name=COLLECTION_NAME,
                payload={
                    "kategori_posisi": meta["kategori_posisi"],
                    "posisi_relevan": meta["posisi_relevan"],
                },
                points=query_filter,
            )
        updated_count += match_count

    print()
    if args.dry_run:
        print(f"[DRY RUN] Akan meng-update {updated_count} point. Tidak ada perubahan ditulis.")
    else:
        print(f"Selesai. {updated_count} point diperbarui dengan posisi_relevan & kategori_posisi.")

    if unmapped:
        print(f"PERINGATAN: {len(unmapped)} kompetensi di KOMPETENSI_MAP tidak menemukan point yang cocok: {unmapped}")
        print("Cek apakah nama kompetensi di payload persis sama dengan Interview_Questions.json.")

    if not args.dry_run and updated_count > 0:
        sample = client.scroll(COLLECTION_NAME, limit=1, with_payload=True)[0]
        if sample:
            print("\nContoh payload setelah update:")
            print(sample[0].payload)

if __name__ == "__main__":
    main()
