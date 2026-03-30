FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app/clinical_trial_auditor/
COPY server/app.py /app/server_app.py

# Create a simple launcher that sets up the module path
RUN echo 'import sys; sys.path.insert(0, "/app"); \
from clinical_trial_auditor.server.app import app' > /app/main.py

# Expose port for HF Spaces
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run the server
CMD ["uvicorn", "clinical_trial_auditor.server.app:app", "--host", "0.0.0.0", "--port", "7860"]
