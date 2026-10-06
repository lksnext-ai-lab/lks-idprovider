# LKS-idprovider API Specification

## Overview

This document defines the API specification for the LKS-idprovider library, consisting of two packages:

1. **lks-idprovider-api**: Pure API specification (protocols, models, types)
2. **lks-idprovider-keycloak**: Keycloak implementation + FastAPI integration

## Scope

### Core Functionality
1. **Token Validation**: Validate access and refresh tokens from identity providers
2. **Claims Extraction**: Extract user info, roles, and permissions from tokens
3. **Client Credentials**: Obtain client credentials from identity providers
4. **FastAPI Integration**: Seamless integration with FastAPI applications

### Non-Goals
- Admin operations (user management, realm configuration)
- Complex identity provider management
- Multi-protocol support (focus on OAuth2/OIDC)

## API Package Structure

```
lks-idprovider-api/
├── src/lks_idprovider/
│   ├── __init__.py
│   ├── protocols/
│   │   ├── __init__.py
│   │   ├── provider.py          # IdentityProvider protocol
│   │   └── client_credentials.py # ClientCredentialsProvider protocol
│   ├── models/
│   │   ├── __init__.py
│   │   ├── auth.py              # AuthContext, Identity, User, ClientIdentity, Role, Permission
│   │   ├── token.py             # Token models
│   │   ├── config.py            # Configuration models
│   │   └── errors.py            # Exception hierarchy
│   └── types/
│       ├── __init__.py
│       └── enums.py             # TokenType, AuthMethod enums
```

## Core Protocols

### 1. IdentityProvider Protocol

```python
from typing import Protocol, Optional, Dict, Any
from datetime import datetime
from .models.auth import AuthContext
from .models.token import TokenValidationResult


class IdentityProvider(Protocol):
    """Protocol for identity provider implementations."""

    async def validate_token(
        self, token: str, token_type: str = "access_token", **kwargs
    ) -> AuthContext:
        """Validate a token and return authentication context.

        Args:
            token: The token to validate
            token_type: Type of token ("access_token", "refresh_token")
            **kwargs: Provider-specific options

        Returns:
            AuthContext with identity, roles, and permissions

        Raises:
            TokenValidationError: If token is invalid
            TokenExpiredError: If token is expired
            ProviderError: If provider-specific error occurs
        """
        ...

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an access token using a refresh token.

        Args:
            refresh_token: The refresh token

        Returns:
            Dict containing new access_token, refresh_token, expires_in

        Raises:
            TokenValidationError: If refresh token is invalid
            ProviderError: If refresh fails
        """
        ...

    def get_provider_name(self) -> str:
        """Return the name of this provider (e.g., 'keycloak')."""
        ...

    def supports_token_type(self, token_type: str) -> bool:
        """Check if provider supports a specific token type."""
        ...
```

### 2. ClientCredentialsProvider Protocol

```python
from typing import Protocol, Dict, Any


class ClientCredentialsProvider(Protocol):
    """Protocol for client credentials flow."""

    async def get_client_credentials(
        self, scopes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get client credentials token.

        Args:
            scopes: Optional list of scopes to request

        Returns:
            Dict containing access_token, token_type, expires_in, scope

        Raises:
            ClientCredentialsError: If credentials are invalid
            ProviderError: If request fails
        """
        ...
```

## Core Models

### 1. Authentication Models

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass(frozen=True)
class Identity:
    """Base identity representation for users and clients."""

    id: str
    name: str
    identity_type: str  # "user" or "client"
    attributes: Dict[str, Any] = None


@dataclass(frozen=True)
class User(Identity):
    """Represents an authenticated user."""

    identity_type: str = "user"
    username: str = ""
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    def __post_init__(self):
        # Set name to username if not provided
        if not self.name and self.username:
            object.__setattr__(self, "name", self.username)


@dataclass(frozen=True)
class ClientIdentity(Identity):
    """Represents an authenticated client (service-to-service)."""

    identity_type: str = "client"
    client_id: str = ""
    client_name: Optional[str] = None
    scopes: List[str] = None

    def __post_init__(self):
        # Set name to client_name or client_id if not provided
        if not self.name:
            display_name = self.client_name or self.client_id
            object.__setattr__(self, "name", display_name)
        # Set id to client_id if not provided
        if not self.id and self.client_id:
            object.__setattr__(self, "id", self.client_id)


@dataclass(frozen=True)
class Role:
    """Represents a user role."""

    name: str
    description: Optional[str] = None
    client: Optional[str] = None  # For client-specific roles


@dataclass(frozen=True)
class Permission:
    """Represents a permission."""

    resource: str
    action: str
    scope: Optional[str] = None


@dataclass(frozen=True)
class AuthContext:
    """Complete authentication context."""

    identity: Identity  # Always present - either User or ClientIdentity
    roles: List[Role] = None
    permissions: List[Permission] = None
    token_expires_at: Optional[datetime] = None
    refresh_expires_at: Optional[datetime] = None
    provider: str = ""
    scopes: List[str] = None

    @property
    def identity_type(self) -> str:
        """Return the type of identity: 'user' or 'client'."""
        return self.identity.identity_type

    @property
    def identity_name(self) -> str:
        """Return the name/identifier of the identity."""
        return self.identity.name

    @property
    def identity_id(self) -> str:
        """Return the ID of the identity."""
        return self.identity.id

    @property
    def user(self) -> Optional[User]:
        """Return User if identity is a user, None otherwise."""
        return self.identity if isinstance(self.identity, User) else None

    @property
    def client(self) -> Optional[ClientIdentity]:
        """Return ClientIdentity if identity is a client, None otherwise."""
        return self.identity if isinstance(self.identity, ClientIdentity) else None
```

### 2. Token Models

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from .types.enums import TokenType


@dataclass(frozen=True)
class TokenInfo:
    """Token information and metadata."""

    token: str
    token_type: TokenType
    expires_at: Optional[datetime] = None
    issued_at: Optional[datetime] = None
    issuer: Optional[str] = None
    audience: Optional[str] = None
    subject: Optional[str] = None
    scopes: List[str] = None


@dataclass(frozen=True)
class TokenValidationResult:
    """Result of token validation."""

    is_valid: bool
    token_info: Optional[TokenInfo] = None
    error: Optional[str] = None
    auth_context: Optional[AuthContext] = None
```

### 3. Configuration Models

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    """Base configuration for identity providers."""

    provider_name: str
    base_url: str
    timeout: int = Field(default=30, ge=1, le=300)
    verify_ssl: bool = True
    debug: bool = False


class KeycloakConfig(ProviderConfig):
    """Keycloak-specific configuration."""

    provider_name: str = "keycloak"
    realm: str
    client_id: str
    client_secret: Optional[str] = None

    # JWT validation settings
    validate_audience: bool = True
    validate_issuer: bool = True
    leeway: int = Field(default=0, ge=0, le=300)  # Clock skew tolerance

    # Caching settings
    jwks_cache_ttl: int = Field(default=300, ge=60, le=3600)  # 5 minutes

    # Client credentials settings
    client_credentials_scope: Optional[str] = None
```

### 4. Error Models

```python
class LKSIdProviderError(Exception):
    """Base exception for all LKS ID Provider errors."""

    pass


class TokenValidationError(LKSIdProviderError):
    """Token validation failed."""

    pass


class TokenExpiredError(TokenValidationError):
    """Token has expired."""

    pass


class TokenMalformedError(TokenValidationError):
    """Token is malformed or invalid format."""

    pass


class ClientCredentialsError(LKSIdProviderError):
    """Client credentials flow failed."""

    pass


class ProviderError(LKSIdProviderError):
    """Provider-specific error."""

    pass


class ConfigurationError(LKSIdProviderError):
    """Configuration is invalid."""

    pass
```

## Types and Enums

```python
from enum import Enum


class TokenType(str, Enum):
    """Supported token types."""

    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    ID_TOKEN = "id_token"


class AuthMethod(str, Enum):
    """Authentication methods."""

    BEARER = "bearer"
    CLIENT_CREDENTIALS = "client_credentials"
```

## Usage Examples

### Basic Token Validation

```python
from lks_idprovider.protocols.provider import IdentityProvider
from lks_idprovider.models.config import KeycloakConfig

# Configure provider
config = KeycloakConfig(
    base_url="http://localhost:8080", realm="myrealm", client_id="myclient"
)

# Validate user token
provider: IdentityProvider = KeycloakProvider(config)
auth_context = await provider.validate_token("eyJ0eXAiOiJKV1Q...")

# Work with unified Identity interface
print(f"Identity: {auth_context.identity.name} ({auth_context.identity.identity_type})")
print(f"ID: {auth_context.identity.id}")

# Access type-specific properties if needed
if auth_context.user:
    print(f"User email: {auth_context.user.email}")
    print(f"Roles: {[role.name for role in auth_context.roles]}")
elif auth_context.client:
    print(f"Client ID: {auth_context.client.client_id}")
    print(f"Scopes: {auth_context.scopes}")

# Or use convenience properties
print(f"Identity: {auth_context.identity_name} ({auth_context.identity_type})")
```

### Client Credentials Flow

```python
from lks_idprovider.protocols.client_credentials import ClientCredentialsProvider

# Get client credentials
provider: ClientCredentialsProvider = KeycloakProvider(config)
credentials = await provider.get_client_credentials(scopes=["read", "write"])

access_token = credentials["access_token"]
expires_in = credentials["expires_in"]

# Validate the client credentials token
auth_context = await provider.validate_token(access_token)
print(f"Client: {auth_context.identity.name}")
print(f"Type: {auth_context.identity.identity_type}")
print(f"Scopes: {auth_context.scopes}")
```

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from lks_idprovider.models.auth import AuthContext
from lks_idprovider_keycloak.fastapi import get_auth_context, require_roles

app = FastAPI()


@app.get("/protected")
async def protected_endpoint(auth: AuthContext = Depends(get_auth_context)):
    # Work with unified Identity interface
    return {
        "identity": auth.identity.name,
        "type": auth.identity.identity_type,
        "id": auth.identity.id,
    }


@app.get("/admin")
@require_roles(["admin"])
async def admin_endpoint(auth: AuthContext = Depends(get_auth_context)):
    return {"admin_data": "secret", "identity": auth.identity_name}


@app.get("/service")
async def service_endpoint(auth: AuthContext = Depends(get_auth_context)):
    # Handle both user and client authentication uniformly
    return {
        "service_data": f"Hello {auth.identity.name}",
        "identity_type": auth.identity.identity_type,
        "scopes": auth.scopes if auth.identity.identity_type == "client" else None,
    }


@app.get("/user-specific")
async def user_specific_endpoint(auth: AuthContext = Depends(get_auth_context)):
    # Access user-specific properties when needed
    if auth.user:
        return {
            "user_email": auth.user.email,
            "full_name": f"{auth.user.first_name} {auth.user.last_name}",
            "roles": [role.name for role in auth.roles],
        }
    else:
        raise HTTPException(status_code=403, detail="User authentication required")
```

## Implementation Requirements

### For Provider Implementations

1. **Must implement both protocols**: `IdentityProvider` and `ClientCredentialsProvider`
2. **Async support**: All methods must be async-compatible
3. **Error handling**: Proper exception mapping to API error types
4. **Configuration validation**: Use Pydantic models for config validation
5. **Logging**: Structured logging for debugging and monitoring

### For Framework Integrations

1. **Dependency injection**: Provide clean dependency injection patterns
2. **Error handling**: Map provider errors to HTTP status codes
3. **OpenAPI integration**: Proper security scheme documentation
4. **Middleware support**: Optional middleware for automatic token validation
5. **Testing utilities**: Provide test fixtures and mocks

## Validation Rules

### Token Validation
- JWT signature verification (for JWT tokens)
- Expiration time validation (`exp` claim)
- Not-before time validation (`nbf` claim)
- Issuer validation (`iss` claim)
- Audience validation (`aud` claim)
- Custom claims validation (provider-specific)

### Configuration Validation
- Required fields must be present
- URL formats must be valid
- Timeout values must be reasonable
- SSL verification settings must be boolean

## Extension Points

### Custom Providers
Implement the `IdentityProvider` and `ClientCredentialsProvider` protocols:

```python
class CustomProvider(IdentityProvider, ClientCredentialsProvider):
    def __init__(self, config: CustomConfig):
        self.config = config

    async def validate_token(self, token: str, **kwargs) -> AuthContext:
        # Custom implementation that returns AuthContext with Identity
        pass

    async def get_client_credentials(self, scopes=None) -> Dict[str, Any]:
        # Custom implementation
        pass
```

### Custom Framework Integration
Follow the patterns established in the FastAPI integration for other frameworks.

## Security Considerations

1. **Token Storage**: Never log or store tokens in plain text
2. **Clock Skew**: Allow configurable leeway for token expiration
3. **Key Rotation**: Handle JWKS key rotation gracefully
4. **Rate Limiting**: Implement reasonable rate limits for provider calls
5. **Secure Defaults**: Use secure defaults for all configuration options
6. **Input Validation**: Validate all inputs before processing
7. **Error Information**: Don't leak sensitive information in error messages

This specification provides a clean, focused API that supports the core use cases while remaining extensible for future needs.
