"""
Lightweight health-check HTTP server, run in a background thread alongside
Streamlit.

IMPORTANT (Cloud Run): this listens on its own port (default 8081), which
is NOT reachable from the public service URL — Cloud Run only forwards
external traffic to the single $PORT the container declares (used by
Streamlit itself). This server is for:
  1. Cloud Run startup/liveness probes configured against this port in the
     service spec (gcloud run services update --... or YAML), and
  2. local/internal debugging via `gcloud run services proxy` or
     `kubectl port-forward`-style tooling.

For a publicly-curlable basic liveness check, use Streamlit's own built-in
route on the main port instead: GET /_stcore/health -> "ok"
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import health_check
from logger import get_logger

logger = get_logger("health_server")


class HealthHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress default stderr access logs; structured logger used instead

    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {"status": "ok"})
        elif self.path == "/health/deep":
            result = health_check.run_all_checks()
            code = 200 if result["status"] == "ok" else 503
            self._respond(code, result)
        else:
            self._respond(404, {"status": "not_found"})

    def _respond(self, code: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start_health_server(port: int = 8081):
    """Starts the health server in a daemon thread. Call once at app startup."""
    def _serve():
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        logger.info("Health server started", extra={"port": port})
        server.serve_forever()

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()
    return thread
