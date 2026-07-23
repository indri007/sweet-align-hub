"""
N8N Client — HTTP wrapper for communicating with N8N webhooks.
Sends requests to N8N workflows and returns AI-generated responses.
Falls back to local agents if N8N is unreachable.
"""

import requests
import json
import config


def call_n8n_webhook(endpoint: str, data: dict, timeout: int = 120) -> dict:
    """
    Send a POST request to an N8N webhook endpoint.

    Args:
        endpoint: The webhook path (e.g., '/webhook/job-match')
        data: JSON payload to send
        timeout: Request timeout in seconds

    Returns:
        dict with the response data, or {"error": "..."} on failure
    """
    url = config.N8N_WEBHOOK_URL.rstrip("/") + endpoint

    try:
        response = requests.post(
            url,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )
        response.raise_for_status()

        # N8N may return the data in different formats
        result = response.json()

        # Handle case where N8N wraps response in array
        if isinstance(result, list) and len(result) > 0:
            result = result[0]

        return result

    except requests.exceptions.Timeout:
        return {"error": "N8N webhook timeout. Server mungkin sedang sibuk."}
    except requests.exceptions.ConnectionError:
        return {"error": "Tidak dapat terhubung ke N8N. Pastikan N8N server aktif."}
    except requests.exceptions.HTTPError as e:
        return {"error": f"N8N HTTP error: {e.response.status_code} - {e.response.text[:200]}"}
    except json.JSONDecodeError:
        # Response might be plain text
        return {"output": response.text}
    except Exception as e:
        return {"error": f"N8N error: {str(e)}"}


# ─── Wrapper Functions for Each Workflow ──────────────────


def match_cv_to_jobs_n8n(cv_text: str, jobs_context: str) -> str:
    """
    Call N8N to get AI analysis of CV-to-job matching.
    Returns the AI summary text.
    """
    result = call_n8n_webhook("/webhook/job-match", {
        "cv_text": cv_text[:3000],
        "jobs_context": jobs_context,
    })
    return result.get("output") or result.get("text") or result.get("response") or result.get("error", "")


def review_cv_n8n(cv_text: str, target_job: dict = None) -> str:
    """
    Call N8N to review CV and get feedback.
    Returns the feedback text.
    """
    payload = {"cv_text": cv_text}
    if target_job:
        payload["target_job"] = target_job
    result = call_n8n_webhook("/webhook/cv-review", payload)
    return result.get("output") or result.get("text") or result.get("response") or result.get("error", "")


def generate_ats_cv_n8n(cv_text: str, target_job: dict = None) -> str:
    """
    Call N8N to generate an ATS-friendly version of the CV.
    Returns the ATS CV text.
    """
    payload = {"cv_text": cv_text}
    if target_job:
        payload["target_job"] = target_job
    result = call_n8n_webhook("/webhook/ats-generate", payload)
    return result.get("output") or result.get("text") or result.get("response") or result.get("error", "")


def career_chat_n8n(cv_text: str, chat_history: list[dict], user_message: str, target_job: dict = None) -> str:
    """
    Call N8N for career consultation chat.
    Returns the AI response text.
    """
    payload = {
        "cv_text": cv_text[:4000],
        "chat_history": chat_history,
        "user_message": user_message,
    }
    if target_job:
        payload["target_job"] = target_job
    result = call_n8n_webhook("/webhook/career-chat", payload)
    return result.get("output") or result.get("text") or result.get("response") or result.get("error", "")


def start_interview_n8n(cv_text: str, job_info: dict) -> str:
    """
    Call N8N to start a mock interview session.
    Returns the AI interviewer's first question.
    """
    result = call_n8n_webhook("/webhook/mock-interview", {
        "action": "start",
        "cv_text": cv_text[:3000],
        "job_title": job_info.get("job_title", ""),
        "company_name": job_info.get("company_name", ""),
        "job_description": job_info.get("job_description", "")[:2000],
    })
    return result.get("output") or result.get("text") or result.get("response") or result.get("error", "")


def continue_interview_n8n(cv_text: str, job_info: dict, interview_history: list[dict], user_answer: str) -> str:
    """
    Call N8N to continue a mock interview with user's answer.
    Returns the AI interviewer's feedback + next question.
    """
    result = call_n8n_webhook("/webhook/mock-interview", {
        "action": "continue",
        "cv_text": cv_text[:2000],
        "job_title": job_info.get("job_title", ""),
        "company_name": job_info.get("company_name", ""),
        "job_description": job_info.get("job_description", "")[:1000],
        "interview_history": interview_history,
        "user_answer": user_answer,
    })
    return result.get("output") or result.get("text") or result.get("response") or result.get("error", "")


def generate_sql_query_n8n(natural_language_query: str) -> str:
    """
    Call N8N to convert natural language to SQL query.
    Returns the SQL query string.
    """
    result = call_n8n_webhook("/webhook/sql-query", {
        "question": natural_language_query,
    })
    return result.get("output") or result.get("text") or result.get("sql") or result.get("error", "")


def explain_sql_results_n8n(question: str, sql_query: str, results: list[dict]) -> str:
    """
    Call N8N to get AI explanation of SQL query results.
    Returns the explanation text.
    """
    result = call_n8n_webhook("/webhook/sql-query", {
        "action": "explain",
        "question": question,
        "sql_query": sql_query,
        "results": str(results[:10]),
        "result_count": len(results),
    })
    return result.get("output") or result.get("text") or result.get("response") or result.get("error", "")
