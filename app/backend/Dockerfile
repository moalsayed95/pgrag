FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first (cache layer)
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ src/

# Expose port
EXPOSE 8000

# Run FastAPI
CMD ["uv", "run", "fastapi", "run", "src/pg_rag/main.py", "--host", "0.0.0.0", "--port", "8000"]
