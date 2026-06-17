# Fixed Dockerfile for selenium/standalone-chrome
FROM selenium/standalone-chrome:latest

# Switch to root to fix permissions and install Python
USER root

# Install Python and PyAutoGUI dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-tk \
    python3-dev \
    xvfb \
    scrot \
    python3-xlib \
    xdotool \
    x11-utils \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

# Fix SeleniumBase driver permissions (install location varies)
RUN chmod -R 777 /usr/local/lib/python*/site-packages/seleniumbase/drivers 2>/dev/null || \
    chmod -R 777 /usr/lib/python*/site-packages/seleniumbase/drivers 2>/dev/null || true

# Copy application files and startup script
COPY . .
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Create writable cache directories for selenium and seleniumbase
RUN mkdir -p /home/seluser/.cache/selenium && \
    chown -R seluser:seluser /home/seluser/.cache && \
    chmod -R 777 /home/seluser/.cache

# Set environment variables
ENV CHROME_BIN=/usr/bin/google-chrome
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create app directory owned by seluser and X11 socket directory
RUN chown -R seluser:seluser /app && \
    mkdir -p /tmp/.X11-unix && \
    chmod 1777 /tmp/.X11-unix

# Switch back to seluser (the default user for selenium image)
USER seluser

# Run the startup script
CMD ["/app/start.sh"]