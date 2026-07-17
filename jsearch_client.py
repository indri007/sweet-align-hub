"""
JSearch (RapidAPI) client - fetches real-time job listings and maps them
to the same dict shape DatabaseManager.insert_jobs() / scraper.py already
expect, so no other code needs to change.

Env vars required:
  RAPIDAPI_KEY   - your RapidAPI key for JSearch

IMPORTANT (quota): num_pages controls how many result-pages are fetched in
one call. Each page fetched typically consumes one unit against your
monthly quota, so num_pages=2 counts as ~2 requests, not 1. Keep
num_pages=1 to guarantee exactly 1 request per fetch_jobs() call.
"""

import os
import time
import httpx

from logger import get_logger

logger = get_logger("jsearch_client")

JSEARCH_HOST = "jsearch.p.rapidapi.com"
JSEARCH_URL = f"https://{JSEARCH_HOST}/search-v2"

_CURRENCY_LABEL = {
    "IDR": "Rp",
    "USD": "$",
    "SGD": "S$",
}


def _get_api_key() -> str:
    key = os.environ.get("RAPIDAPI_KEY", "")
    if not key:
        raise RuntimeError("RAPIDAPI_KEY environment variable is not set.")
    return key


def _format_salary(job: dict) -> str:
    min_salary = job.get("job_min_salary")
    max_salary = job.get("job_max_salary")
    if not min_salary or not max_salary:
        return "None"

    currency = job.get("job_salary_currency") or "IDR"
    label = _CURRENCY_LABEL.get(currency, currency + " ")

    if currency == "IDR":
        lo = f"{min_salary:,.0f}".replace(",", ".")
        hi = f"{max_salary:,.0f}".replace(",", ".")
    else:
        lo = f"{min_salary:,.0f}"
        hi = f"{max_salary:,.0f}"

    period = job.get("job_salary_period", "MONTH")
    period_label = {"MONTH": "per month", "YEAR": "per year", "HOUR": "per hour"}.get(period, "")
    return f"{label} {lo} \u2013 {label} {hi} {period_label}".strip()


def fetch_jobs(query: str, country: str = "id", num_pages: int = 1) -> list[dict]:
    """
    Calls JSearch /search (exactly `num_pages` pages, default 1 = 1 request)
    and maps results into the dict shape expected by
    DatabaseManager.insert_jobs():
      job_title, company_name, location, work_type, salary,
      job_description, _scrape_timestamp, _source_job_id
    """
    if num_pages != 1:
        logger.info(
            "fetch_jobs called with num_pages != 1; this consumes more than "
            "1 request against the monthly quota",
            extra={"num_pages": num_pages},
        )

    headers = {
        "x-rapidapi-key": _get_api_key(),
        "x-rapidapi-host": JSEARCH_HOST,
    }
    params = {
        "query": query,
        "country": country,
        "num_pages": str(num_pages),
        "date_posted": "all",
    }

    logger.info("Fetching jobs from JSearch", extra={"query": query, "country": country})

    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(JSEARCH_URL, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        logger.error(
            "JSearch API returned an error",
            extra={"status_code": e.response.status_code, "body": e.response.text[:500]},
        )
        raise
    except Exception as e:
        logger.error("JSearch API request failed", extra={"error": str(e)})
        raise

    data_field = data.get("data", [])
    if isinstance(data_field, dict):
        raw_jobs = data_field.get("jobs", [])
    else:
        raw_jobs = data_field
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ")

    mapped = []
    for job in raw_jobs:
        location_parts = [job.get("job_city"), job.get("job_state")]
        location = ", ".join(p for p in location_parts if p) or job.get("job_country", "N/A")

        mapped.append({
            "job_title": job.get("job_title") or "Unknown Position",
            "company_name": job.get("employer_name") or "Unknown Company",
            "location": location,
            "work_type": job.get("job_employment_type") or "N/A",
            "salary": _format_salary(job),
            "job_description": job.get("job_description") or "",
            "_scrape_timestamp": now_iso,
            "_source_job_id": job.get("job_id", ""),
        })

    logger.info(
        "JSearch fetch completed",
        extra={"query": query, "jobs_returned": len(mapped)},
    )
    return mapped
