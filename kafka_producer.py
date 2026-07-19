import json
import logging
import threading
from kafka import KafkaProducer
import config

logger = logging.getLogger(__name__)

class KafkaProducerSingleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(KafkaProducerSingleton, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self):
        try:
            import os
            ca_path = os.path.abspath(config.KAFKA_CA_PATH)
            self.producer = KafkaProducer(
                bootstrap_servers=[config.KAFKA_URI],
                security_protocol="SASL_SSL",
                sasl_mechanism="SCRAM-SHA-256",
                sasl_plain_username=config.KAFKA_USER,
                sasl_plain_password=config.KAFKA_PASS,
                ssl_cafile=ca_path,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info("✅ Berhasil terhubung ke Aiven Kafka!")
        except Exception as e:
            logger.error(f"❌ Gagal terhubung ke Aiven Kafka: {e}")
            self.producer = None

    def send_message(self, topic: str, message: dict):
        if not self.producer:
            logger.warning(f"⚠️ Kafka belum terhubung. Gagal mengirim ke {topic}")
            return
        
        try:
            self.producer.send(topic, value=message)
            self.producer.flush()
        except Exception as e:
            logger.error(f"❌ Error mengirim pesan ke Kafka ({topic}): {e}")

# Global instance for easy import
_kafka = KafkaProducerSingleton()

def send_kafka_message(topic: str, message_dict: dict):
    """
    Sends a JSON message to a Kafka topic in the background.
    """
    def _send():
        _kafka.send_message(topic, message_dict)
    
    threading.Thread(target=_send, daemon=True).start()
