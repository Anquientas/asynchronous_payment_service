FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /bin/uv
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"
COPY pyproject.toml uv.lock .
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini README.md .
RUN uv sync --frozen --no-dev
CMD ["uvicorn", "payment_service.bootstrap.api:app", "--host", "0.0.0.0", "--port", "8000"]
