FROM python:3.12-slim-bookworm AS builder

WORKDIR /api

COPY --from=ghcr.io/astral-sh/uv:0.11.8 /uv /uvx /bin/

ENV UV_PROJECT_ENVIRONMENT=/api/.venv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev


FROM python:3.12-slim-bookworm AS runtime

WORKDIR /api

ENV PATH="/api/.venv/bin:$PATH"

COPY --from=builder /api/.venv /api/.venv

# 复制应用代码
COPY . .

RUN chmod +x /api/bin/boot.sh

EXPOSE 8000

ENTRYPOINT ["/api/bin/boot.sh"]
