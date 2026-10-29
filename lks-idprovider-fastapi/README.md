# lks-idprovider-fastapi

Provider-agnostic FastAPI integration for lks-idprovider API protocols.

This package provides reusable FastAPI dependencies, decorators, and middleware for REST API security, based on the lks-idprovider API protocols. It is not tied to any specific provider implementation (e.g., Keycloak) and can be used with any compatible backend.

## Features
- Bearer token security scheme for OpenAPI
- AuthContext dependency for user/client authentication
- Role-based and route protection dependencies
- Easy integration with any provider implementing the API protocols

## Usage
1. Install this package and your chosen provider implementation.
2. Configure your provider (e.g., Keycloak) in your FastAPI app.
3. Inject the provider into the dependencies from this package.

For installation and a complete Keycloak example, see the
[partner integration guide](https://github.com/lksnext-ai-lab/lks-idprovider/blob/main/docs/partner-integration.md).

## License
AGPL-3.0-only
