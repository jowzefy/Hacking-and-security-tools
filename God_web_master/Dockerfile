FROM python:3.11-slim

LABEL maintainer="God_Web_Master"
LABEL description="Professional Web Scanner"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -s /bin/bash scanner && \
    chown -R scanner:scanner /app
USER scanner

# Create output directory
RUN mkdir -p output logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
ENTRYPOINT ["python", "app/main.py"]
CMD ["--interactive"]