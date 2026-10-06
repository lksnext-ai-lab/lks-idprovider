"""
Keycloak HTTP Client.

This module contains the KeycloakHttpClient class that handles all HTTP
interactions with the Keycloak server.
"""

import asyncio
from typing import Any, Optional

import httpx

from ..config import KeycloakConfig


class KeycloakHttpClient:
    """HTTP client for Keycloak API."""

    def __init__(self, config: KeycloakConfig):
        """Initialize the Keycloak HTTP client."""
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._client_lock = asyncio.Lock()

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self):
        """Ensure the HTTP client is initialized.

        A single provider/client instance is meant to be shared and called
        concurrently for the lifetime of a process, so the None-check has to be
        race-safe: without the lock, two coroutines can both pass it before either
        assigns `self._client`, each building their own `httpx.AsyncClient` and
        leaking one of the two connection pools.
        """
        if self._client is not None:
            return
        async with self._client_lock:
            if self._client is None:
                self._client = httpx.AsyncClient(
                    base_url=self.config.base_url,
                    timeout=self.config.timeout,
                    verify=self.config.verify_ssl,
                    headers={
                        "User-Agent": "lks-idprovider-keycloak/0.1.0",
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                )

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_well_known_config(self) -> dict[str, Any]:
        """Get the well-known OpenID Connect configuration."""
        await self._ensure_client()
        if not self._client:
            raise RuntimeError("HTTP client is not initialized")
        response = await self._client.get(
            f"/realms/{self.config.realm}/.well-known/openid-configuration"
        )
        response.raise_for_status()
        return response.json()

    async def introspect_token(self, token: str) -> dict[str, Any]:
        """Validate a token using the OIDC introspection endpoint.

        Returns:
            A dictionary containing the token's introspection results.
        """
        await self._ensure_client()
        if not self._client:
            raise RuntimeError("HTTP client is not initialized")

        data = {
            "token": token,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        response = await self._client.post(
            f"/realms/{self.config.realm}/protocol/openid-connect/token/introspect",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()

    async def get_userinfo(self, token: str) -> dict[str, Any]:
        """Get user info from the userinfo endpoint using the provided access token."""
        await self._ensure_client()
        if not self._client:
            raise RuntimeError("HTTP client is not initialized")
        response = await self._client.get(
            self.config.userinfo_endpoint,
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()
