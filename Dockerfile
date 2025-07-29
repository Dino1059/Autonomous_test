# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install essential system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    procps \
    xdg-utils \
    xvfb \
    x11-apps \
    libxss1 \
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    libxcb-dri3-0 \
    libxtst6 \
    libxshmfence1 \
    libglu1-mesa \
    libgles2-mesa \
    libegl1-mesa \
    libpulse0 \
    libdbus-1-3 \
    libcairo2 \
    libcups2 \
    libexpat1 \
    libfontconfig1 \
    libfreetype6 \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libxcursor1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Create browser profile directory
RUN mkdir -p /app/browser_profiles/default

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/demo_reports

# Set permissions
RUN chmod +x /app/app/main.py /app/gradio_ui/webui.py

# Copy and set permissions for start.sh
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose ports
EXPOSE 8081 7860

# Set default command
CMD ["/app/start.sh"]