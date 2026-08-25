# ==============================================================================
# TelConnect Backend Dockerfile (Optimized for Hugging Face Spaces)
# ==============================================================================

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    HOME=/home/user

# Install system build dependencies and curl for health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with UID 1000 required for Hugging Face Spaces security
RUN useradd -m -u 1000 user

WORKDIR /app

# Upgrade pip and install CPU-only PyTorch for fast, lightweight builds
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy and install backend requirements
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend application source code
COPY backend /app

# Ensure non-root user has full read/write permissions
RUN chown -R user:user /app /home/user

USER user

# Expose standard Hugging Face Spaces port
EXPOSE 7860

# Container health probe
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Start FastAPI server on port 7860
CMD ["uvicorn", "app.routes.main:app", "--host", "0.0.0.0", "--port", "7860"]
