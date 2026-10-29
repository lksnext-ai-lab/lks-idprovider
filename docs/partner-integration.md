# Keycloak and FastAPI integration

This guide is for a Python tool integrated into an existing FastAPI application
that receives end-user access tokens from Keycloak. It uses Python 3.11 or later.
The API application and Keycloak must be reachable over the network, and the
partner must have access to this repository and its GitHub Release assets.

## Integration overview

1. A client authenticates a user with Keycloak and obtains an access token.
2. The client sends the token to the FastAPI application as a bearer token.
3. The application uses `lks-idprovider-keycloak` to introspect the token and
    retrieve the user and roles. The `lks-idprovider-fastapi` dependencies expose
    that information to the endpoint.
4. The application enforces its own resource-level and domain-specific rules.

The host application owns its FastAPI instance, provider configuration, secret
management and authorization decisions. This library does not install a server
or automatically secure routes.

## Prerequisites

| Requirement | Purpose |
| --- | --- |
| Python 3.11 or later | Run the application and packages. |
| Access to GitHub Releases | Download the API, Keycloak and FastAPI distributions. |
| Keycloak realm and confidential client | Authenticate introspection requests from the API. |
| End-user access token | Call protected endpoints and verify the integration. |
| Network access to Keycloak | Reach the introspection and userinfo endpoints from the API. |

## Install the packages

Install the API, Keycloak, and FastAPI packages from compatible GitHub Release
assets. GitHub Releases is not a package index: explicitly provide the API
package as well as both integrations. For a `uv` project, the following pins
target the release versions in this repository. Confirm that the corresponding
release assets have been published and that you can access them before use.

```toml
[project]
dependencies = ["lks-idprovider-api", "lks-idprovider-keycloak", "lks-idprovider-fastapi"]

[tool.uv.sources]
lks-idprovider-api = { url = "https://github.com/lksnext-ai-lab/lks-idprovider/releases/download/api-v0.1.8/lks_idprovider_api-0.1.8-py3-none-any.whl" }
lks-idprovider-keycloak = { url = "https://github.com/lksnext-ai-lab/lks-idprovider/releases/download/keycloak-v0.1.6/lks_idprovider_keycloak-0.1.6-py3-none-any.whl" }
lks-idprovider-fastapi = { url = "https://github.com/lksnext-ai-lab/lks-idprovider/releases/download/fastapi-v0.1.2/lks_idprovider_fastapi-0.1.2-py3-none-any.whl" }
```

Merge these entries into the partner project's existing `pyproject.toml`, then
run `uv sync`. Access to private assets may require
separate authentication. Third-party dependencies still need a configured package
index. Check the [releases](https://github.com/lksnext-ai-lab/lks-idprovider/releases)
for the available versions and assets.

Alternatively, install the same wheels into an activated Python virtual
environment using `pip`:

```bash
python -m pip install \
    https://github.com/lksnext-ai-lab/lks-idprovider/releases/download/api-v0.1.8/lks_idprovider_api-0.1.8-py3-none-any.whl \
    https://github.com/lksnext-ai-lab/lks-idprovider/releases/download/keycloak-v0.1.6/lks_idprovider_keycloak-0.1.6-py3-none-any.whl \
    https://github.com/lksnext-ai-lab/lks-idprovider/releases/download/fastapi-v0.1.2/lks_idprovider_fastapi-0.1.2-py3-none-any.whl
```

The direct API wheel is necessary because the provider and FastAPI packages
declare it as a dependency and the release assets are not an index. Install an
ASGI server separately for a standalone application, for example
`uv add uvicorn` or `python -m pip install uvicorn`.

## Keycloak configuration

Use a confidential client allowed to call the realm's token-introspection
endpoint. Set its secret through the application's secret manager; do not put it
in source control. For the supplied ShasAI example, the intended realm is
`shasai` and the API client and intended access-token audience are `shasai-api`.
Configure the client and audience for your actual environment before use.

| Application setting | Example | Meaning |
| --- | --- | --- |
| `KEYCLOAK_BASE_URL` | `https://identity.example.org` | Keycloak base URL, without `/realms/shasai`. |
| `KEYCLOAK_REALM` | `shasai` | Realm that issues the incoming token. |
| `KEYCLOAK_CLIENT_ID` | `shasai-api` | Confidential client used for introspection. |
| `KEYCLOAK_CLIENT_SECRET` | Supplied by a secret manager | Secret for the introspection client. |

For example, the expected issuer for these first two values is
`https://identity.example.org/realms/shasai`. Obtain the actual URL and
credentials from the Keycloak administrator; the sample hostname is not a live
service. `KeycloakConfig` is a Pydantic model and does not read environment
variables automatically: the application below reads them explicitly.

The example realm has inconsistent role names: the definitions use
`key_custodian` and `retention_automation`, while policy references and the
Airflow service account use hyphenated names. Resolve these references in the
project's realm before relying on its import or authorization policies. The
example's passwords, placeholder secrets, disabled SSL requirement and direct
access grants are for local testing, not production.

## FastAPI application

The client application obtains an end-user access token separately, preferably
using authorization code with PKCE. This library does not implement that login
flow. Configure `KEYCLOAK_BASE_URL`, `KEYCLOAK_REALM`, `KEYCLOAK_CLIENT_ID`, and
`KEYCLOAK_CLIENT_SECRET` in the API process. Use HTTPS and a real secret outside
local development.

This example demonstrates integration and role checks, not a complete
production authorization configuration. See [Security boundaries](#security-boundaries)
before deploying it.

```python
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request

from lks_idprovider.models.auth import AuthContext
from lks_idprovider_fastapi.dependencies import get_default_provider, requires_role
from lks_idprovider_keycloak import KeycloakConfig, KeycloakProvider


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = KeycloakConfig(
        base_url=os.environ["KEYCLOAK_BASE_URL"],
        realm=os.environ["KEYCLOAK_REALM"],
        client_id=os.environ["KEYCLOAK_CLIENT_ID"],
        client_secret=os.environ["KEYCLOAK_CLIENT_SECRET"],
    )
    async with KeycloakProvider(config) as provider:
        app.state.identity_provider = provider
        yield


app = FastAPI(lifespan=lifespan)


def get_provider(request: Request) -> KeycloakProvider:
    return request.app.state.identity_provider


app.dependency_overrides[get_default_provider] = get_provider


@app.get("/profile")
async def profile(context: AuthContext = Depends(requires_role("data_holder"))):
    return {"subject": context.identity_id, "roles": context.get_role_names()}
```

In an existing application, merge the provider lifecycle into its existing
lifespan and add the override to that application. `requires_role` checks a
realm role by default; pass `client="client-id"` for a client role. The returned
context contains the identity, roles and token information. With the default
configuration, identity claims come from userinfo and roles from introspection.

For a standalone test, put the example in `main.py` and run
`uv run uvicorn main:app`. The existing host application can instead use its
own ASGI server and startup configuration.

For example, set the non-secret values in the API process environment:

```bash
export KEYCLOAK_BASE_URL="https://identity.example.org"
export KEYCLOAK_REALM="shasai"
export KEYCLOAK_CLIENT_ID="shasai-api"
```

Provide `KEYCLOAK_CLIENT_SECRET` through the deployment's secret store before
starting the server. Missing environment variables fail application startup;
incorrect credentials or network connectivity will surface when Keycloak is
contacted. TLS verification is enabled by default.

## Authorization examples

Add these routes to the application above. The first requires authentication
without imposing a role. The second accepts either of two realm roles. The third
requires a role assigned specifically for the `shasai-grants-api` client.

```python
from fastapi import Depends

from lks_idprovider.models.auth import AuthContext
from lks_idprovider_fastapi.dependencies import (
    login_required,
    requires_any_role,
    requires_role,
)


@app.get("/me")
async def current_user(context: AuthContext = Depends(login_required)):
    return {"subject": context.identity_id, "provider": context.provider}


@app.get("/metadata")
async def metadata(
    context: AuthContext = Depends(
        requires_any_role("data_holder", "data_governance_body")
    ),
):
    return {"requested_by": context.identity_id}


@app.get("/grant-evaluations")
async def grant_evaluations(
    context: AuthContext = Depends(
        requires_role("grant-evaluator", client="shasai-grants-api")
    ),
):
    return {"requested_by": context.identity_id}
```

The client-role example is illustrative: the role must actually be assigned to
the caller and included in the introspection response. The supplied realm assigns
it to a service account, not to the example human users. For an end-user token,
the client must also request an appropriate scope and mapper that includes the
assigned client role. A matching role name under another client does not grant
access to this route.

`requires_role("data_holder")` checks realm roles only. In contrast,
`context.has_role("data_holder")` without a `client` argument matches that name
in either a realm or client role. For an explicit realm-only check outside a
dependency, use `any(role.name == "data_holder" and role.client is None for role
in context.roles)`.

## Use the provider outside FastAPI

A Python tool that already has an incoming user token can use the provider
directly. Reuse a provider for the lifetime of the process or application, and
close it using its async context manager. This example obtains no token itself.

```python
from lks_idprovider.models.auth import AuthContext
from lks_idprovider_keycloak import KeycloakConfig, KeycloakProvider


async def resolve_user(config: KeycloakConfig, access_token: str) -> AuthContext:
    async with KeycloakProvider(config) as provider:
        return await provider.get_auth_context(access_token)
```

`get_auth_context` validates the token and raises a provider error if it cannot
construct the context. To inspect validity without constructing user information,
call `await provider.validate_token(access_token)` and check `result.is_valid`.
That method returns `TokenValidationResult`, not `AuthContext`. Avoid calling
both methods for every request: each performs an introspection request.

The current Keycloak user provider sets `context.scopes` to an empty list; do not
use `context.has_scope()` as a ShasAI purpose or grant authorization check. The
context's token information contains the original bearer token, so do not log
or return the complete context to clients.

## Security boundaries

The Keycloak provider validates token activity using Keycloak's introspection
endpoint. Although `KeycloakConfig` exposes issuer and audience settings, the
current introspection path does not independently compare the returned issuer
or audience against the intended API. Enforce the expected issuer, audience and
token type in an appropriate security layer before relying on this example in
production. Do not assume a token accepted by introspection is intended for this
API. The provider also does not evaluate Keycloak Authorization Services
resource policies or the ShasAI purpose and time-limited grant claims; the host
application must enforce those separately.

Missing bearer credentials are rejected by FastAPI's bearer scheme. Invalid
tokens and provider failures are returned as 401; missing required roles are 403.
Avoid exposing sensitive provider error details to callers in production.

## Smoke test

Start the application with the environment above and obtain an access token for
an end user with the `data_holder` realm role through your approved login flow.
Set `ACCESS_TOKEN` in the shell without writing it to a script or command
history, then call the local API:

```bash
curl --silent --show-error \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    http://127.0.0.1:8000/profile
```

An authorized caller receives a response with this shape; the subject and roles
depend on the token:

```json
{
    "subject": "user-subject-id",
    "roles": ["data_holder", "data_engineer"]
}
```

Repeat with an inactive token and a user without the role; expect 401 and 403
respectively. Also check the host's issuer and audience enforcement, including a
token intended for another API. Never paste tokens or client secrets into logs,
tickets, or source files.

The repository's [local test realm](keycloak-development.md) uses the roles
`user` and `admin`, not the ShasAI roles in this example. To test `/profile`
against that realm, change the example's required role to `user` and use the
local test client configuration. This checks integration behavior; it does not
validate the supplied ShasAI realm or its authorization policies.

## Test a protected endpoint

For application unit tests, override the authentication-context dependency so
the test does not require Keycloak. This example tests the role decision for
the `/profile` endpoint in `main.py`:

```python
import pytest
from fastapi.testclient import TestClient

from lks_idprovider.models.auth import AuthContext
from lks_idprovider.models.identity import User
from lks_idprovider.models.role import Role
from lks_idprovider.models.token import TokenInfo
from lks_idprovider.types.enums import TokenType
from lks_idprovider_fastapi.dependencies import get_auth_context

from main import app


@pytest.mark.parametrize(
    ("roles", "expected_status"),
    [([Role(name="data_holder")], 200), ([], 403)],
)
def test_profile_requires_data_holder(monkeypatch, roles, expected_status):
    context = AuthContext(
        identity=User(id="user-123", name="Test User", username="test-user"),
        roles=roles,
        provider="keycloak",
        token_info=TokenInfo(token="test-token", token_type=TokenType.ACCESS_TOKEN),
    )

    async def override_context():
        return context

    monkeypatch.setitem(app.dependency_overrides, get_auth_context, override_context)
    response = TestClient(app).get("/profile")

    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["subject"] == "user-123"
```

Install the project's test dependencies, including `pytest` and `httpx`, and run
`pytest` from the directory containing the application and test. This override
bypasses token validation and Keycloak; use integration tests with real tokens
to test those parts of the flow. It applies to dependencies such as
`requires_role` that inject `get_auth_context`. `login_required` calls that
function directly, so tests of `/me` should override the provider instead.

## Troubleshooting

| Symptom | Checks |
| --- | --- |
| Application fails at startup | Verify all four environment variables are present and the base URL includes `http://` or `https://`. |
| Token rejected as inactive | Check token expiry, realm, introspection credentials and whether the client is in the token audience. |
| Authenticated user receives 403 | Check the exact role name, whether it is a realm or client role, and the roles in the introspection response. |
| Authentication fails despite an active token | Check connectivity to userinfo and whether the access token has the required OpenID scope. |
| Provider is not configured | Register the `get_default_provider` override on the same FastAPI application that serves the route. |

If the call fails, check the realm URL, TLS, client credentials and network
access to introspection and userinfo. For role failures, inspect the realm role
in the introspection response and verify the role mapper and client scope.
Keycloak can return an inactive introspection result when the introspecting
client is absent from the token audience; verify the audience mapper as well.