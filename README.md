# LKS Identity Provider Python

[![Python Support](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A modular Python library for identity provider integration with support for multiple providers and web frameworks.

## Project Structure

This repository contains two separate packages:

### 📦 [lks-idprovider-api](./lks-idprovider-api/)
Pure API specification package containing:
- **Protocols**: Contracts for identity provider implementations
- **Models**: Data models for authentication context, identities, tokens
- **Types**: Enums and type definitions
- **Contracts**: Validation and lifecycle contracts

### 🔐 [lks-idprovider-keycloak](./lks-idprovider-keycloak/)
Keycloak provider implementation package containing:
- **Keycloak Provider**: Complete REST API implementation
- **FastAPI Integration**: Dependencies, and middleware
- **Client Credentials**: OAuth2 client credentials flow
- **Caching Support**: Optional Redis caching

## Quick Start

### Installation

```bash
# Install API specification only
pip install lks-idprovider-api

# Install Keycloak provider with FastAPI support
pip install lks-idprovider-keycloak[fastapi]
```

### Basic Usage

```python
from lks_idprovider_keycloak import KeycloakProvider, KeycloakConfig

# Configure provider
config = KeycloakConfig(
    base_url="http://localhost:8080", realm="myrealm", client_id="myclient"
)

provider = KeycloakProvider(config)

# Validate token
auth_context = await provider.validate_token("eyJ0eXAiOiJKV1Q...")

# Work with unified Identity model
print(f"Identity: {auth_context.identity.name} ({auth_context.identity.identity_type})")

if auth_context.user:
    print(f"User: {auth_context.user.email}")
elif auth_context.client:
    print(f"Client: {auth_context.client.client_id}")
```

## Installation

The packages are distributed as GitHub Release assets (not on PyPI). Each release is tagged `<package>-v<version>`
(e.g. `api-v0.1.7`, `keycloak-v0.1.5`, `entraid-v0.1.4`, `fastapi-v0.1.1`) and carries the wheel and sdist.

Add the packages to your `pyproject.toml` and point `uv` at the release assets. `lks-idprovider-api` must always be
declared too, because the other packages depend on it and `uv` would otherwise look for it on PyPI:

```toml
[project]
dependencies = ["lks-idprovider-api", "lks-idprovider-keycloak"]

[tool.uv.sources]
lks-idprovider-api = { url = "https://github.com/lksnext-ai-lab/lks-idprovider/releases/download/api-v0.1.7/lks_idprovider_api-0.1.7-py3-none-any.whl" }
lks-idprovider-keycloak = { url = "https://github.com/lksnext-ai-lab/lks-idprovider/releases/download/keycloak-v0.1.5/lks_idprovider_keycloak-0.1.5-py3-none-any.whl" }
```

Alternatively, install straight from a tag:

```toml
[tool.uv.sources]
lks-idprovider-api = { git = "https://github.com/lksnext-ai-lab/lks-idprovider", tag = "api-v0.1.7", subdirectory = "lks-idprovider-api" }
```

## Documentation

- [API Specification](./API_SPECIFICATION.md)
- [Implementation Plan](./IMPLEMENTATION_PLAN.md)
- [Protocol Documentation](https://lks-idprovider.readthedocs.io/protocols/)
- [Model Reference](https://lks-idprovider.readthedocs.io/models/)

## Related Packages

- **lks-idprovider-keycloak**: Keycloak provider implementation with FastAPI integration
- **lks-idprovider-auth0**: Auth0 provider implementation (planned)
- **lks-idprovider-azure**: Azure AD provider implementation (planned)

## Development

Each package can be developed independently:

```bash
# API package development
cd lks-idprovider-api
poetry install --with dev
poetry run pytest

# Keycloak package development
cd lks-idprovider-keycloak
poetry install --with dev --extras all
poetry run pytest
```

## Architecture

The library follows a clean architecture with separation of concerns:

- **API Package**: Pure specifications and contracts (no implementation)
- **Provider Packages**: Specific implementations (Keycloak, Auth0, etc.)
- **Framework Integrations**: Web framework specific utilities (FastAPI, Django, etc.)

### Unified Identity Model

Both users and clients are represented through a common `Identity` interface:

- **User**: Authenticated end-users with profile information
- **ClientIdentity**: Authenticated services (client credentials flow)
- **AuthContext**: Contains identity + authorization information (roles, scopes)

This design allows applications to handle both user and service authentication uniformly while maintaining type safety for specific use cases.

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Format code
poetry run black src tests
poetry run isort src tests

# Type checking
poetry run mypy src
```

## Contributing

We welcome contributions from the LKS S. Coop. community! To contribute to this project, please follow these guidelines:

Fork the repository and create a new branch for your changes.
Ensure your changes adhere to the project's coding standards and best practices.
Make sure to include appropriate tests for your changes.
Submit a pull request, explaining the purpose and details of your changes.
All contributions are subject to the GNU Affero General Public License v3.0 (AGPL-3.0-only).

By contributing to this project, you agree to license your contributions under the AGPL-3.0-only.
## License

This project is licensed under the GNU Affero General Public License v3.0 only (AGPL-3.0-only).
For more information, please refer to the [LICENSE](LICENSE) file in this repository.

## Changelog

### 0.1.0 (2025-06-30)

- Initial release
- Core protocols and models
- Unified Identity model (User/ClientIdentity)
- Base configuration and error handling
- Full type safety with Pydantic models
