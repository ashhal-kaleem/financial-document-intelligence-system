FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# Install system build dependencies for PyMuPDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copy dependency specifications
COPY pyproject.toml uv.lock ./

# Install python dependencies
RUN uv sync --frozen --no-dev

# Copy backend source code
COPY src/ ./src/
COPY README.md ./

EXPOSE 8000

# Start FastAPI via uvicorn binding to Render PORT
CMD ["sh", "-c", "uv run uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
