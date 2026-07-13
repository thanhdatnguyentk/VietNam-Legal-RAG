FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[dev]" && \
    pip install --no-cache-dir uvicorn[standard] fastapi rank_bm25 accelerate

# Copy scripts
COPY scripts/ scripts/

EXPOSE 8000

CMD ["uvicorn", "vietnam_legal_rag.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
