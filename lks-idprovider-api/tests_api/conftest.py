"""
Pytest configuration and fixtures for LKS Identity Provider API tests.

This module provides common fixtures and configuration for testing
the API specification components.
"""

from datetime import datetime, timezone
from typing import Any

import pytest

# Test data fixtures


@pytest.fixture
def sample_token_claims() -> dict[str, Any]:
    """Sample JWT token claims for testing."""
    return {
        "sub": "user-123",
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "iss": "https://auth.example.com",
        "aud": "my-api",
        "exp": int(datetime.now(timezone.utc).timestamp()) + 3600,  # 1 hour from now
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "nbf": int(datetime.now(timezone.utc).timestamp()),
        "scope": "read write",
        "roles": ["user", "api-consumer"],
    }


@pytest.fixture
def sample_client_claims() -> dict[str, Any]:
    """Sample client credentials token claims for testing."""
    return {
        "sub": "client-service-123",
        "client_id": "my-service-client",
        "client_name": "My Service Client",
        "iss": "https://auth.example.com",
        "aud": "api-service",
        "exp": int(datetime.now(timezone.utc).timestamp()) + 7200,  # 2 hours from now
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "nbf": int(datetime.now(timezone.utc).timestamp()),
        "scope": "read:api write:api service:admin",
        "roles": ["service", "api-client"],
    }


@pytest.fixture
def sample_jwt_token() -> str:
    """Sample JWT token string for testing (not a real JWT, just
    for structure tests)."""
    return (
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJ1c2V"
        "yLTEyMyIsInVzZXJuYW1lIjoiam9obl9kb2UifQ.signature"
    )


@pytest.fixture
def sample_bearer_token() -> str:
    """Sample bearer token for testing."""
    return (
        "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJ1c2VyLTEyMyJ9.signature"
    )


@pytest.fixture
def sample_opaque_token() -> str:
    """Sample opaque token for testing."""
    return "opaquetoken-abc123-def456-ghi789"


@pytest.fixture
def sample_roles() -> list[dict[str, Any]]:
    """Sample roles data for testing."""
    return [
        {"name": "admin", "description": "Administrator role"},
        {"name": "user", "description": "Regular user role"},
        {"name": "api-consumer", "description": "API consumer role"},
    ]


@pytest.fixture
def sample_provider_config() -> dict[str, Any]:
    """Sample provider configuration for testing."""
    return {
        "provider_name": "test-provider",
        "base_url": "https://auth.example.com",
        "timeout": 30,
        "verify_ssl": True,
        "debug": False,
    }


@pytest.fixture
def sample_jwt_config() -> dict[str, Any]:
    """Sample JWT configuration for testing."""
    return {
        "algorithm": "RS256",
        "verify_signature": True,
        "verify_expiration": True,
        "verify_audience": True,
        "verify_issuer": True,
        "leeway": 10,
        "issuer": "https://auth.example.com",
        "audience": "my-api",
    }


@pytest.fixture
def sample_cache_config() -> dict[str, Any]:
    """Sample cache configuration for testing."""
    return {
        "enabled": True,
        "cache_type": "memory",
        "default_ttl": 300,
        "max_size": 1000,
        "key_prefix": "lks_idprovider",
    }


@pytest.fixture
def sample_client_credentials_config() -> dict[str, Any]:
    """Sample client credentials configuration for testing."""
    return {
        "client_id": "PythonServiceTest",
        "client_secret": "test-secret",
        "default_scopes": ["read", "write"],
        "allowed_scopes": ["read", "write", "admin"],
        "token_endpoint": "https://auth.example.com/token",
    }


# Error testing fixtures


@pytest.fixture
def sample_error_details() -> dict[str, Any]:
    """Sample error details for testing."""
    return {
        "error": "invalid_token",
        "error_description": "The token is invalid or expired",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": "abc123-def456",
    }


# Mock implementations for protocol testing


class MockIdentityProvider:
    """Mock implementation of IdentityProvider protocol for testing."""

    def __init__(self):
        self.tokens = {}
        self.users = {}

    def validate_token(self, token: str):
        """Mock token validation."""
        if token in self.tokens:
            return self.tokens[token]
        raise ValueError("Invalid token")

    def get_user_info(self, token: str):
        """Mock user info retrieval."""
        if token in self.tokens:
            return self.users.get(self.tokens[token]["sub"])
        raise ValueError("Invalid token")

    def get_auth_context(self, token: str):
        """Mock auth context retrieval."""
        if token in self.tokens:
            return {
                "user": self.users.get(self.tokens[token]["sub"]),
                "roles": [],
            }
        raise ValueError("Invalid token")


@pytest.fixture
def mock_identity_provider():
    """Mock identity provider for testing."""
    return MockIdentityProvider()


class MockClientCredentialsProvider:
    """Mock implementation of ClientCredentialsProvider protocol for testing."""

    def __init__(self):
        self.client_tokens = {}
        self.clients = {}

    def validate_client_token(self, token: str):
        """Mock client token validation."""
        if token in self.client_tokens:
            return self.client_tokens[token]
        raise ValueError("Invalid client token")

    def get_client_info(self, token: str):
        """Mock client info retrieval."""
        if token in self.client_tokens:
            return self.clients.get(self.client_tokens[token]["client_id"])
        raise ValueError("Invalid client token")

    def get_client_auth_context(self, token: str):
        """Mock client auth context retrieval."""
        if token in self.client_tokens:
            return {
                "client": self.clients.get(self.client_tokens[token]["client_id"]),
                "roles": [],
            }
        raise ValueError("Invalid client token")


@pytest.fixture
def mock_client_credentials_provider():
    """Mock client credentials provider for testing."""
    return MockClientCredentialsProvider()
