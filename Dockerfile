FROM python:3.9-slim

WORKDIR /app

# Install FFmpeg for video processing
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directories
RUN mkdir -p static/downloads

# Expose port
EXPOSE 10000

# Command to run the application
CMD ["gunicorn", "--config", "gunicorn_config.py", "server:app"]