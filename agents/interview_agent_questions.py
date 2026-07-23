import random
from typing import Optional
from qdrant_client import QdrantClient, models
import config

COLLECTION_NAME = "interview_questions_bank"
STAR_ORDER = {"Situation": 0, "Task": 1, "Action": 2, "Result": 3}

def get_interview_questions(
    posisi: str,
    jumlah_kompetensi: int = 4,
    client: Optional[QdrantClient] = None,
) -> list[dict]:
    if client is None:
        client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)

    specific = _fetch_by_posisi(client, [posisi])
    umum = _fetch_by_posisi(client, ["Umum"])

    grouped = _group_by_kompetensi(specific + umum)

    if not grouped:
        raise ValueError(
            f"Tidak ada soal wawancara ditemukan untuk posisi={posisi!r} maupun "
            f"kategori 'Umum'. Kemungkinan payload posisi_relevan belum di-set."
        )

    kompetensi_list = list(grouped.keys())
    if len(kompetensi_list) > jumlah_kompetensi:
        selected = random.sample(kompetensi_list, jumlah_kompetensi)
    else:
        selected = kompetensi_list

    session_questions = []
    for komp in selected:
        stages = grouped[komp]
        ordered = dict(sorted(stages.items(), key=lambda kv: STAR_ORDER.get(kv[0], 99)))
        session_questions.append({"kompetensi": komp, "pertanyaan_star": ordered})

    return session_questions


def _fetch_by_posisi(client: QdrantClient, posisi_match: list[str]) -> list[dict]:
    query_filter = models.Filter(
        must=[models.FieldCondition(key="posisi_relevan", match=models.MatchAny(any=posisi_match))]
    )
    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=query_filter,
        with_payload=True,
        limit=200,
    )
    return [p.payload for p in points]


def _group_by_kompetensi(payloads: list[dict]) -> dict[str, dict[str, str]]:
    grouped: dict[str, dict[str, str]] = {}
    for p in payloads:
        komp, tahap, pertanyaan = p.get("kompetensi"), p.get("tahap"), p.get("pertanyaan")
        if not (komp and tahap and pertanyaan):
            continue
        grouped.setdefault(komp, {})[tahap] = pertanyaan
    return grouped
