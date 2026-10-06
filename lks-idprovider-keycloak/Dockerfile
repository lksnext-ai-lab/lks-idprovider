# Multi-stage Dockerfile for LKS Identity Provider Keycloak Implementation
#
# Build context is the REPO ROOT, not this directory: uv resolves this package's
# dependencies against the shared workspace pyproject.toml + uv.lock, and needs
# every declared workspace member's pyproject.toml to exist on disk even though
# only lks-idprovider-keycloak is installed/built here, e.g.:
#   docker build --target builder -f lks-idprovider-keycloak/Dockerfile -t <tag> .
#
# Stage 1: Build stage with uv and development dependencies
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set work directory
WORKDIR /app

# Copy the workspace root (uv needs it to resolve) plus this package and the one
# workspace sibling it actually depends on (lks-idprovider-api) — entraid and
# fastapi aren't needed to build this package.
COPY pyproject.toml uv.lock ./
COPY lks-idprovider-api ./lks-idprovider-api
COPY lks-idprovider-keycloak ./lks-idprovider-keycloak

WORKDIR /app/lks-idprovider-keycloak

# Install this package + its dev group, from the locked workspace
RUN uv sync --group dev --frozen

# Build the package
RUN uv build --out-dir dist

# Stage 2: Publishing stage with minimal dependencies
FROM python:3.11-slim AS publisher

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install uv (only needed for publishing)
RUN pip install uv

# Set work directory
WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 publisher \
    && chown -R publisher:publisher /app

# Copy built package and pyproject.toml
# (no coverage.xml here: the builder stage doesn't run tests — coverage is
# produced by the Jenkinsfile's own `docker run` step against the live checkout,
# not by this image build, so there's nothing to copy)
COPY --from=builder /app/lks-idprovider-keycloak/dist ./dist
COPY --from=builder /app/lks-idprovider-keycloak/pyproject.toml ./

# Fix ownership of copied files
RUN chown -R publisher:publisher /app

# Switch to non-root user
USER publisher

# Default command for publishing (will be overridden in Jenkins)
CMD ["echo", "Build completed successfully. Use 'uv publish' to publish to repository."]

# Stage 3: Development stage for local development
FROM builder AS development

# Install additional development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    make \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash developer
RUN chown -R developer:developer /app
USER developer

# Default command for development
CMD ["/bin/bash"]
