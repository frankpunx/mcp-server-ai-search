# ------------------- Stage 1: Build Stage ------------------------------
FROM python:3.13-alpine AS build

# Install build dependencies for packages with native extensions
RUN apk add --no-cache gcc g++ musl-dev python3-dev libffi-dev openssl-dev cargo pkgconfig

COPY --from=ghcr.io/astral-sh/uv:0.9.14 /uv /uvx /bin/

WORKDIR /code

# Copy dependency files and install dependencies (for layer caching)
COPY uv.lock pyproject.toml ./
RUN uv sync --locked --no-install-project

# Copy the project and sync
COPY . .
RUN uv sync --locked

# ------------------- Stage 2: Final Stage ------------------------------
FROM python:3.13-alpine AS final

RUN addgroup -S app && adduser -S app -G app

COPY --from=build --chown=app:app /code /code

WORKDIR /code/src/server
USER app

ENV PATH="/code/.venv/bin:$PATH"

EXPOSE 8000

CMD ["python", "basic_mcp_http.py"]
