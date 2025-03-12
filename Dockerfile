FROM python:3.9-slim

WORKDIR /app

# Install FFmpeg and browser dependencies for cookie extraction
RUN apt-get update && \
    apt-get install -y ffmpeg curl gnupg && \
    curl -sS https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p static/downloads

# Expose the port
EXPOSE 10000

# Command to run the application
CMD ["gunicorn", "--config", "gunicorn_config.py", "server:app"]