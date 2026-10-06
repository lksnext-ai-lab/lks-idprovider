"""
Common fixtures and test utilities for FastAPI authentication tests.
"""

import httpx
import pytest
from fastapi import HTTPException

from lks_idprovider.models.auth import AuthContext
from lks_idprovider.models.identity import User
from lks_idprovider.models.identity.client_identity import ClientIdentity
from lks_idprovider.models.role import Role
from lks_idprovider.models.token import TokenInfo
from lks_idprovider.protocols import ClientCredentialsProvider, IdentityProvider
from lks_idprovider.types.enums import TokenType

INVALID_TOKEN_MESSAGE = "Invalid token"


def get_access_token(config, username=None, password=None, client_credentials=False):
    token_url = f"{config.base_url}/realms/{config.realm}/protocol/openid-connect/token"
    data = {
        "client_id": config.client_id,
        "client_secret": config.client_secret,
    }
    if client_credentials:
        data["grant_type"] = "client_credentials"
    else:
        data["grant_type"] = "password"
        data["username"] = username
        data["password"] = password
        data["scope"] = "openid"
    response = httpx.post(token_url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]


@pytest.fixture
def mock_user():
    """Create a mock user identity."""
    return User(
        id="testuser",
        name="testuser",  # Required by base Identity class
        username="testuser",
        email="test@example.com",
    )


@pytest.fixture
def mock_client_identity():
    """Create a mock client identity."""
    return ClientIdentity(id="client123", name="testclient", client_id="testclient")


@pytest.fixture
def mock_roles():
    """Create mock roles."""
    return [
        Role(name="admin", description="Administrator role"),
        Role(name="user", description="User role"),
        Role(name="manager", client="app1", description="Manager for app1"),
        Role(name="editor", description="Editor role"),
    ]


@pytest.fixture
def mock_token_info():
    """Create mock token info."""
    return TokenInfo(
        token="mock.jwt.token",  # Required field
        token_type=TokenType.ACCESS_TOKEN,  # Must be a valid enum value
        subject="testuser",
        issuer="keycloak",
        audience="app1",  # Must be a string, not a list
        expires_at=None,
        issued_at=None,
    )


@pytest.fixture
def mock_auth_context(mock_user, mock_roles, mock_token_info):
    """Create a mock authentication context with roles."""
    return AuthContext(
        identity=mock_user,
        roles=mock_roles,
        provider="keycloak",
        token_info=mock_token_info,
    )


@pytest.fixture
def mock_auth_context_no_roles(mock_user, mock_token_info):
    """Create a mock authentication context with no roles."""
    return AuthContext(
        identity=mock_user, roles=[], provider="keycloak", token_info=mock_token_info
    )


@pytest.fixture
def mock_client_auth_context(mock_client_identity, mock_roles, mock_token_info):
    """Create a mock client authentication context."""
    return AuthContext(
        identity=mock_client_identity,
        roles=mock_roles,
        provider="keycloak",
        token_info=mock_token_info,
    )


@pytest.fixture
def mock_identity_provider(mock_auth_context):
    """Create a mock identity provider."""
    return MockIdentityProvider(mock_auth_context, should_fail=False)  # type: ignore


@pytest.fixture
def mock_identity_provider_fail():
    """Create a mock identity provider that fails authentication."""
    return MockIdentityProvider(should_fail=True)  # type: ignore


@pytest.fixture
def mock_client_provider(mock_client_auth_context):
    """Create a mock client credentials provider."""
    return MockClientCredentialsProvider(mock_client_auth_context, should_fail=False)  # type: ignore


@pytest.fixture
def mock_client_provider_fail():
    """Create a mock client credentials provider that fails authentication."""
    return MockClientCredentialsProvider(should_fail=True)  # type: ignore


@pytest.fixture
def mock_user_provider():
    """Create a mock user provider with token-based authentication."""
    return MockUserProvider()  # type: ignore


@pytest.fixture
def mock_client_provider_token():
    """Create a mock client provider with token-based authentication."""
    return MockClientProvider()  # type: ignore


def override_get_auth_context_factory(mock_context):
    """Factory to create auth context override function."""

    async def override():
        return mock_context

    return override


def override_provider_factory(provider):
    """Factory to create provider override function."""

    def override():
        return provider

    return override


def override_bearer_token_factory(token: str):
    """Factory to create bearer token override function."""

    def override():
        return token

    return override


class MockUserProvider(IdentityProvider):
    async def get_auth_context(self, token: str) -> AuthContext:
        if token == "user_token":
            return AuthContext(
                identity=User(
                    id="testuser",
                    name="testuser",  # Required by base Identity class
                    username="testuser",
                    email="test@example.com",
                ),
                roles=[Role(name="user")],
                token_info=TokenInfo(
                    token="user_token", token_type=TokenType.ACCESS_TOKEN
                ),
            )
        raise HTTPException(status_code=401, detail=INVALID_TOKEN_MESSAGE)


class MockClientProvider(ClientCredentialsProvider):
    async def get_client_auth_context(self, token: str) -> AuthContext:
        if token == "client_token":
            return AuthContext(
                identity=ClientIdentity(id="c1", name="svc", client_id="svc"),
                roles=[Role(name="service")],
                token_info=TokenInfo(
                    token="client_token", token_type=TokenType.ACCESS_TOKEN
                ),
            )
        raise HTTPException(status_code=401, detail=INVALID_TOKEN_MESSAGE)


class MockIdentityProvider(IdentityProvider):
    """Mock identity provider for testing."""

    def __init__(self, auth_context: AuthContext, should_fail: bool = False):
        self.auth_context = auth_context
        self.should_fail = should_fail

    async def get_auth_context(self, token: str) -> AuthContext:
        if self.should_fail:
            raise HTTPException(status_code=401, detail=INVALID_TOKEN_MESSAGE)
        return self.auth_context


class MockClientCredentialsProvider(ClientCredentialsProvider):
    """Mock client credentials provider for testing."""

    def __init__(self, auth_context: AuthContext, should_fail: bool = False):
        self.auth_context = auth_context
        self.should_fail = should_fail

    async def get_client_auth_context(self, token: str) -> AuthContext:
        if self.should_fail:
            raise HTTPException(status_code=401, detail=INVALID_TOKEN_MESSAGE)
        return self.auth_context
