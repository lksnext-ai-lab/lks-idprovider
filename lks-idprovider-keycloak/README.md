# LKS-idprovider Keycloak

Keycloak provider implementation for the LKS Identity Provider library with FastAPI integration.

## Overview

This package provides a complete Keycloak implementation of the LKS-idprovider API specification, including:

- **Keycloak Provider**: Complete implementation using Keycloak's REST API and token introspection
- **FastAPI Integration**: Seamless integration with FastAPI applications
- **Unified Identity Support**: Support for both user and client authentication flows
- **Client Credentials**: OAuth2 client credentials flow implementation
- **Caching Support**: Optional Redis caching for improved performance

## Key Features

- **REST API First**: Uses Keycloak's token introspection API for reliable validation
- **JWT Support**: Optional JWT validation for performance optimization
- **Async/Await**: Full async support for high-performance applications
- **Type Safety**: Complete type hints and Pydantic validation
- **FastAPI Dependencies**: Ready-to-use FastAPI dependencies and decorators
- **Error Handling**: Comprehensive error handling with proper HTTP status mapping

## Installation

```bash
# Basic installation
pip install lks-idprovider-keycloak

# With FastAPI support
pip install lks-idprovider-keycloak[fastapi]

# With Redis caching support
pip install lks-idprovider-keycloak[redis]

# Full installation with all optional dependencies
pip install lks-idprovider-keycloak[all]
```

## Quick Start

### Basic Configuration

```python
from lks_idprovider_keycloak import KeycloakProvider, KeycloakConfig

# Configure Keycloak provider
config = KeycloakConfig(
    base_url="http://localhost:8080",
    realm="myrealm",
    client_id="myclient",
    client_secret="mysecret",  # Optional, for client credentials
)

provider = KeycloakProvider(config)
```

### Token Validation

```python
# Validate user token
auth_context = await provider.validate_token("eyJ0eXAiOiJKV1Q...")

# Handle both user and client tokens uniformly
print(f"Identity: {auth_context.identity.name} ({auth_context.identity.identity_type})")

# Access user-specific information
if auth_context.user:
    print(f"User email: {auth_context.user.email}")
    print(f"Roles: {[role.name for role in auth_context.roles]}")

# Access client-specific information
if auth_context.client:
    print(f"Client ID: {auth_context.client.client_id}")
    print(f"Scopes: {auth_context.scopes}")
```

### Client Credentials Flow

```python
# Get client credentials token
credentials = await provider.get_client_credentials(scopes=["read", "write"])
access_token = credentials["access_token"]

# Validate the client token
auth_context = await provider.validate_token(access_token)
print(f"Client: {auth_context.identity.name}")
```

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from lks_idprovider_keycloak.fastapi import get_auth_context, require_roles
from lks_idprovider.models.auth import AuthContext

app = FastAPI()

# Configure the provider (usually done in startup)
# provider = KeycloakProvider(config)


@app.get("/protected")
async def protected_endpoint(auth: AuthContext = Depends(get_auth_context)):
    return {
        "identity": auth.identity.name,
        "type": auth.identity.identity_type,
        "id": auth.identity.id,
    }


@app.get("/admin")
@require_roles(["admin"])
async def admin_endpoint(auth: AuthContext = Depends(get_auth_context)):
    return {"message": "Admin access granted"}


@app.get("/user-only")
async def user_only_endpoint(
    user=Depends(get_user),  # Only accepts User identities
):
    return {"email": user.email, "full_name": f"{user.first_name} {user.last_name}"}


@app.get("/service-only")
async def service_only_endpoint(
    client=Depends(get_client_identity),  # Only accepts ClientIdentity
):
    return {"client_id": client.client_id, "scopes": client.scopes}
```

## Configuration

### Environment Variables

```bash
# Keycloak configuration
KEYCLOAK_BASE_URL=http://localhost:8080
KEYCLOAK_REALM=myrealm
KEYCLOAK_CLIENT_ID=myclient
KEYCLOAK_CLIENT_SECRET=mysecret

# Optional settings
KEYCLOAK_TIMEOUT=30
KEYCLOAK_VERIFY_SSL=true
KEYCLOAK_DEBUG=false
```

### Advanced Configuration

```python
from lks_idprovider_keycloak import KeycloakConfig

config = KeycloakConfig(
    base_url="http://localhost:8080",
    realm="myrealm",
    client_id="myclient",
    client_secret="mysecret",
    # JWT validation settings
    validate_audience=True,
    validate_issuer=True,
    leeway=30,  # Clock skew tolerance in seconds
    # Caching settings
    jwks_cache_ttl=300,  # JWKS cache TTL in seconds
    # HTTP client settings
    timeout=30,
    verify_ssl=True,
    debug=False,
)
```

## Related Packages

- **lks-idprovider-api**: API specification with protocols and models
