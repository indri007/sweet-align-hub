"""
Database module — SQLite/MySQL query manager using SQLAlchemy.
Handles structured job data queries (filters, stats, etc.)
"""

import re
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text as sql_text
import config

Base = declarative_base()


class Job(Base):
    """Job listing model for SQL database."""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_title = Column(String(500), nullable=False)
    company_name = Column(String(500))
    location = Column(String(500))
    work_type = Column(String(100))
    salary_raw = Column(String(500))
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    job_description = Column(Text)
    scrape_timestamp = Column(String(100))


def parse_salary(salary_str: str) -> tuple[Optional[float], Optional[float]]:
    """
    Parse salary string into min and max values.
    Examples:
        "Rp 10.000.000 – Rp 14.000.000 per month" -> (10000000, 14000000)
        "Rp 6.000.000 per month" -> (6000000, 6000000)
        "None" -> (None, None)
    """
    if not salary_str or salary_str == "None":
        return None, None

    numbers = re.findall(r'[\d]+(?:\.[\d]+)*', salary_str)
    parsed = []
    for num_str in numbers:
        clean = num_str.replace(".", "")
        try:
            parsed.append(float(clean))
        except ValueError:
            continue

    parsed = [n for n in parsed if n >= 100000]

    if len(parsed) >= 2:
        return min(parsed), max(parsed)
    elif len(parsed) == 1:
        return parsed[0], parsed[0]
    return None, None


class DatabaseManager:
    """Manages SQLite/MySQL database connections and queries."""

    _FORBIDDEN_SQL = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|GRANT|REVOKE|CREATE)\b|;|--",
        re.IGNORECASE,
    )

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or config.DATABASE_URL

        if self.db_url.startswith("mysql"):
            if not self.db_url.startswith("mysql+pymysql://"):
                self.db_url = self.db_url.replace("mysql://", "mysql+pymysql://")

            if "?" in self.db_url:
                self.db_url = self.db_url.split("?")[0]

            import os
            ca_paths = ["aiven/ca.pem", "ca.pem", "data/ca.pem"]
            ca_path = next((p for p in ca_paths if os.path.exists(p)), None)

            if ca_path:
                ssl_args = {"ssl": {"ssl_ca": ca_path}}
            else:
                ssl_args = {"ssl": {"ssl_disabled": False}}

            self.engine = create_engine(self.db_url, connect_args=ssl_args, echo=False)
        else:
            self.engine = create_engine(self.db_url, echo=False)

        self.Session = sessionmaker(bind=self.engine)


    def create_tables(self):
        """Create all tables."""
        Base.metadata.create_all(self.engine)

    def insert_jobs(self, jobs_data: list[dict]):
        """Insert multiple job records."""
        session = self.Session()
        try:
            for job in jobs_data:
                salary_min, salary_max = parse_salary(job.get("salary", "None"))
                record = Job(
                    job_title=job.get("job_title", ""),
                    company_name=job.get("company_name", ""),
                    location=job.get("location", ""),
                    work_type=job.get("work_type", ""),
                    salary_raw=job.get("salary", "None"),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    job_description=job.get("job_description", ""),
                    scrape_timestamp=job.get("_scrape_timestamp", ""),
                )
                session.add(record)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_job_count(self) -> int:
        """Get total number of jobs."""
        session = self.Session()
        try:
            return session.query(Job).count()
        finally:
            session.close()

    def get_all_work_types(self) -> list[str]:
        """Get all unique work types."""
        session = self.Session()
        try:
            results = session.query(Job.work_type).distinct().all()
            return sorted([r[0] for r in results if r[0]])
        finally:
            session.close()

    def get_all_locations(self) -> list[str]:
        """Get all unique locations."""
        session = self.Session()
        try:
            results = session.query(Job.location).distinct().all()
            return sorted([r[0] for r in results if r[0]])
        finally:
            session.close()

    def get_job_stats(self) -> dict:
        """Get dashboard statistics."""
        session = self.Session()
        try:
            total = session.query(Job).count()
            with_salary = session.query(Job).filter(Job.salary_min.isnot(None)).count()
            companies = session.query(Job.company_name).distinct().count()
            work_types = session.query(Job.work_type).distinct().all()
            work_type_counts = {}
            for wt in work_types:
                if wt[0]:
                    count = session.query(Job).filter(Job.work_type == wt[0]).count()
                    work_type_counts[wt[0]] = count
            return {
                "total_jobs": total,
                "jobs_with_salary": with_salary,
                "total_companies": companies,
                "work_type_distribution": work_type_counts,
            }
        finally:
            session.close()

    def search_jobs_by_filters(
        self,
        work_type: Optional[str] = None,
        location_keyword: Optional[str] = None,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        keyword: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Search jobs with filters."""
        session = self.Session()
        try:
            query = session.query(Job)

            if work_type and work_type != "Semua":
                query = query.filter(Job.work_type == work_type)
            if location_keyword:
                query = query.filter(Job.location.ilike(f"%{location_keyword}%"))
            if salary_min is not None:
                query = query.filter(Job.salary_max >= salary_min)
            if salary_max is not None:
                query = query.filter(Job.salary_min <= salary_max)
            if keyword:
                query = query.filter(
                    (Job.job_title.ilike(f"%{keyword}%"))
                    | (Job.job_description.ilike(f"%{keyword}%"))
                )

            results = query.limit(limit).all()
            return [
                {
                    "id": r.id,
                    "job_title": r.job_title,
                    "company_name": r.company_name,
                    "location": r.location,
                    "work_type": r.work_type,
                    "salary_raw": r.salary_raw,
                    "salary_min": r.salary_min,
                    "salary_max": r.salary_max,
                    "job_description": r.job_description,
                }
                for r in results
            ]
        finally:
            session.close()

    def execute_raw_sql(self, query_str: str) -> list[dict]:
        """Execute a raw SQL query and return results as dicts. For SQL Agent."""
        if not query_str.strip().upper().startswith("SELECT"):
            return [{"error": "Hanya query SELECT yang diizinkan."}]
        if self._FORBIDDEN_SQL.search(query_str):
            return [{"error": "Query mengandung keyword yang tidak diizinkan."}]

        session = self.Session()
        try:
            result = session.execute(sql_text(query_str))
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"SQL execution failed: {e}")
            return [{"error": "Terjadi kesalahan saat menjalankan query."}]
        finally:
            session.close()

    def get_job_by_id(self, job_id: int) -> Optional[dict]:
        """Get a single job by ID."""
        session = self.Session()
        try:
            job = session.query(Job).filter(Job.id == job_id).first()
            if not job:
                return None
            return {
                "id": job.id,
                "job_title": job.job_title,
                "company_name": job.company_name,
                "location": job.location,
                "work_type": job.work_type,
                "salary_raw": job.salary_raw,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "job_description": job.job_description,
            }
        finally:
            session.close()
