FROM python:3.14-slim

WORKDIR /app

COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache --no-dev

WORKDIR /app

COPY . .

# Avoid python to write bytecode and buffer output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD uv run manage.py migrate && uv run manage.py runserver 0.0.0.0:8000
