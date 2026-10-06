"""
Tests for KeycloakProvider.
"""

import asyncio

import pytest
from lks_idprovider.models.auth import AuthContext
from lks_idprovider.models.errors.provider import ProviderError
from lks_idprovider.models.identity.user import User
from lks_idprovider.models.role import Role
from lks_idprovider.models.token import TokenValidationResult
from pytest_httpx import HTTPXMock

from lks_idprovider_keycloak.config import KeycloakConfig
from lks_idprovider_keycloak.provider import KeycloakProvider


@pytest.fixture
def config():
    """Return a default KeycloakConfig instance for testing."""
    return KeycloakConfig(
        base_url="http://localhost:8080",
        realm="lks-test",
        client_id="python-service-test",
        client_secret="test",
    )


@pytest.fixture
def provider(config: KeycloakConfig) -> KeycloakProvider:
    """Return a KeycloakProvider instance for testing."""
    return KeycloakProvider(config)


@pytest.mark.asyncio
async def test_validate_token_success(
    provider: KeycloakProvider, httpx_mock: HTTPXMock
):
    """Test that a valid token is correctly validated."""
    httpx_mock.add_response(
        method="POST",
        url=f"{provider.config.base_url}/realms/{provider.config.realm}/protocol/openid-connect/token/introspect",
        json={"active": True},
        status_code=200,
    )

    result = await provider.validate_token("valid-token")
    assert isinstance(result, TokenValidationResult)
    assert result.is_valid is True


@pytest.mark.asyncio
async def test_validate_token_inactive(
    provider: KeycloakProvider, httpx_mock: HTTPXMock
):
    """Test that an inactive token is correctly identified."""
    httpx_mock.add_response(
        method="POST",
        url=f"{provider.config.base_url}/realms/{provider.config.realm}/protocol/openid-connect/token/introspect",
        json={"active": False},
        status_code=200,
    )

    result = await provider.validate_token("inactive-token")
    assert isinstance(result, TokenValidationResult)
    assert result.is_valid is False


@pytest.mark.asyncio
async def test_validate_token_invalid_http_status(
    provider: KeycloakProvider, httpx_mock: HTTPXMock
):
    """Test that an invalid token (401) is correctly handled."""
    httpx_mock.add_response(
        method="POST",
        url=f"{provider.config.base_url}/realms/{provider.config.realm}/protocol/openid-connect/token/introspect",
        status_code=401,
    )

    result = await provider.validate_token("invalid-token")
    assert isinstance(result, TokenValidationResult)
    assert result.is_valid is False


@pytest.mark.asyncio
async def test_get_user_info_success(provider: KeycloakProvider, httpx_mock: HTTPXMock):
    """Test get_user_info returns a User object for a valid token."""
    userinfo_response = {
        "sub": "123456",
        "preferred_username": "testuser",
        "email": "testuser@lks.com",
        "email_verified": True,
        "given_name": "Test",
        "family_name": "User",
        "phone_number": "+1234567890",
    }
    httpx_mock.add_response(
        method="GET",
        url=f"{provider.config.userinfo_endpoint}",
        json=userinfo_response,
        status_code=200,
    )
    user = await provider.get_user_info("valid-token")
    assert isinstance(user, User)
    assert user.username == "testuser"
    assert user.email == "testuser@lks.com"
    assert user.email_verified is True
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.phone_number == "+1234567890"


@pytest.mark.asyncio
async def test_get_user_info_invalid_token(
    provider: KeycloakProvider, httpx_mock: HTTPXMock
):
    """Test get_user_info raises on invalid token (401)."""
    httpx_mock.add_response(
        method="GET",
        url=f"{provider.config.userinfo_endpoint}",
        status_code=401,
    )
    with pytest.raises(ProviderError):
        await provider.get_user_info("invalid-token")


@pytest.mark.asyncio
async def test_get_user_info_error(provider: KeycloakProvider, httpx_mock: HTTPXMock):
    """Test get_user_info raises on server error."""
    httpx_mock.add_response(
        method="GET",
        url=f"{provider.config.userinfo_endpoint}",
        status_code=500,
    )
    with pytest.raises(ProviderError):
        await provider.get_user_info("any-token")


def mock_async_introspect_token_factory(token_claims):
    async def mock_introspect_token(token):
        return await asyncio.to_thread(lambda: token_claims)

    return mock_introspect_token


@pytest.mark.asyncio
async def test_get_user_roles_realm_roles_only(
    provider: KeycloakProvider, httpx_mock: HTTPXMock
):
    token_claims = {
        "realm_access": {"roles": ["user", "admin"]},
        "resource_access": {},
    }
    provider._client.introspect_token = mock_async_introspect_token_factory(
        token_claims
    )
    roles = await provider.get_user_roles("valid-token")
    assert all(isinstance(r, Role) for r in roles)
    assert {r.name for r in roles} == {"user", "admin"}
    assert all(r.client is None for r in roles)


@pytest.mark.asyncio
async def test_get_user_roles_client_roles_only(
    provider: KeycloakProvider, httpx_mock: HTTPXMock
):
    token_claims = {
        "realm_access": {},
        "resource_access": {"PythonServiceTest": {"roles": ["read", "write"]}},
    }
    provider._client.introspect_token = mock_async_introspect_token_factory(
        token_claims
    )
    roles = await provider.get_user_roles("valid-token")
    assert all(isinstance(r, Role) for r in roles)
    assert {r.name for r in roles} == {"read", "write"}
    assert all(r.client == "PythonServiceTest" for r in roles)


@pytest.mark.asyncio
async def test_get_user_roles_both_realm_and_client(
    provider: KeycloakProvider, httpx_mock: HTTPXMock
):
    token_claims = {
        "realm_access": {"roles": ["user"]},
        "resource_access": {"PythonServiceTest": {"roles": ["read"]}},
    }
    provider._client.introspect_token = mock_async_introspect_token_factory(
        token_claims
    )
    roles = await provider.get_user_roles("valid-token")
    assert {r.name for r in roles} == {"user", "read"}
    assert any(r.client == "PythonServiceTest" for r in roles)
    assert any(r.client is None for r in roles)


@pytest.mark.asyncio
async def test_get_user_roles_no_roles(
    provider: KeycloakProvider, httpx_mock: HTTPXMock
):
    token_claims = {"realm_access": {}, "resource_access": {}}
    provider._client.introspect_token = mock_async_introspect_token_factory(
        token_claims
    )
    roles = await provider.get_user_roles("valid-token")
    assert roles == []


@pytest.mark.asyncio
async def test_get_auth_context_valid_token(
    provider: KeycloakProvider, httpx_mock: HTTPXMock
):
    """get_auth_context aggregates user info and roles for a valid token, and only
    introspects once — validate_token/get_user_roles each introspect independently
    when called on their own, but get_auth_context must not pay for that twice."""
    introspect_response = {
        "active": True,
        "sub": "user-123",
        "realm_access": {"roles": ["user"]},
        "resource_access": {"api-service": {"roles": ["api-consumer"]}},
    }
    userinfo_response = {
        "sub": "user-123",
        "preferred_username": "test_user",
        "email": "test@example.com",
        "given_name": "Test",
        "family_name": "User",
    }
    httpx_mock.add_response(
        method="POST",
        url=f"{provider.config.base_url}/realms/{provider.config.realm}/protocol/openid-connect/token/introspect",
        json=introspect_response,
        status_code=200,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{provider.config.userinfo_endpoint}",
        json=userinfo_response,
        status_code=200,
    )

    auth_context = await provider.get_auth_context("valid_token")

    assert isinstance(auth_context, AuthContext)
    assert isinstance(auth_context.identity, User)
    assert auth_context.identity.username == "test_user"
    assert auth_context.identity.email == "test@example.com"
    assert {r.name for r in auth_context.roles} == {"user", "api-consumer"}

    introspect_requests = [
        r for r in httpx_mock.get_requests() if r.url.path.endswith("/token/introspect")
    ]
    assert len(introspect_requests) == 1


@pytest.mark.asyncio
async def test_get_auth_context_use_userinfo_endpoint_false(
    provider: KeycloakProvider, httpx_mock: HTTPXMock
):
    """With use_userinfo_endpoint=False, the user is built from the introspection
    payload instead of a separate /userinfo call — no request should reach it."""
    provider.config.use_userinfo_endpoint = False
    introspect_response = {
        "active": True,
        "sub": "user-123",
        "preferred_username": "test_user",
        "email": "test@example.com",
        "realm_access": {"roles": ["user"]},
        "resource_access": {},
    }
    httpx_mock.add_response(
        method="POST",
        url=f"{provider.config.base_url}/realms/{provider.config.realm}/protocol/openid-connect/token/introspect",
        json=introspect_response,
        status_code=200,
    )

    auth_context = await provider.get_auth_context("valid_token")

    assert isinstance(auth_context.identity, User)
    assert auth_context.identity.username == "test_user"
    assert auth_context.identity.email == "test@example.com"
    assert {r.name for r in auth_context.roles} == {"user"}
    assert not [r for r in httpx_mock.get_requests() if "userinfo" in r.url.path]


@pytest.mark.asyncio
async def test_get_auth_context_invalid_token(
    provider: KeycloakProvider, httpx_mock: HTTPXMock
):
    """Test get_auth_context raises ProviderError for an inactive token."""
    httpx_mock.add_response(
        method="POST",
        url=f"{provider.config.base_url}/realms/{provider.config.realm}/protocol/openid-connect/token/introspect",
        json={"active": False},
        status_code=200,
    )

    with pytest.raises(ProviderError):
        await provider.get_auth_context("invalid_token")
