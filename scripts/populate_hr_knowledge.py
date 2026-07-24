import os
import sys
import subprocess
import re
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import DatabaseManager

BASE_DOCX_PATH = "/Users/jevin/Downloads/8. 10 TOOL HRD  Modul Interview + Katalog KPI + SOP HRD + Form + Pelatih/TOOLS HRD/TOOLS HRD/Tools 1 - Kamus Kompetensi Hard Skills dan Soft Skills"

FILES_TO_PROCESS = [
    ("IT & Business Dev", "Kamus Kompetensi Bidang Business Development dan IT.docx"),
    ("HRD", "Kamus Kompetensi Bidang HRD.docx"),
    ("Finance & Audit", "Kamus Kompetensi Bidang Keuangan Audit dan Pajak.docx")
]

def extract_text_from_docx(filepath):
    try:
        result = subprocess.run(['textutil', '-convert', 'txt', filepath, '-stdout'], capture_output=True, text=True, check=True)
        return result.stdout
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return ""

def parse_skills(text_content):
    skills = []
    lines = text_content.split('\n')
    for line in lines:
        line = line.strip()
        # Many docx lists use standard bullet characters
        if line.startswith('•') or line.startswith('-'):
            # Extract text between bullet and colon, e.g. "• Feasibility Study :"
            match = re.search(r'[•\-]\s*(.*?)\s*:', line)
            if match:
                skill_name = match.group(1).strip()
                if skill_name and len(skill_name) < 100:  # Avoid parsing whole paragraphs
                    skills.append(skill_name)
    return list(set(skills)) # Deduplicate

def populate_db():
    print("Connecting to Aiven MySQL...")
    db = DatabaseManager()
    
    with db.engine.begin() as conn:
        for function_name, filename in FILES_TO_PROCESS:
            filepath = os.path.join(BASE_DOCX_PATH, filename)
            if not os.path.exists(filepath):
                print(f"Skipping {function_name}, file not found.")
                continue
                
            print(f"Extracting skills for {function_name}...")
            raw_text = extract_text_from_docx(filepath)
            skills = parse_skills(raw_text)
            print(f"Found {len(skills)} skills for {function_name}.")
            
            # Insert Job Function
            result = conn.execute(text("INSERT INTO job_functions (function_name_id, function_name_en) VALUES (:id_name, :en_name)"), {"id_name": function_name, "en_name": function_name})
            function_id = result.lastrowid
            
            # Insert Skills
            for skill in skills:
                conn.execute(
                    text("INSERT INTO skills (skill_name_id, skill_name_en, skill_type, function_id) VALUES (:id_name, :en_name, 'hard_skill', :func_id)"),
                    {"id_name": skill, "en_name": skill, "func_id": function_id}
                )
                
    print("✅ Knowledge Base populated successfully!")

if __name__ == "__main__":
    populate_db()
