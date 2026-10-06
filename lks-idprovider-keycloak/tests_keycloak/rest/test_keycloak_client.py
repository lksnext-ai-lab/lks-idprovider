"""
Tests for Keycloak REST client.
"""

import asyncio

import httpx
import pytest
from pytest_httpx import HTTPXMock

from lks_idprovider_keycloak.config import KeycloakConfig
from lks_idprovider_keycloak.rest.keycloak_oidc_client import KeycloakHttpClient


@pytest.fixture
def config():
    """Return a default KeycloakConfig instance for testing."""
    return KeycloakConfig(
        base_url="http://localhost:8080",
        realm="lks-test",
        client_id="PythonServiceTest",
    )


class TestKeycloakHttpClient:
    """Test the KeycloakHttpClient."""

    def test_client_creation(self, config: KeycloakConfig):
        """Test that the client is created correctly."""
        client = KeycloakHttpClient(config)
        assert client.config == config

    @pytest.mark.asyncio
    async def test_get_well_known_config_success(
        self, config: KeycloakConfig, httpx_mock: HTTPXMock
    ):
        """Test get_well_known_config successfully retrieves config."""
        mock_config = {"issuer": "http://localhost:8080/realms/lks-test"}
        httpx_mock.add_response(
            method="GET",
            url=f"{config.base_url}/realms/{config.realm}/.well-known/openid-configuration",
            json=mock_config,
            status_code=200,
        )

        async with KeycloakHttpClient(config) as client:
            well_known_config = await client.get_well_known_config()
            assert well_known_config == mock_config

    @pytest.mark.asyncio
    async def test_get_well_known_config_not_found(
        self, config: KeycloakConfig, httpx_mock: HTTPXMock
    ):
        """Test get_well_known_config handles 404 Not Found."""
        httpx_mock.add_response(
            method="GET",
            url=f"{config.base_url}/realms/{config.realm}/.well-known/openid-configuration",
            status_code=404,
        )

        with pytest.raises(httpx.HTTPStatusError):
            async with KeycloakHttpClient(config) as client:
                await client.get_well_known_config()

    @pytest.mark.asyncio
    async def test_ensure_client_is_race_safe_under_concurrency(
        self, config: KeycloakConfig, monkeypatch: pytest.MonkeyPatch
    ):
        """Concurrent callers racing the first `_ensure_client()` must share one client.

        Regression test for the leak this guards against: without the lock, two
        coroutines can both see `self._client is None` before either assigns it,
        each building (and leaking) their own httpx.AsyncClient.
        """
        created: list[httpx.AsyncClient] = []
        real_async_client = httpx.AsyncClient

        def counting_async_client(*args, **kwargs):
            instance = real_async_client(*args, **kwargs)
            created.append(instance)
            return instance

        monkeypatch.setattr(
            "lks_idprovider_keycloak.rest.keycloak_oidc_client.httpx.AsyncClient",
            counting_async_client,
        )

        client = KeycloakHttpClient(config)
        await asyncio.gather(*(client._ensure_client() for _ in range(20)))

        assert len(created) == 1
        assert client._client is created[0]
        await client.close()
