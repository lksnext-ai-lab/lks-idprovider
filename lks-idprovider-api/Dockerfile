# Dockerfile for lks-idprovider-api
#
# Build context is the REPO ROOT, not this directory: uv resolves against the
# shared workspace pyproject.toml + uv.lock, e.g.:
#   docker build -f lks-idprovider-api/Dockerfile --target tester -t <tag> .

# 1. Base Stage: Common setup for all subsequent stages
FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv
RUN pip install uv

# Copy the workspace root (uv needs it to resolve) plus this package — it has no
# workspace-sibling dependencies, so nothing else needs to be present.
COPY pyproject.toml uv.lock ./
COPY lks-idprovider-api ./lks-idprovider-api

WORKDIR /app/lks-idprovider-api

# 2. Dependencies Stage: Install all dependencies including dev
FROM base as dependencies

RUN uv sync --group dev --frozen

# 3. Linter Stage: Run code quality checks
FROM dependencies as linter

RUN uv run black --check src tests_api && \
    uv run isort --check-only src tests_api && \
    uv run ruff check src tests_api && \
    uv run mypy src

# 4. Tester Stage: Run tests
FROM dependencies as tester

RUN uv run pytest tests_api --ignore=tests_api/integration

# 5. Builder Stage: Build the distributable package
FROM dependencies as builder

RUN uv build --out-dir dist
