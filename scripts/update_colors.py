import sys

file_path = "frontend/src/routes/index.tsx"
with open(file_path, "r") as f:
    content = f.read()

# Blue
content = content.replace("#0A66C2", "#007AFF") # Bright blue
content = content.replace("#004182", "#005BB5") # Darker blue

# Green
content = content.replace("#34A853", "#1DB954") # Spotify green
content = content.replace("#1E7A38", "#1AA34A") # Hover green
content = content.replace("#1b5e32", "#107533") # Darker green

# Yellow
content = content.replace("#FBBC05", "#FFC107") # Yellow
content = content.replace("#B58600", "#B28704") # Darker yellow

# Red is already #FF0000 which is bright red

with open(file_path, "w") as f:
    f.write(content)

print("Colors updated successfully.")
