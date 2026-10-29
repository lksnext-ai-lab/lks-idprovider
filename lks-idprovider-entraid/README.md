# LKS-idprovider Entra ID

Azure Entra ID (formerly Azure Active Directory) provider implementation for the LKS Identity Provider library.

## Overview

This package provides a complete Azure Entra ID implementation of the LKS-idprovider API specification, including:

- **Azure Entra ID Provider**: Complete implementation using Microsoft's azure.identity SDK and JWT validation
- **Microsoft Graph Integration**: Seamless integration with Microsoft Graph API for user information
- **Client Credentials Support**: OAuth2 client credentials flow using azure.identity
- **JWT Validation**: Token validation using PyJWT with JWKS
- **Unified Identity Support**: Support for both user and client authentication flows
- **Multiple Auth Methods**: Support for client secrets, certificates, and managed identities

## Status

🚧 **Work in Progress** - This package is currently under development.

## Key Features

- **Azure Identity SDK**: Uses Microsoft's official azure.identity library for authentication
- **Automatic Token Management**: Token caching and refresh handled by azure.identity
- **JWT Validation**: Token validation with JWKS for security
- **Microsoft Graph API**: Native integration with Microsoft Graph for user information
- **Multiple Credential Types**: Support for client secrets, certificates, and managed identities
- **Async/Await**: Full async support for high-performance applications
- **Type Safety**: Complete type hints and Pydantic validation
- **FastAPI Integration**: Compatible with lks-idprovider-fastapi

## Installation

Install the Entra ID and API packages from compatible GitHub Release assets.
The API package must be supplied explicitly because GitHub Releases is not a
package index. See the [repository installation guidance](https://github.com/lksnext-ai-lab/lks-idprovider#installation-and-integration)
and [releases](https://github.com/lksnext-ai-lab/lks-idprovider/releases).

## Quick Start

### Basic Configuration

```python
from lks_idprovider_entraid import EntraIDConfig, EntraIDProvider

# Configure Azure Entra ID provider
config = EntraIDConfig(
    tenant_id="your-tenant-id",  # or "common" for multi-tenant
    client_id="your-client-id",
    client_secret="your-client-secret",
)

provider = EntraIDProvider(config)
```

### Token Validation

```python
# Validate user token
async with provider:
    auth_context = await provider.get_auth_context("eyJ0eXAiOiJKV1Q...")

    print(f"Identity: {auth_context.identity.name}")
    print(f"Type: {auth_context.identity.identity_type}")
    print(f"Roles: {[role.name for role in auth_context.roles]}")
```

## Configuration

### Environment Variables

```bash
# Azure Entra ID configuration
ENTRAID_TENANT_ID=your-tenant-id
ENTRAID_CLIENT_ID=your-client-id
ENTRAID_CLIENT_SECRET=your-client-secret

# Optional settings
ENTRAID_AUTHORITY_HOST=login.microsoftonline.com
ENTRAID_API_VERSION=v1.0
ENTRAID_TIMEOUT=30
ENTRAID_VERIFY_SSL=true
```

### Advanced Configuration

```python
from lks_idprovider_entraid import EntraIDConfig

config = EntraIDConfig(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret",
    # JWT validation settings
    validate_audience=True,
    validate_issuer=True,
    leeway=30,  # Clock skew tolerance
    # Caching settings
    jwks_cache_ttl=300,
    token_cache_ttl=60,
    # Microsoft Graph settings
    api_version="v1.0",  # or "beta"
    # HTTP client settings
    timeout=30,
    verify_ssl=True,
)
```

### Certificate-Based Authentication

```python
config = EntraIDConfig(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    certificate_path="/path/to/cert.pem",
    certificate_password="cert-password",
)
```

### Managed Identity Authentication

```python
config = EntraIDConfig(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    use_managed_identity=True,  # For Azure resources
)
```

## Project Structure

```
lks-idprovider-entraid/
├── src/
│   └── lks_idprovider_entraid/
│       ├── __init__.py
│       ├── config.py              # EntraIDConfig
│       ├── provider.py            # EntraIDProvider (TODO)
│       ├── client_credentials_provider.py  # (TODO)
│       ├── utils.py               # (TODO)
│       └── rest/
│           └── entraid_client.py  # (TODO)
└── tests_entraid/
    ├── conftest.py
    ├── test_config.py
    └── ...
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/lksnext-ai-lab/lks-idprovider.git
cd lks-idprovider/lks-idprovider-entraid

# Activate virtual environment (PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
poetry install --with dev

# Run tests
poetry run pytest tests_entraid/ -v

# Run tests with coverage
poetry run pytest tests_entraid/ --cov=src/lks_idprovider_entraid --cov-report=html
```

## Related Packages

- **lks-idprovider-api**: API specification with protocols and models
- **lks-idprovider-keycloak**: Keycloak provider implementation
- **lks-idprovider-fastapi**: FastAPI integration

## Documentation

See the [integration test setup](https://github.com/lksnext-ai-lab/lks-idprovider/blob/main/docs/entraid/integration-setup.md)
and [integration test guide](https://github.com/lksnext-ai-lab/lks-idprovider/blob/main/docs/entraid/integration-tests.md).

## License

Copyright © LKS Next

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.
