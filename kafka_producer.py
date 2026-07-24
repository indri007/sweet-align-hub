import json
import logging
import threading
from confluent_kafka import Producer
import config
import os

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
            ca_path = os.path.abspath(config.KAFKA_CA_PATH)
            
            conf = {
                'bootstrap.servers': config.KAFKA_URI,
                'security.protocol': 'SASL_SSL',
                'sasl.mechanisms': 'SCRAM-SHA-256',
                'sasl.username': config.KAFKA_USER,
                'sasl.password': config.KAFKA_PASS,
                'ssl.ca.location': ca_path,
                'client.id': 'jobmatch-ai-producer'
            }
            
            self.producer = Producer(conf)
            logger.info("✅ Berhasil terhubung ke Aiven Kafka (via confluent-kafka)!")
        except Exception as e:
            logger.error(f"❌ Gagal terhubung ke Aiven Kafka: {e}")
            self.producer = None

    def send_message(self, topic: str, message: dict):
        if not self.producer:
            logger.warning(f"⚠️ Kafka belum terhubung. Gagal mengirim ke {topic}")
            return
        
        try:
            payload = json.dumps(message).encode('utf-8')
            
            # Fire and forget with a callback
            def delivery_report(err, msg):
                if err is not None:
                    logger.error(f"❌ Message delivery failed: {err}")
            
            self.producer.produce(topic, value=payload, callback=delivery_report)
            self.producer.poll(0) # Trigger callbacks
        except Exception as e:
            logger.error(f"❌ Error mengirim pesan ke Kafka ({topic}): {e}")
            
    def flush(self):
        if self.producer:
            self.producer.flush()

# Global instance for easy import
_kafka = KafkaProducerSingleton()

def send_kafka_message(topic: str, message_dict: dict):
    """
    Sends a JSON message to a Kafka topic in the background.
    """
    def _send():
        _kafka.send_message(topic, message_dict)
    
    threading.Thread(target=_send, daemon=True).start()
