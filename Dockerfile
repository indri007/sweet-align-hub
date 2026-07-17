# Use official Python lightweight image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies + Google Chrome (needed by Selenium in scraper.py)
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    gnupg \
    unzip \
    curl \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port for Cloud Run (Cloud Run uses 8080 by default)
EXPOSE 8080

# Command to run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port", "8080", "--server.address", "0.0.0.0"]
