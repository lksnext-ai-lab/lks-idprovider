# Keycloak and FastAPI integration

This guide is for a Python tool integrated into an existing FastAPI application
that receives end-user access tokens from Keycloak. It uses Python 3.11 or later.
The API application and Keycloak must be reachable over the network, and the
partner must have access to this repository and its GitHub Release assets.

## Install

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

Run `uv sync` in the partner project. Access to private assets may require
separate authentication. Third-party dependencies still need a configured package
index. Check the [releases](https://github.com/lksnext-ai-lab/lks-idprovider/releases)
for the available versions and assets.

For a standalone test application, add an ASGI server with `uv add uvicorn`.

## Keycloak configuration

Use a confidential client allowed to call the realm's token-introspection
endpoint. Set its secret through the application's secret manager; do not put it
in source control. For the supplied ShasAI example, the intended realm is
`shasai` and the API client and intended access-token audience are `shasai-api`.
Configure the client and audience for your actual environment before use.

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
Call `GET /profile` with `Authorization: Bearer <access-token>`; expect the
subject and roles. Repeat with an inactive token and a user without the role;
expect 401 and 403 respectively. Also check the host's issuer and audience
enforcement, including a token intended for another API. Never paste tokens or
client secrets into logs, tickets, or source files.

If the call fails, check the realm URL, TLS, client credentials and network
access to introspection and userinfo. For role failures, inspect the realm role
in the introspection response and verify the role mapper and client scope.
Keycloak can return an inactive introspection result when the introspecting
client is absent from the token audience; verify the audience mapper as well.