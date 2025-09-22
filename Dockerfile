# Fixed Dockerfile for selenium/standalone-chrome
FROM selenium/standalone-chrome:latest

# Switch to root to fix permissions and install Python
USER root

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

# Copy application files
COPY . .

# Create writable cache directories for selenium
RUN mkdir -p /home/seluser/.cache/selenium && \
    chown -R seluser:seluser /home/seluser/.cache && \
    chmod -R 755 /home/seluser/.cache

# Set environment variables
ENV CHROME_BIN=/usr/bin/google-chrome
ENV DISPLAY=:99

# Create app directory owned by seluser
RUN chown -R seluser:seluser /app

# Switch back to seluser (the default user for selenium image)
USER seluser

# Run the application
CMD ["python3", "squash.py", "--mode", "prod"]