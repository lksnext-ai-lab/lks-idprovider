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

Protocol methods describe the interface; availability varies by provider. For
example, the current Keycloak provider raises `NotImplementedError` for its
`health_check` method.

`validate_token` returns validation status and optional token metadata, not an
authentication context. `get_auth_context` constructs the context for an incoming
token. The protocol is not an end-user login flow.

For example, application code that already has a configured provider can use
the protocol without depending on the Keycloak implementation:

```python
from lks_idprovider.protocols import IdentityProvider


async def identify_caller(provider: IdentityProvider, access_token: str) -> dict:
	context = await provider.get_auth_context(access_token)
	return {
		"subject": context.identity_id,
		"provider": context.provider,
		"roles": context.get_role_names(),
	}
```

The caller supplies an already-issued token and manages the provider lifecycle.
Provider errors must be handled at the application boundary. Do not log the
token or serialize the complete context as an API response.

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

| Attribute or method | Purpose |
| --- | --- |
| `identity_id`, `identity_name`, `identity_type` | Identify the authenticated principal. |
| `user`, `client` | Access the concrete identity when it is of that type. |
| `roles` | Inspect `Role` objects, including their client association. |
| `has_role(name, client=None)` | Check a role name; without `client`, matches realm or client roles. |
| `get_role_names(client=None)` | List role names; without `client`, includes all roles. |
| `token_info` | Access token metadata; it also contains the original sensitive token. |

In FastAPI, `requires_role(name)` checks realm roles only, while
`requires_role(name, client=...)` checks a role for that client. This is different
from `AuthContext.has_role(name)` without a client filter.

`TokenValidationResult.is_valid` describes the result of `validate_token`;
`token_info` and `error` are optional. A provider can also raise an error, such
as when the identity service cannot be contacted. The Keycloak provider's
`get_auth_context` performs its own introspection, so a preceding
`validate_token` call is not required merely to obtain the context.

[`ProviderConfig`](../lks-idprovider-api/src/lks_idprovider/models/config/base.py)
and the provider-specific configuration models are Pydantic models. They do not
automatically load the environment variables shown in setup guides.

The Keycloak user provider currently returns an empty `AuthContext.scopes` list.
Do not treat it as a source of OAuth scopes or project-specific purpose grants;
enforce those requirements separately using an appropriate verified source.

For a complete Keycloak/FastAPI integration and its security boundaries, see the
[partner integration guide](partner-integration.md).