# ==============================================================================
# TelConnect Backend Dockerfile (Standalone Backend / Hugging Face Spaces)
# ==============================================================================

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    HOME=/home/user

# Install build dependencies and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user UID 1000 for Hugging Face Spaces
RUN useradd -m -u 1000 user

WORKDIR /app

# Upgrade pip and install CPU-only PyTorch
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend application source code
COPY . /app

# Ensure proper user permissions
RUN chown -R user:user /app /home/user

USER user
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

CMD ["uvicorn", "app.routes.main:app", "--host", "0.0.0.0", "--port", "7860"]
