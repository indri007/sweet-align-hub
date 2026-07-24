import secrets
from sqlalchemy import create_engine, text
import config

try:
    engine = create_engine(config.DATABASE_URL, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        # Generate random passwords
        ro_pass = secrets.token_urlsafe(16)
        log_pass = secrets.token_urlsafe(16)
        
        print("Creating n8n_readonly user...")
        conn.execute(text(f"CREATE USER IF NOT EXISTS 'n8n_readonly'@'%' IDENTIFIED BY '{ro_pass}';"))
        conn.execute(text(f"ALTER USER 'n8n_readonly'@'%' IDENTIFIED BY '{ro_pass}';"))
        conn.execute(text("GRANT SELECT ON defaultdb.jobs TO 'n8n_readonly'@'%';"))
        
        # Telemetry log table may or may not exist. We just grant INSERT anyway.
        # But wait, what is the log table named? In JSON it says telemetry_log. Let's create it if it doesn't exist.
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS telemetry_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            event_type VARCHAR(50),
            user_message TEXT,
            bot_reply TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """))
        
        print("Creating n8n_logger user...")
        conn.execute(text(f"CREATE USER IF NOT EXISTS 'n8n_logger'@'%' IDENTIFIED BY '{log_pass}';"))
        conn.execute(text(f"ALTER USER 'n8n_logger'@'%' IDENTIFIED BY '{log_pass}';"))
        conn.execute(text("GRANT INSERT ON defaultdb.telemetry_log TO 'n8n_logger'@'%';"))
        
        conn.execute(text("FLUSH PRIVILEGES;"))
        
        print("\nSUCCESS! Users created.")
        print("-" * 30)
        print("N8N Read-Only Credential (for Aiven 1):")
        print(f"User: n8n_readonly")
        print(f"Password: {ro_pass}")
        print("-" * 30)
        print("N8N Logger Credential (for Aiven 2):")
        print(f"User: n8n_logger")
        print(f"Password: {log_pass}")
        
except Exception as e:
    print(f"Error: {e}")
