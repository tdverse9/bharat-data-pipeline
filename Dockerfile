FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required for Playwright and C-extensions
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download required spaCy model and Playwright browser binaries
RUN python -m spacy download en_core_web_sm
RUN playwright install-deps
RUN playwright install chromium

# Copy project source code into container
COPY . .

# Grant execution permissions to driver script
RUN chmod +x run.sh

# Run unit tests and execute the full pipeline by default
CMD ["/bin/bash", "-c", "pytest tests/ && ./run.sh"]