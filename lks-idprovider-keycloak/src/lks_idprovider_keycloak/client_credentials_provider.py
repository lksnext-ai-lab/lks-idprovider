from typing import Any, Optional

import httpx
from lks_idprovider.models.errors.provider import ProviderError
from lks_idprovider.models.identity.client_identity import ClientIdentity
from lks_idprovider.models.role import Role
from lks_idprovider.models.token import TokenValidationResult
from lks_idprovider.protocols.client_credentials import ClientCredentialsProvider
from lks_idprovider.types.aliases import Token

from .config import KeycloakConfig
from .rest.keycloak_oidc_client import KeycloakHttpClient
from .utils import map_introspection_to_token_info


class KeycloakClientCredentialsProvider(ClientCredentialsProvider):
    def __init__(self, config: KeycloakConfig):
        self.config = config
        self._client = KeycloakHttpClient(config)

    async def get_client_credentials_token(
        self, scopes: Optional[list[str]] = None
    ) -> dict:
        """Obtain a client credentials token from Keycloak."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }
        if scopes:
            data["scope"] = " ".join(scopes)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.config.token_endpoint, data=data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise ProviderError(
                f"Error obtaining client credentials token: {str(e)}"
            ) from e

    async def validate_client_token(self, token: Token) -> TokenValidationResult:
        """Validate a client credentials token using the OIDC introspection endpoint."""
        try:
            token_introspection = await self._client.introspect_token(token)
            token_info = None
            if token_introspection.get("active", False):
                token_info = map_introspection_to_token_info(token_introspection, token)
            return TokenValidationResult(
                is_valid=token_introspection.get("active", False),
                token_info=token_info,
                error=(
                    None
                    if token_introspection.get("active", False)
                    else "Inactive token"
                ),
            )
        except Exception as e:
            raise ProviderError(f"Error validating client token: {str(e)}") from e

    async def get_client_info(self, token: Token) -> ClientIdentity:
        """Extract client identity from a valid client credentials token."""
        try:
            claims = await self._client.introspect_token(token)
            if not claims.get("active", False):
                raise ProviderError("Inactive client token")
            scopes = claims.get("scope", "").split() if "scope" in claims else []
            return ClientIdentity(
                id=claims.get("sub", ""),
                name=claims.get("client_name") or claims.get("client_id", ""),
                identity_type="client",
                client_id=claims.get("client_id", ""),
                client_name=claims.get("client_name"),
                scopes=scopes,
                audience=claims.get("aud"),
                attributes={
                    k: v
                    for k, v in claims.items()
                    if k not in {"sub", "client_id", "client_name", "aud", "scope"}
                },
            )
        except Exception as e:
            raise ProviderError(f"Error extracting client info: {str(e)}") from e

    async def get_client_roles(self, token: Token) -> list[Role]:
        """Extract client roles from a valid client credentials token."""
        try:
            claims = await self._client.introspect_token(token)
            roles: list[Role] = []
            resource_access = claims.get("resource_access", {})
            for client_id, client_info in resource_access.items():
                for role_name in client_info.get("roles", []):
                    roles.append(Role(name=role_name, client=client_id))
            return roles
        except Exception as e:
            raise ProviderError(f"Error extracting client roles: {str(e)}") from e

    async def get_client_auth_context(self, token: Token):
        """Get complete authentication context for a client token."""
        from lks_idprovider.models.auth import AuthContext

        try:
            validation_result = await self.validate_client_token(token)
            if not validation_result.is_valid or validation_result.token_info is None:
                raise ProviderError(f"Invalid client token: {validation_result.error}")
            token_info = validation_result.token_info
            token_expires_at = validation_result.token_info.expires_at
            refresh_expires_at = None
            client = await self.get_client_info(token)
            roles = await self.get_client_roles(token)
            return AuthContext(
                identity=client,
                roles=roles,
                token_expires_at=token_expires_at,
                refresh_expires_at=refresh_expires_at,
                provider="keycloak",
                scopes=client.scopes,
                token_info=token_info or {},
            )
        except Exception as e:
            raise ProviderError(f"Error building client auth context: {str(e)}") from e

    async def get_client_scopes(self, token: Token) -> list[str]:
        """Get active scopes for a client from a valid token.

        TODO: Implement scope extraction from client token
        """
        raise NotImplementedError("get_client_scopes not yet implemented")

    async def get_client_provider_config(self) -> dict[str, Any]:
        """Get client credentials provider configuration information.

        TODO: Implement provider configuration information
        """
        raise NotImplementedError("get_client_provider_config not yet implemented")

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the client credentials provider.

        TODO: Implement health check functionality
        """
        raise NotImplementedError("health_check not yet implemented")
