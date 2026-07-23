import re

file_path = "/Users/jevin/Downloads/sweet-align-hub-backup-20260718/sweet-align-hub-extracted/PRD_JobMatch_AI_Redeploy_Updated.md"

with open(file_path, 'r') as f:
    content = f.read()

# Replace heaven
content = re.sub(r'heaven-493814-f85dc', 'braided-trees-502809-r5', content)
content = re.sub(r'heaven-493814', 'braided-trees-502809', content)
content = re.sub(r'heaven', 'braided-trees', content)

# Replace Cloud Run with Platform
content = re.sub(r'(?i)Cloud Run', 'Platform', content)

# Specific fixes for awkward phrasing
content = content.replace("Service Platform live", "Service live")
content = content.replace("ke Platform", "ke Platform Server")
content = content.replace("di Platform", "di Platform Server")
content = content.replace("dari Platform", "dari Platform Server")
content = content.replace("untuk Platform", "untuk Platform Server")
content = content.replace("Google Platform", "Google Cloud")
content = content.replace("Platform Server Server", "Platform Server")
content = content.replace("Deployment Platform", "Deployment")
content = content.replace("gcloud run", "gcloud run") # gcloud run command is necessary if they deploy to GCP

with open(file_path, 'w') as f:
    f.write(content)

print("Replacements done.")
