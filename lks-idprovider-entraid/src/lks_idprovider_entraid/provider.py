"""
Azure Entra ID Provider Implementation.

This module contains the EntraIDProvider class that implements
the IdentityProvider protocol for Azure Entra ID-based authentication
and authorization.
"""

from typing import Any

import httpx
import jwt
from jwt import PyJWKClient
from lks_idprovider.models import Role
from lks_idprovider.models.auth import AuthContext
from lks_idprovider.models.errors.provider import ProviderError
from lks_idprovider.models.identity import User
from lks_idprovider.models.token import TokenValidationResult
from lks_idprovider.types.aliases import Token

from .config import EntraIDConfig
from .rest.entraid_client import EntraIDCredentialClient
from .utils import (
    decode_token_without_validation,
    extract_roles_from_token,
    map_token_to_token_info,
)


class EntraIDProvider:
    """Azure Entra ID implementation of IdentityProvider protocol.

    This provider connects to Azure Entra ID to validate tokens and extract
    user identity information for REST API security.
    """

    def __init__(self, config: EntraIDConfig):
        """Initialize the Entra ID provider.

        Args:
            config: Entra ID configuration instance
        """
        self.config = config
        self._credential_client = EntraIDCredentialClient(config)
        self._http_client: httpx.AsyncClient | None = None
        self._jwks_client: PyJWKClient | None = None
        self._well_known_config: dict[str, Any] | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._http_client = httpx.AsyncClient(timeout=30.0)
        # Initialize JWKS client for token validation
        self._jwks_client = PyJWKClient(
            self.config.jwks_endpoint,
            cache_keys=True,
            max_cached_keys=10,
        )
        await self._credential_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._http_client:
            await self._http_client.aclose()
        await self._credential_client.__aexit__(exc_type, exc_val, exc_tb)

    async def test_connection(self) -> bool:
        """Test connection to Azure Entra ID.

        This method tests if the Entra ID tenant is accessible and responds
        to well-known configuration requests.

        Returns:
            True if connection is successful, False otherwise

        Raises:
            ProviderError: If there's a configuration or connection error
        """
        try:
            self._well_known_config = await self.get_well_known_config()
            return True
        except httpx.ConnectError as err:
            raise ProviderError(
                f"Cannot connect to Azure Entra ID at {self.config.base_url}"
            ) from err
        except httpx.TimeoutException as err:
            raise ProviderError("Timeout connecting to Azure Entra ID") from err
        except httpx.HTTPStatusError as err:
            if err.response.status_code == 404:
                raise ProviderError(
                    f"Tenant '{self.config.tenant_id}' not found"
                ) from err
            raise ProviderError(
                f"Azure AD status {err.response.status_code}: {err.response.text}"
            ) from err
        except Exception as e:
            raise ProviderError(f"Error connecting to Azure Entra ID: {str(e)}") from e

    async def get_well_known_config(self) -> dict[str, Any]:
        """Get the well-known OpenID Connect configuration.

        Returns:
            Dictionary containing the well-known configuration

        Raises:
            ProviderError: If configuration cannot be retrieved
        """
        if self._well_known_config:
            return self._well_known_config

        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=30.0)

        try:
            response = await self._http_client.get(self.config.well_known_endpoint)
            response.raise_for_status()
            self._well_known_config = response.json()
            # Type guard: We just set it, so it's not None
            assert self._well_known_config is not None
            return self._well_known_config
        except httpx.HTTPStatusError as err:
            raise ProviderError(
                f"Error fetching well-known config: {err.response.text}"
            ) from err
        except Exception as e:
            raise ProviderError(
                f"Error retrieving well-known configuration: {str(e)}"
            ) from e

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "entra_id"

    def get_tenant_info(self) -> dict[str, str]:
        """Get tenant information for debugging.

        Returns:
            Dictionary with tenant information
        """
        return {
            "tenant_id": self.config.tenant_id,
            "client_id": self.config.client_id,
            "authority": self.config.authority,
            "api_version": self.config.api_version,
        }

    def _validate_audience(
        self, claims: dict[str, Any]
    ) -> TokenValidationResult | None:
        """Validate token audience based on configuration.

        Returns:
            TokenValidationResult with error if validation fails, None if valid
        """
        if not self.config.validate_audience:
            return None

        token_audience = claims.get("aud")
        from .config import TokenType

        if self.config.token_type == TokenType.ID_TOKEN:
            expected_audience = self.config.client_id
            if token_audience != expected_audience:
                return TokenValidationResult(
                    is_valid=False,
                    error=f"Invalid audience for ID token: {token_audience}. "
                    f"Expected: {expected_audience}. "
                    f"Configured to accept ID tokens only "
                    f"(token_type=TokenType.ID_TOKEN)",
                )

        elif self.config.token_type == TokenType.ACCESS_TOKEN:
            expected_audience = f"api://{self.config.client_id}"
            if token_audience != expected_audience:
                return TokenValidationResult(
                    is_valid=False,
                    error=f"Invalid audience for access token:"
                    "{token_audience}. "
                    f"Expected: {expected_audience}. "
                    f"Configured to accept access tokens only "
                    f"(token_type=TokenType.ACCESS_TOKEN). "
                    f"Make sure your Azure AD app exposes an API.",
                )

        return None

    def _get_expected_issuer(self, claims: dict[str, Any]) -> str | None:
        """Get expected issuer for token validation.

        Returns:
            Expected issuer string or None if validation is disabled
        """
        if not self.config.validate_issuer:
            return None

        token_issuer = claims.get("iss")
        tenant_id = self.config.tenant_id
        valid_issuers = [
            f"https://login.microsoftonline.com/{tenant_id}/v2.0",
            f"https://sts.windows.net/{tenant_id}/",
        ]

        if token_issuer in valid_issuers:
            return token_issuer

        return self.config.issuer

    def _initialize_jwks_client(self) -> None:
        """Initialize JWKS client if not already done."""
        if not self._jwks_client:
            self._jwks_client = PyJWKClient(
                self.config.jwks_endpoint,
                cache_keys=True,
                max_cached_keys=10,
            )

    def _handle_jwt_validation_error(self, error: Exception) -> TokenValidationResult:
        """Handle JWT validation errors and return appropriate result.

        Args:
            error: The JWT validation exception

        Returns:
            TokenValidationResult with error details
        """
        error_messages = {
            jwt.ExpiredSignatureError: "Token has expired",
            jwt.InvalidAudienceError: "Invalid audience",
            jwt.InvalidIssuerError: "Invalid issuer",
            jwt.InvalidSignatureError: "Invalid signature",
            jwt.DecodeError: "Token decode error",
            jwt.PyJWKClientError: "Token validation error",
        }

        error_type = type(error)
        message = error_messages.get(error_type, "Unknown validation error")

        return TokenValidationResult(
            is_valid=False,
            error=f"{message}: {str(error)}",
        )

    async def validate_token(self, token: Token) -> TokenValidationResult:
        """Validate a JWT token using Azure AD's JWKS.

        Args:
            token: JWT token to validate

        Returns:
            TokenValidationResult with validation status and token info
        """
        try:
            claims = decode_token_without_validation(token)

            # Validate audience
            audience_error = self._validate_audience(claims)
            if audience_error:
                return audience_error

            # Initialize JWKS client and get signing key
            self._initialize_jwks_client()
            if self._jwks_client is None:
                raise ProviderError("JWKS client not initialized")
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)

            # Get expected values for validation
            expected_audience = (
                claims.get("aud") if self.config.validate_audience else None
            )
            expected_issuer = self._get_expected_issuer(claims)

            # Validate the token signature
            jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=expected_audience,
                issuer=expected_issuer,
                leeway=self.config.leeway,
            )

            # Token is valid, create TokenInfo
            token_info = map_token_to_token_info(claims, token)

            return TokenValidationResult(
                is_valid=True,
                token_info=token_info,
                error=None,
            )

        except (
            jwt.ExpiredSignatureError,
            jwt.InvalidAudienceError,
            jwt.InvalidIssuerError,
            jwt.InvalidSignatureError,
            jwt.DecodeError,
            jwt.PyJWKClientError,
        ) as err:
            return self._handle_jwt_validation_error(err)
        except Exception as e:
            raise ProviderError(f"Error validating token: {str(e)}") from e

    async def get_user_info(self, token: Token) -> User:
        """Extract user information from token.

        For both ID tokens and Access tokens (for your API), user information
        is extracted directly from the token claims.

        Note: If you need to call Microsoft Graph API, you would need a separate
        access token with audience=https://graph.microsoft.com

        Args:
            token: Valid JWT token (ID token or access token for your API)

        Returns:
            User instance with user information

        Raises:
            ProviderError: If user info cannot be retrieved
        """
        try:
            # Decode token to get claims
            claims = decode_token_without_validation(token)

            # Extract user info from token claims
            # Both ID tokens and access tokens (for your API) contain user info
            user_id = claims.get("oid") or claims.get("sub") or ""
            username = (
                claims.get("preferred_username")
                or claims.get("upn")
                or claims.get("unique_name")
                or ""
            )
            name = claims.get("name") or ""
            # Use email claim if available, otherwise fall back to upn or unique_name
            email = (
                claims.get("email") or claims.get("upn") or claims.get("unique_name")
            )

            return User(
                id=user_id,
                username=username,
                email=email,
                name=name,
                first_name=claims.get("given_name"),
                last_name=claims.get("family_name"),
            )

        except httpx.HTTPStatusError as err:
            raise ProviderError(
                f"Graph API error: {err.response.status_code} {err.response.text}"
            ) from err
        except Exception as e:
            raise ProviderError(f"Error getting user info: {str(e)}") from e

    async def get_user_roles(self, token: Token) -> list[Role]:
        """Extract user roles from a valid token.

        Azure AD includes roles in the token claims, so we don't need
        to make an additional API call.

        Args:
            token: Valid JWT access token

        Returns:
            List of Role instances

        Raises:
            ProviderError: If roles cannot be extracted
        """
        try:
            # Decode token to get claims
            claims = decode_token_without_validation(token)

            # Extract roles from token claims
            return extract_roles_from_token(claims)

        except Exception as e:
            raise ProviderError(f"Error extracting user roles: {str(e)}") from e

    async def get_auth_context(self, token: Token) -> AuthContext:
        """Get complete authentication context from a token.

        Args:
            token: JWT access token

        Returns:
            AuthContext with user, roles, and token info

        Raises:
            ProviderError: If auth context cannot be built
        """
        try:
            # Validate token
            validation_result = await self.validate_token(token)
            if not validation_result.is_valid or not validation_result.token_info:
                raise ProviderError(f"Invalid token: {validation_result.error}")

            token_info = validation_result.token_info

            # Get user info and roles
            user = await self.get_user_info(token)
            roles = await self.get_user_roles(token)

            return AuthContext(
                identity=user,
                roles=roles,
                token_expires_at=token_info.expires_at,
                refresh_expires_at=None,  # Entra ID doesn't expose refresh token expiry
                provider=self.get_provider_name(),
                scopes=token_info.scopes,
                token_info=token_info,
            )

        except Exception as e:
            raise ProviderError(f"Error building auth context: {str(e)}") from e

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the identity provider.

        Returns:
            Dictionary containing health status information
        """
        try:
            # Try to get well-known config
            await self.get_well_known_config()

            return {
                "status": "healthy",
                "provider": self.get_provider_name(),
                "tenant_id": self.config.tenant_id,
                "endpoints_accessible": True,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.get_provider_name(),
                "tenant_id": self.config.tenant_id,
                "endpoints_accessible": False,
                "error": str(e),
            }

    async def get_provider_info(self) -> dict[str, Any]:
        """Get information about the provider implementation.

        Returns:
            Dictionary containing provider metadata
        """
        return {
            "name": self.get_provider_name(),
            "display_name": "Azure Entra ID",
            "version": "1.0.0",
            "tenant_id": self.config.tenant_id,
            "authority": self.config.authority,
            "api_version": self.config.api_version,
            "credential_type": self.config.get_credential_type(),
            "supports_user_tokens": True,
            "supports_app_tokens": True,
            "supports_managed_identity": self.config.use_managed_identity,
        }
