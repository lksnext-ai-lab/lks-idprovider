# Identity Provider API

The `lks-idprovider-api` package defines runtime-checkable provider protocols and
Pydantic models. The source definitions are the authoritative API reference.

## User identity provider

[`IdentityProvider`](../lks-idprovider-api/src/lks_idprovider/protocols/provider.py)
defines the following async operations for already-authenticated users:

- `validate_token(token) -> TokenValidationResult`
- `get_user_info(token) -> User`
- `get_user_roles(token) -> list[Role]`
- `get_auth_context(token) -> AuthContext`
- Provider health and metadata operations, defined in the protocol.

`validate_token` returns validation status and optional token metadata, not an
authentication context. `get_auth_context` constructs the context for an incoming
token. The protocol is not an end-user login flow.

## Client credentials provider

[`ClientCredentialsProvider`](../lks-idprovider-api/src/lks_idprovider/protocols/client_credentials.py)
defines separate operations for client token acquisition and validation, client
identity, roles, scopes and `get_client_auth_context`. Implementations can
support different flows; consult the selected provider rather than assuming that
the user provider implements these operations.

## Models

[`AuthContext`](../lks-idprovider-api/src/lks_idprovider/models/auth.py) contains
an identity, roles, provider, scopes, token metadata, and expiration timestamps.
Its identity can be a `User` or `ClientIdentity`. `Role` distinguishes realm
roles from client roles by its optional `client` field.

[`ProviderConfig`](../lks-idprovider-api/src/lks_idprovider/models/config/base.py)
and the provider-specific configuration models are Pydantic models. They do not
automatically load the environment variables shown in setup guides.

For a complete Keycloak/FastAPI integration and its security boundaries, see the
[partner integration guide](partner-integration.md).