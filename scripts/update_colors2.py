import sys

file_path = "frontend/src/routes/index.tsx"
with open(file_path, "r") as f:
    content = f.read()

# Replace Green to Pastel Green
content = content.replace("#1DB954", "#98FB98") # Pastel green
content = content.replace("#1AA34A", "#77DD77") # Hover pastel green
content = content.replace("#107533", "#55C655") # Darker pastel green

# Replace Yellow to Bright Yellow
content = content.replace("#FFC107", "#FFE600") # Bright yellow
content = content.replace("#B28704", "#CCB800") # Darker bright yellow

# Ensure Blue is Bright Blue
content = content.replace("#007AFF", "#0088FF") # Brighter blue
content = content.replace("#005BB5", "#0066CC") # Darker brighter blue

# Red is already #FF0000

with open(file_path, "w") as f:
    f.write(content)

print("Colors updated successfully.")
