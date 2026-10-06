"""
Keycloak Provider Implementation.

This module contains the KeycloakProvider class that implements the IdentityProvider
protocol for Keycloak-based authentication and authorization.
"""

from typing import Any, Optional

import httpx
from lks_idprovider.models import Role
from lks_idprovider.models.auth import AuthContext
from lks_idprovider.models.errors.provider import ProviderError
from lks_idprovider.models.identity import User
from lks_idprovider.models.token import TokenInfo, TokenValidationResult
from lks_idprovider.types.aliases import Token

from .config import KeycloakConfig
from .rest.keycloak_oidc_client import KeycloakHttpClient
from .utils import map_introspection_to_token_info


class KeycloakProvider:
    """Keycloak implementation of IdentityProvider protocol.

    This provider connects to Keycloak to validate tokens and extract user identity
    information for REST API security.
    """

    def __init__(self, config: KeycloakConfig):
        """Initialize the Keycloak provider.

        Args:
            config: Keycloak configuration instance
        """
        self.config = config
        self._client = KeycloakHttpClient(config)
        self._well_known_config: Optional[dict[str, Any]] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def test_connection(self) -> bool:
        """Test connection to Keycloak instance.

        This method tests if the Keycloak instance is accessible and responds
        to health checks or well-known configuration requests.

        Returns:
            True if connection is successful, False otherwise

        Raises:
            ProviderError: If there's a configuration or connection error
        """
        try:
            self._well_known_config = await self._client.get_well_known_config()
            return True
        except httpx.ConnectError as err:
            raise ProviderError(
                f"Cannot connect to Keycloak at {self.config.base_url}"
            ) from err
        except httpx.TimeoutException as err:
            raise ProviderError(
                f"Timeout connecting to Keycloak at {self.config.base_url}"
            ) from err
        except httpx.HTTPStatusError as err:
            if err.response.status_code == 404:
                raise ProviderError(
                    f"Realm '{self.config.realm}' not found in Keycloak"
                ) from err
            raise ProviderError(
                f"Keycloak status {err.response.status_code}: {err.response.text}"
            ) from err
        except Exception as e:
            raise ProviderError(f"Error connecting to Keycloak: {str(e)}") from e

    async def get_well_known_config(self) -> dict[str, Any] | None:
        """Get the well-known OpenID Connect configuration.

        Returns:
            dictionary containing the well-known configuration

        Raises:
            ProviderError: If configuration cannot be retrieved
        """
        if self._well_known_config is None:
            # Try to fetch it
            if not await self.test_connection():
                raise ProviderError("Cannot retrieve well-known configuration")

        return self._well_known_config

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "keycloak"

    def get_realm_info(self) -> dict[str, str]:
        """Get realm information for debugging.

        Returns:
            dictionary with realm information
        """
        return {
            "realm": self.config.realm,
            "base_url": self.config.base_url,
            "realm_url": self.config.realm_url,
            "client_id": self.config.client_id,
        }

    async def validate_token(self, token: Token) -> TokenValidationResult:
        """Validate a token using the OIDC introspection endpoint."""
        try:
            token_introspection = await self._client.introspect_token(token)
            return self._build_validation_result(token_introspection, token)
        except httpx.HTTPStatusError as err:
            # If the token is invalid, the introspection endpoint may return 401
            if err.response.status_code == 401:
                return TokenValidationResult(is_valid=False, error=err.response.text)
            raise ProviderError(
                f"Keycloak status {err.response.status_code}: {err.response.text}"
            ) from err
        except Exception as e:
            raise ProviderError(f"Error validating token: {str(e)}") from e

    @staticmethod
    def _build_validation_result(
        token_introspection: dict[str, Any], token: Token
    ) -> TokenValidationResult:
        """Map a raw introspection payload into a `TokenValidationResult`.

        Split out of `validate_token()` so `get_auth_context()` can reuse a single
        already-fetched introspection payload instead of introspecting twice.
        """
        token_info: TokenInfo = map_introspection_to_token_info(
            introspection_data=token_introspection, token=token
        )
        return TokenValidationResult(
            is_valid=token_introspection.get("active", False),
            token_info=token_info,
            error=None,
        )

    @staticmethod
    def _build_user(claims: dict[str, Any]) -> User:
        """Map OIDC-ish claims (userinfo or introspection response) into a `User`.

        Shared by `get_user_info()` (claims from `/userinfo`) and, when
        `use_userinfo_endpoint` is disabled, `get_auth_context()` (claims from the
        already-fetched introspection payload) — both are the same "claims dict to
        User" shape.
        """
        return User(
            id=claims.get("sub", ""),
            name=claims.get("preferred_username") or claims.get("sub", ""),
            identity_type="user",
            username=claims.get("preferred_username", ""),
            email=claims.get("email"),
            email_verified=claims.get("email_verified", False),
            first_name=claims.get("given_name"),
            last_name=claims.get("family_name"),
            phone_number=claims.get("phone_number"),
            preferred_username=claims.get("preferred_username"),
            attributes={
                k: v
                for k, v in claims.items()
                if k
                not in {
                    "sub",
                    "preferred_username",
                    "email",
                    "email_verified",
                    "given_name",
                    "family_name",
                    "phone_number",
                }
            },
        )

    async def get_user_info(self, token: Token) -> User:
        """Extract user information from a valid token using the userinfo endpoint."""
        try:
            userinfo = await self._client.get_userinfo(token)
            return self._build_user(userinfo)
        except httpx.HTTPStatusError as err:
            raise ProviderError(
                f"Keycloak userinfo error:{err.response.status_code} {str(err)}"
            ) from err
        except Exception as e:
            raise ProviderError(f"Error extracting user info: {str(e)}") from e

    async def get_auth_context(self, token: Token) -> AuthContext:
        """Get complete authentication context from a token.

        Introspects the token once and reuses that payload for both validity and
        role extraction — `validate_token()` and `get_user_roles()` each introspect
        independently when called on their own, so this can't simply delegate to
        them without paying for the same round-trip twice.
        """
        try:
            try:
                token_introspection = await self._client.introspect_token(token)
            except httpx.HTTPStatusError as err:
                if err.response.status_code == 401:
                    raise ProviderError(f"Invalid token: {err.response.text}") from err
                raise ProviderError(
                    f"Keycloak status {err.response.status_code}: {err.response.text}"
                ) from err

            validation_result = self._build_validation_result(
                token_introspection, token
            )
            if not validation_result.is_valid or validation_result.token_info is None:
                raise ProviderError(f"Invalid token: {validation_result.error}")
            token_info = validation_result.token_info
            token_expires_at = validation_result.token_info.expires_at
            refresh_expires_at = None

            if self.config.use_userinfo_endpoint:
                user = await self.get_user_info(token)
            else:
                user = self._build_user(token_introspection)
            roles = self._extract_roles(token_introspection)

            return AuthContext(
                identity=user,
                roles=roles,
                token_expires_at=token_expires_at,
                refresh_expires_at=refresh_expires_at,
                provider=self.get_provider_name(),
                scopes=[],
                token_info=token_info,
            )
        except Exception as e:
            raise ProviderError(f"Error building auth context: {str(e)}") from e

    async def get_user_roles(self, token: Token) -> list[Role]:
        """Extract user roles from a valid token (realm and client roles)."""
        try:
            claims = await self._client.introspect_token(token)
            return self._extract_roles(claims)
        except Exception as e:
            raise ProviderError(f"Error extracting user roles: {str(e)}") from e

    @staticmethod
    def _extract_roles(claims: dict[str, Any]) -> list[Role]:
        """Map an introspection payload's realm/client role claims into `Role`s."""
        roles: list[Role] = []
        # Realm roles
        realm_roles = (
            claims.get("realm_access", {}).get("roles", [])
            if claims.get("realm_access")
            else []
        )
        for role_name in realm_roles:
            roles.append(Role(name=role_name, client=None))
        # Client roles
        resource_access = claims.get("resource_access", {})
        for client_id, client_info in resource_access.items():
            for role_name in client_info.get("roles", []):
                roles.append(Role(name=role_name, client=client_id))
        return roles

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the identity provider.

        Returns:
            Dictionary containing health status information

        Example:
            ```python
            health = await provider.health_check()
            if health["status"] == "healthy":
                print("Provider is healthy")
            ```
        """
        raise NotImplementedError("Health check not yet implemented")

    async def get_provider_info(self) -> dict[str, Any]:
        """Get information about the provider implementation.

        Returns:
            Dictionary containing provider metadata

        Example:
            ```python
            info = await provider.get_provider_info()
            print(f"Provider: {info['name']} v{info['version']}")
            ```
        """
        raise NotImplementedError("Provider info not yet implemented")
