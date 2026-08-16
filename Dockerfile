FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app
COPY config.json .

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "app.main"]
