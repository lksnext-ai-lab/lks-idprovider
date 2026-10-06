"""
Tests for protocol definitions in the LKS Identity Provider API.

This module tests the protocol definitions to ensure they define the correct
interfaces and can be properly implemented. Since protocols are just type
definitions, these tests focus on:
- Protocol structure and method signatures
- Mock implementations that satisfy
def validate_token(self, token: str, **kwargs) -> TokenValidationResult:
                if token.startswith("valid_"):
                    token_info = TokenInfo(
                        token=token,
                        token_type=TokenType.ACCESS_TOKEN,
                        subject="user-123",
                        expires_at=datetime.now(timezone.utc),
                        issued_at=datetime.now(timezone.utc),
                        issuer="test-issuer",
                        audience="test-audience",
                    )
                    return TokenValidationResult(
                        is_valid=True,
                        token_info=token_info,
                        error=None,
                        auth_context=None
                    )
                else:
                    return TokenValidationResult(
                        is_valid=False,
                        error="Invalid token",
                        token_info=None,
                        auth_context=None
                    )ls
- Type checking and inheritance relationships
"""

from datetime import datetime, timezone

import pytest

from lks_idprovider.models.auth import AuthContext
from lks_idprovider.models.errors import TokenValidationError
from lks_idprovider.models.identity import ClientIdentity, User
from lks_idprovider.models.role import Role
from lks_idprovider.models.token import TokenInfo, TokenValidationResult
from lks_idprovider.protocols import (
    CacheProvider,
    ClientCredentialsProvider,
    IdentityProvider,
)
from lks_idprovider.types import TokenType


class TestIdentityProviderProtocol:
    """Test cases for IdentityProvider protocol."""

    def test_identity_provider_is_protocol(self):
        """Test that IdentityProvider is a protocol."""
        assert hasattr(IdentityProvider, "__annotations__")
        # Protocols have __protocol__ attribute in runtime_checkable protocols

    def test_mock_identity_provider_implementation(self, mock_identity_provider):
        """Test that mock implementation satisfies the protocol."""
        # This would be checked by mypy in real usage
        provider = mock_identity_provider

        # Test that mock has required methods
        assert hasattr(provider, "validate_token")
        assert hasattr(provider, "get_user_info")
        assert hasattr(provider, "get_auth_context")
        assert callable(provider.validate_token)
        assert callable(provider.get_user_info)
        assert callable(provider.get_auth_context)


class TestClientCredentialsProviderProtocol:
    """Test cases for ClientCredentialsProvider protocol."""

    def test_client_credentials_provider_is_protocol(self):
        """Test that ClientCredentialsProvider is a protocol."""
        assert hasattr(ClientCredentialsProvider, "__annotations__")

    def test_mock_client_credentials_provider_implementation(
        self, mock_client_credentials_provider
    ):
        """Test that mock implementation satisfies the protocol."""
        provider = mock_client_credentials_provider

        # Test that mock has required methods
        assert hasattr(provider, "validate_client_token")
        assert hasattr(provider, "get_client_info")
        assert hasattr(provider, "get_client_auth_context")
        assert callable(provider.validate_client_token)
        assert callable(provider.get_client_info)
        assert callable(provider.get_client_auth_context)


class TestCacheProviderProtocol:
    """Test cases for CacheProvider protocol."""

    def test_cache_provider_is_protocol(self):
        """Test that CacheProvider is a protocol."""
        assert hasattr(CacheProvider, "__annotations__")


class TestProtocolImplementations:
    """Test cases for protocol implementations using mock classes."""

    def test_identity_provider_workflow(self):
        """Test complete identity provider workflow."""

        class MockProvider:
            """Mock provider implementation for testing."""

            def validate_token(self, token: str) -> TokenValidationResult:
                if token == "valid_token":
                    token_info = TokenInfo(
                        token=token,
                        token_type=TokenType.ACCESS_TOKEN,
                        subject="user-123",
                        expires_at=datetime.now(timezone.utc),
                        issued_at=datetime.now(timezone.utc),
                        issuer="test-issuer",
                        audience="test-audience",
                    )
                    return TokenValidationResult(
                        is_valid=True,
                        token_info=token_info,
                        error=None,
                    )
                else:
                    return TokenValidationResult(
                        is_valid=False,
                        error="Invalid token",
                        token_info=None,
                    )

            def get_user_info(self, token: str) -> User:
                if token == "valid_token":
                    return User(
                        id="user-123",
                        name="test_user",
                        identity_type="user",
                        attributes={"sub": "user-123"},
                        username="test_user",
                        email="test@example.com",
                        first_name="Test",
                        last_name="User",
                        phone_number=None,
                        preferred_username="test_user",
                    )
                else:
                    raise TokenValidationError("Invalid token")

            def get_user_roles(self, token: str) -> list[Role]:
                if token == "valid_token":
                    return [
                        Role(name="user", description="User role", client=None),
                        Role(
                            name="api-consumer",
                            description="API consumer role",
                            client=None,
                        ),
                    ]
                else:
                    raise TokenValidationError("Invalid token")

            def get_auth_context(self, token: str) -> AuthContext:
                if token == "valid_token":
                    user = self.get_user_info(token)
                    roles = self.get_user_roles(token)
                    return AuthContext(
                        identity=user,
                        roles=roles,
                        token_expires_at=datetime.now(timezone.utc),
                        refresh_expires_at=datetime.now(timezone.utc),
                        provider="mock-provider",
                        scopes=["read", "write"],
                        token_info=TokenInfo(
                            token=token,
                            token_type=TokenType.ACCESS_TOKEN,
                            subject="user-123",
                            expires_at=datetime.now(timezone.utc),
                            issued_at=datetime.now(timezone.utc),
                        ),
                    )
                else:
                    raise TokenValidationError("Invalid token")

            def health_check(self) -> dict:
                return {"status": "healthy", "provider": "mock"}

            def get_provider_info(self) -> dict:
                return {"name": "mock-provider", "version": "1.0.0"}

        provider = MockProvider()

        # Test valid token workflow
        result = provider.validate_token("valid_token")
        assert result.is_valid is True
        assert result.token_info is not None
        assert result.token_info.subject == "user-123"

        user = provider.get_user_info("valid_token")
        assert user.username == "test_user"
        assert user.id == "user-123"

        roles = provider.get_user_roles("valid_token")
        assert len(roles) == 2
        assert roles[0].name == "user"

        auth_context = provider.get_auth_context("valid_token")
        assert isinstance(auth_context.identity, User)
        assert len(auth_context.roles) == 2

        # Test invalid token
        result = provider.validate_token("invalid_token")
        assert result.is_valid is False
        assert (
            result.error == "Invalid token"
        )  # Fixed: use 'error' field instead of 'error_message'

        with pytest.raises(TokenValidationError):
            provider.get_user_info("invalid_token")

    def test_client_credentials_provider_workflow(self):
        """Test complete client credentials provider workflow."""

        class MockClientProvider:
            """Mock client provider implementation for testing."""

            def validate_client_token(self, token: str) -> TokenValidationResult:
                if token == "valid_client_token":
                    token_info = TokenInfo(
                        token=token,
                        token_type=TokenType.ACCESS_TOKEN,
                        subject="client-123",
                        expires_at=datetime.now(timezone.utc),
                        issued_at=datetime.now(timezone.utc),
                        issuer="test-issuer",
                        audience="test-audience",
                        scopes=["read:api", "write:api"],
                    )
                    return TokenValidationResult(
                        is_valid=True,
                        token_info=token_info,
                        error=None,
                    )
                else:
                    return TokenValidationResult(
                        is_valid=False,
                        error="Invalid client token",
                        token_info=None,
                    )

            def get_client_info(self, token: str) -> ClientIdentity:
                if token == "valid_client_token":
                    return ClientIdentity(
                        id="client-123",
                        name="PythonServiceTest",
                        identity_type="client",
                        attributes={"client_id": "PythonServiceTest"},
                        client_id="PythonServiceTest",
                        client_name="Test Service",
                        audience="test-audience",
                    )
                else:
                    raise TokenValidationError("Invalid client token")

            def get_client_roles(self, token: str) -> list[Role]:
                if token == "valid_client_token":
                    return [
                        Role(
                            name="service",
                            description="Service role",
                            client="PythonServiceTest",
                        ),
                        Role(
                            name="api-client",
                            description="API client role",
                            client="PythonServiceTest",
                        ),
                    ]
                else:
                    raise TokenValidationError("Invalid client token")

            def get_client_scopes(self, token: str) -> list[str]:
                if token == "valid_client_token":
                    return ["read:api", "write:api"]
                else:
                    raise TokenValidationError("Invalid client token")

            def get_client_auth_context(self, token: str) -> AuthContext:
                if token == "valid_client_token":
                    client = self.get_client_info(token)
                    roles = self.get_client_roles(token)
                    scopes = self.get_client_scopes(token)
                    return AuthContext(
                        identity=client,
                        roles=roles,
                        token_expires_at=datetime.now(timezone.utc),
                        refresh_expires_at=datetime.now(timezone.utc),
                        provider="mock-client-provider",
                        scopes=scopes,
                        token_info=TokenInfo(
                            token=token,
                            token_type=TokenType.ACCESS_TOKEN,
                            subject="client-123",
                            expires_at=datetime.now(timezone.utc),
                            issued_at=datetime.now(timezone.utc),
                            issuer="test-issuer",
                            audience="test-audience",
                            scopes=scopes,
                        ),
                    )
                else:
                    raise TokenValidationError("Invalid client token")

            def health_check(self) -> dict:
                return {"status": "healthy", "provider": "mock-client"}

        provider = MockClientProvider()

        # Test valid client token workflow
        result = provider.validate_client_token("valid_client_token")
        assert result.is_valid is True
        assert result.token_info is not None
        assert result.token_info.subject == "client-123"
        assert "read:api" in result.token_info.scopes

        client = provider.get_client_info("valid_client_token")
        assert client.client_id == "PythonServiceTest"
        assert client.client_name == "Test Service"

        roles = provider.get_client_roles("valid_client_token")
        assert len(roles) == 2
        assert roles[0].name == "service"

        scopes = provider.get_client_scopes("valid_client_token")
        assert "read:api" in scopes
        assert "write:api" in scopes

        auth_context = provider.get_client_auth_context("valid_client_token")
        assert isinstance(auth_context.identity, ClientIdentity)
        assert auth_context.identity.client_id == "PythonServiceTest"
        assert len(auth_context.roles) == 2

        # Test invalid client token
        result = provider.validate_client_token("invalid_token")
        assert result.is_valid is False

        with pytest.raises(TokenValidationError):
            provider.get_client_info("invalid_token")

    def test_cache_provider_workflow(self):
        """Test cache provider workflow."""

        class MockCacheProvider:
            """Mock cache provider implementation for testing."""

            def __init__(self):
                self.cache = {}
                self.ttl = {}

            def get(self, key: str):
                return self.cache.get(key)

            def set(self, key: str, value, ttl=None) -> bool:
                self.cache[key] = value
                if ttl:
                    self.ttl[key] = ttl
                return True

            def delete(self, key: str) -> bool:
                if key in self.cache:
                    del self.cache[key]
                    if key in self.ttl:
                        del self.ttl[key]
                    return True
                return False

            def exists(self, key: str) -> bool:
                return key in self.cache

            def get_many(self, keys: list[str]) -> dict:
                return {key: self.cache.get(key) for key in keys if key in self.cache}

            def set_many(self, mapping: dict, ttl=None) -> bool:
                self.cache.update(mapping)
                if ttl:
                    for key in mapping:
                        self.ttl[key] = ttl
                return True

            def clear(self, pattern=None) -> int:
                if pattern is None:
                    count = len(self.cache)
                    self.cache.clear()
                    self.ttl.clear()
                    return count
                else:
                    # Simple pattern matching for test
                    keys_to_delete = [
                        k for k in self.cache.keys() if pattern.replace("*", "") in k
                    ]
                    for key in keys_to_delete:
                        del self.cache[key]
                        if key in self.ttl:
                            del self.ttl[key]
                    return len(keys_to_delete)

            def health_check(self) -> dict:
                return {"status": "healthy", "cache_size": len(self.cache)}

        cache = MockCacheProvider()

        # Test basic operations
        cache.set("test_key", "test_value")
        value = cache.get("test_key")
        assert value == "test_value"

        exists = cache.exists("test_key")
        assert exists is True

        # Test batch operations
        cache.set_many({"key1": "value1", "key2": "value2"})
        values = cache.get_many(["key1", "key2", "key3"])
        assert values["key1"] == "value1"
        assert values["key2"] == "value2"
        assert "key3" not in values

        # Test deletion
        deleted = cache.delete("key1")
        assert deleted is True

        exists = cache.exists("key1")
        assert exists is False

        # Test clear
        cleared = cache.clear()
        assert cleared >= 1  # At least test_key and key2

        # Test health check
        health = cache.health_check()
        assert health["status"] == "healthy"
