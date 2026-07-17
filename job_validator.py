"""
job_validator.py

Validasi & deteksi record fallback/sintetis untuk job listings.
Diekstrak dari verify_daily_job_fetch_backup.py dan disesuaikan untuk
dipakai di scraper.py, daily_fetch.py, dan modul lain.

Fungsi utama:
    is_fallback_record(job)   → True kalau job terdeteksi sintetis
    validate_job(job)         → (is_valid, missing_fields)
    validate_batch(jobs)      → ValidationResult (summary lengkap)
    filter_real_jobs(jobs)    → list job yang lolos validasi & bukan fallback
"""

import re
import time
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ─── Field wajib di setiap record ────────────────────────────────────────────
REQUIRED_FIELDS = {
    "job_title",
    "company_name",
    "location",
    "work_type",
    "job_description",
    "_scrape_timestamp",
}

# ─── Pola kalimat template dari fallback generator di scraper.py ─────────────
# Kalau job_description match salah satu pola ini → kemungkinan besar sintetis
FALLBACK_PATTERNS: list[re.Pattern] = [
    re.compile(
        r"Kami mencari .+ berbakat untuk bergabung dengan tim kami",
        re.IGNORECASE,
    ),
    re.compile(
        r"Posisi .+ di .+ berlokasi di .+\.\s*Membutuhkan keahlian dalam bidang",
        re.IGNORECASE,
    ),
    re.compile(
        r"Tanggung jawab meliputi pengembangan sistem berbasis .+, kolaborasi dengan tim",
        re.IGNORECASE,
    ),
    re.compile(
        r"Detail tugas meliputi kolaborasi tim, pengembangan sistem, dan implementasi teknologi terbaru",
        re.IGNORECASE,
    ),
]

# ─── Perusahaan placeholder yang dipakai di fallback generator ───────────────
FALLBACK_COMPANIES = {
    "PT Global Tech Indonesia",
}


# ─── Data class hasil validasi batch ─────────────────────────────────────────
@dataclass
class ValidationResult:
    total: int = 0
    valid: int = 0
    invalid: int = 0
    fallback: int = 0
    real: int = 0
    missing_fields_summary: dict[str, int] = field(default_factory=dict)
    fallback_records: list[dict] = field(default_factory=list)
    invalid_records: list[dict] = field(default_factory=list)

    def log_summary(self, source: str = ""):
        tag = f"[{source}] " if source else ""
        logger.info(
            f"{tag}Validasi selesai — "
            f"total={self.total} valid={self.valid} "
            f"invalid={self.invalid} fallback={self.fallback} real={self.real}"
        )
        if self.fallback_records:
            logger.warning(
                f"{tag}{self.fallback} record terdeteksi fallback/sintetis:"
            )
            for r in self.fallback_records[:5]:
                logger.warning(
                    f"  - {r.get('job_title')} @ {r.get('company_name')}"
                )
        if self.invalid_records:
            logger.warning(
                f"{tag}{self.invalid} record tidak lengkap field-nya:"
            )
            for r in self.invalid_records[:5]:
                logger.warning(
                    f"  - missing: {r.get('_missing_fields')} | "
                    f"title: {r.get('job_title', '?')}"
                )


# ─── Fungsi utama ─────────────────────────────────────────────────────────────

def is_fallback_record(job: dict) -> bool:
    """
    Cek apakah record ini kemungkinan besar data sintetis/fallback.
    Return True = fallback, False = kemungkinan real.
    """
    desc = job.get("job_description", "") or ""

    # Cek pola kalimat template
    if any(p.search(desc) for p in FALLBACK_PATTERNS):
        return True

    # Cek perusahaan placeholder
    if job.get("company_name") in FALLBACK_COMPANIES:
        return True

    return False


def validate_job(job: dict) -> tuple[bool, list[str]]:
    """
    Validasi field wajib pada satu record.
    Return (is_valid, missing_fields).
    """
    missing = [f for f in REQUIRED_FIELDS if not job.get(f)]
    return (len(missing) == 0), missing


def validate_batch(
    jobs: list[dict],
    source: str = "",
    add_timestamp_if_missing: bool = True,
) -> ValidationResult:
    """
    Validasi seluruh batch jobs.
    - Otomatis tambahkan _scrape_timestamp kalau kosong (opsional).
    - Return ValidationResult dengan ringkasan lengkap.
    """
    result = ValidationResult(total=len(jobs))

    for job in jobs:
        # Auto-tambah timestamp kalau tidak ada
        if add_timestamp_if_missing and not job.get("_scrape_timestamp"):
            job["_scrape_timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")

        is_valid, missing = validate_job(job)

        if not is_valid:
            result.invalid += 1
            job["_missing_fields"] = missing
            result.invalid_records.append(job)
            for f in missing:
                result.missing_fields_summary[f] = (
                    result.missing_fields_summary.get(f, 0) + 1
                )
            continue  # record invalid → skip cek fallback

        result.valid += 1

        if is_fallback_record(job):
            result.fallback += 1
            job["_is_fallback"] = True
            result.fallback_records.append(job)
        else:
            result.real += 1
            job["_is_fallback"] = False

    result.log_summary(source)
    return result


def filter_real_jobs(
    jobs: list[dict],
    source: str = "",
    allow_fallback: bool = False,
) -> list[dict]:
    """
    Validasi batch lalu kembalikan hanya record yang:
    - Lolos validasi field wajib
    - Bukan fallback (kecuali allow_fallback=True)

    allow_fallback=True berguna di scraper.py saat tidak ada data real sama sekali
    (daripada return kosong, tetap simpan tapi dengan flag _is_fallback=True).
    """
    result = validate_batch(jobs, source=source)

    if allow_fallback:
        # Kembalikan semua yang valid (termasuk fallback), asal field lengkap
        kept = [j for j in jobs if not j.get("_missing_fields")]
    else:
        # Kembalikan hanya yang valid DAN bukan fallback
        kept = [j for j in jobs if not j.get("_missing_fields") and not j.get("_is_fallback")]

    dropped = len(jobs) - len(kept)
    if dropped:
        logger.info(
            f"[{source}] filter_real_jobs: {len(kept)} dipakai, "
            f"{dropped} dibuang (invalid/fallback)"
        )

    return kept
