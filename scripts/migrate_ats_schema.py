import os
import sys
from sqlalchemy import text

# Tambahkan direktori root ke path agar bisa import database.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import DatabaseManager

def migrate():
    print("Connecting to Aiven MySQL...")
    db = DatabaseManager()
    
    # Translate PostgreSQL syntax from Markdown to MySQL syntax
    queries = [
        """
        CREATE TABLE IF NOT EXISTS job_functions (
            function_id INT AUTO_INCREMENT PRIMARY KEY,
            function_name_id VARCHAR(100) NOT NULL,
            function_name_en VARCHAR(100) NOT NULL,
            parent_function_id INT NULL,
            FOREIGN KEY (parent_function_id) REFERENCES job_functions(function_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS job_levels (
            level_id INT AUTO_INCREMENT PRIMARY KEY,
            level_name VARCHAR(50) NOT NULL,
            level_rank INT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS skills (
            skill_id INT AUTO_INCREMENT PRIMARY KEY,
            skill_name_id VARCHAR(150) NOT NULL,
            skill_name_en VARCHAR(150) NOT NULL,
            skill_type VARCHAR(30),
            function_id INT,
            synonyms JSON,
            weight_default DECIMAL(3,2) DEFAULT 1.00,
            FOREIGN KEY (function_id) REFERENCES job_functions(function_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS action_verbs (
            verb_id INT AUTO_INCREMENT PRIMARY KEY,
            verb_id_lang VARCHAR(50),
            verb_en_lang VARCHAR(50),
            category VARCHAR(30)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS scoring_rubric (
            rubric_id INT AUTO_INCREMENT PRIMARY KEY,
            dimension VARCHAR(50),
            criterion TEXT,
            max_points DECIMAL(5,2),
            weight DECIMAL(4,3),
            rule_type VARCHAR(30)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS cv_red_flags (
            flag_id INT AUTO_INCREMENT PRIMARY KEY,
            flag_name_id VARCHAR(150),
            flag_name_en VARCHAR(150),
            description_id TEXT,
            description_en TEXT,
            severity VARCHAR(20),
            fix_suggestion_id TEXT,
            fix_suggestion_en TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS rewrite_examples (
            example_id INT AUTO_INCREMENT PRIMARY KEY,
            function_id INT,
            before_text_id TEXT,
            after_text_id TEXT,
            before_text_en TEXT,
            after_text_en TEXT,
            principle TEXT,
            FOREIGN KEY (function_id) REFERENCES job_functions(function_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS cv_scoring_history (
            scoring_id INT AUTO_INCREMENT PRIMARY KEY,
            cv_hash VARCHAR(64),
            target_function_id INT,
            score_parseability DECIMAL(5,2),
            score_keyword DECIMAL(5,2),
            score_content DECIMAL(5,2),
            score_structure DECIMAL(5,2),
            score_composite DECIMAL(5,2),
            model_version TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (target_function_id) REFERENCES job_functions(function_id)
        );
        """
    ]
    
    with db.engine.begin() as conn:
        for i, query in enumerate(queries):
            print(f"Executing query {i+1}/{len(queries)}...")
            conn.execute(text(query))
            
    print("✅ Migration successful! All tables created in Aiven MySQL.")

if __name__ == "__main__":
    migrate()
