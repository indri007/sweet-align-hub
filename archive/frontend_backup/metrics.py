"""
Basic application metrics, emitted as structured log entries with a
`metric_type` field.

Setup in Cloud Console (one-time, no extra dependency needed):
  Logging -> Log-based Metrics -> Create Metric
  Filter: jsonPayload.metric_type="cv_upload_duration_ms"
This turns log lines into charts/alerts in Cloud Monitoring for free,
without needing the google-cloud-monitoring SDK.
"""

import time
from contextlib import contextmanager

from logger import get_logger

logger = get_logger("metrics")


def record_event(metric_name: str, value: float = 1, **labels):
    """Emit a counter/gauge-style metric as a structured log line.

    Example: record_event("cv_upload_success", format="pdf")
    """
    logger.info(
        f"metric:{metric_name}",
        extra={"metric_type": metric_name, "metric_value": value, **labels},
    )


@contextmanager
def track_duration(metric_name: str, **labels):
    """Context manager to measure and log how long an operation took.

    Example:
        with track_duration("cv_processing"):
            extract_cv_text(file_bytes, filename)
    """
    start = time.time()
    error = None
    try:
        yield
    except Exception as e:
        error = str(e)
        raise
    finally:
        duration_ms = round((time.time() - start) * 1000, 1)
        logger.info(
            f"metric:{metric_name}_duration",
            extra={
                "metric_type": f"{metric_name}_duration_ms",
                "metric_value": duration_ms,
                "success": error is None,
                "error": error,
                **labels,
            },
        )
