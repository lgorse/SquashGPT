# Fixed Dockerfile for selenium/standalone-chrome
FROM selenium/standalone-chrome:latest

# Switch to root to fix permissions and install Python
USER root

# Install Python and PyAutoGUI dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-tk \
    python3-dev \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app


# Install Python dependencies
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

# Fix SeleniumBase driver permissions
RUN chmod -R 777 /opt/venv/lib/python3.14/site-packages/seleniumbase/drivers || true

# Copy application files
COPY . .

# Create writable cache directories for selenium and seleniumbase
RUN mkdir -p /home/seluser/.cache/selenium && \
    mkdir -p /tmp/sb_driver_cache && \
    chown -R seluser:seluser /home/seluser/.cache && \
    chmod -R 777 /home/seluser/.cache && \
    chmod -R 777 /tmp/sb_driver_cache

# Set environment variables
ENV CHROME_BIN=/usr/bin/google-chrome
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV SB_DRIVER_CACHE=/tmp/sb_driver_cache

# Create app directory owned by seluser
RUN chown -R seluser:seluser /app

# Switch back to seluser (the default user for selenium image)
USER seluser

# Run the application
CMD ["python3", "squash.py", "--mode", "prod"]