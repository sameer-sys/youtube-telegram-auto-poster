# Auto Poster Bot - Docker Image for Koyeb
FROM python:3.11-slim

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    base64 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY auto_poster.py .
COPY telegram_loop.py .
COPY fb_ig.py .
COPY entrypoint.sh .

# Create directories
RUN mkdir -p videos metadata fb_metadata ig_metadata

# Run as non-root
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Entrypoint handles secret decoding
ENTRYPOINT ["/app/entrypoint.sh"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080