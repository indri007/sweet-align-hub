from enum import Enum
import time

class ServiceStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"

class SystemHealthMonitor:
    """
    Dipanggil sebelum request ke Gemini/Qdrant, supaya UI bisa tampilkan
    graceful degradation (bukan crash).
    """
    def __init__(self, gemini_client=None, qdrant_client=None, mysql_conn=None):
        self.gemini_client = gemini_client
        self.qdrant_client = qdrant_client
        self.mysql_conn = mysql_conn

    def check_gemini(self) -> (ServiceStatus, float):
        """Health check ringan ke Gemini API."""
        if not self.gemini_client:
            return ServiceStatus.DOWN, 0.0
            
        start = time.time()
        try:
            # Lakukan request ringan misal generate_content("ping")
            self.gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents="ping"
            )
            latency = round((time.time() - start) * 1000, 2)
            return ServiceStatus.OK, latency
        except Exception as e:
            print(f"[Health] Gemini error: {e}")
            return ServiceStatus.DOWN, 0.0

    def check_qdrant(self) -> (ServiceStatus, float):
        """Health check koneksi Qdrant dengan timeout eksplisit."""
        if not self.qdrant_client:
            return ServiceStatus.DOWN, 0.0
            
        start = time.time()
        import concurrent.futures
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self.qdrant_client.get_collections)
                future.result(timeout=5)  # 5 detik timeout
            latency = round((time.time() - start) * 1000, 2)
            return ServiceStatus.OK, latency
        except concurrent.futures.TimeoutError:
            print("[Health] Qdrant connection timed out.")
            return ServiceStatus.DOWN, 0.0
        except Exception as e:
            print(f"[Health] Qdrant error: {e}")
            return ServiceStatus.DOWN, 0.0

    def check_mysql(self) -> (ServiceStatus, float):
        """Health check koneksi Aiven MySQL."""
        if not self.mysql_conn:
            return ServiceStatus.DOWN, 0.0
            
        start = time.time()
        try:
            with self.mysql_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
            latency = round((time.time() - start) * 1000, 2)
            return ServiceStatus.OK, latency
        except Exception as e:
            print(f"[Health] MySQL error: {e}")
            return ServiceStatus.DOWN, 0.0

    def get_degraded_message(self, service: str) -> str:
        """Pesan human-readable Bahasa Indonesia untuk UI."""
        messages = {
            "gemini": "Sistem AI sedang mengalami antrean tinggi. Beberapa fitur analisis dan interview mungkin berjalan lebih lambat. Silakan coba beberapa saat lagi.",
            "qdrant": "Mesin pencarian semantik (Job Matcher) sedang tidak dapat diakses. Rekomendasi pekerjaan mungkin tidak seakurat biasanya.",
            "mysql": "Koneksi ke database profil pengguna terputus. Penyimpanan sesi dan histori CV sementara dinonaktifkan."
        }
        return messages.get(service.lower(), "Layanan sedang mengalami gangguan sementara. Tim engineer kami sedang menanganinya.")
