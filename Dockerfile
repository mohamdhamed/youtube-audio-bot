# Use Python 3.11 slim image
FROM python:3.11-slim

# Install ffmpeg and curl (required for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create downloads directory
RUN mkdir -p downloads

# Expose health check port and dashboard port
EXPOSE 8000 5000

# Run the bot
CMD ["python", "bot.py"]
