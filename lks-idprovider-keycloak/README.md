# LKS Identity Provider: Keycloak

The Keycloak provider validates incoming tokens using the realm's introspection
endpoint and maps user identity and role claims to the shared API models.

Install this package and the compatible API package from GitHub Release assets.
For installation, configuration, a FastAPI example, and security limitations, see
the [partner integration guide](https://github.com/lksnext-ai-lab/lks-idprovider/blob/main/docs/partner-integration.md).
FastAPI integration is provided by the separate `lks-idprovider-fastapi` package.

`KeycloakProvider.validate_token` returns a `TokenValidationResult`;
`get_auth_context` returns an `AuthContext`. The provider's async context manager
manages its HTTP client. It does not independently enforce issuer or audience
settings on its introspection path, nor evaluate application-specific policies.

For local development, see the [Keycloak development guide](https://github.com/lksnext-ai-lab/lks-idprovider/blob/main/docs/keycloak-development.md).

## License

AGPL-3.0-only.