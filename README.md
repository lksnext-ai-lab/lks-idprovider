# LKS Identity Provider Python

Python packages for validating identity-provider tokens and integrating identity
and role information into applications. Python 3.11 or later is required.

## Packages

- [lks-idprovider-api](lks-idprovider-api/): protocols and Pydantic models.
- [lks-idprovider-keycloak](lks-idprovider-keycloak/): Keycloak token introspection and identity mapping.
- [lks-idprovider-entraid](lks-idprovider-entraid/): Microsoft Entra ID provider.
- [lks-idprovider-fastapi](lks-idprovider-fastapi/): FastAPI authentication and role dependencies.

## Installation and integration

Packages are distributed as [GitHub Release assets](https://github.com/lksnext-ai-lab/lks-idprovider/releases).
The API package must be supplied alongside its provider and framework packages;
GitHub Releases is not a package index. For a version-pinned example and a
complete incoming-user-token walkthrough, see the
[Keycloak and FastAPI partner guide](docs/partner-integration.md).

The library validates already-issued tokens and constructs authentication
contexts; user login and application-specific authorization remain the host
application's responsibility.

## Documentation

- [Keycloak and FastAPI partner guide](docs/partner-integration.md)
- [Local Keycloak development](docs/keycloak-development.md)
- [API specification](docs/API_SPECIFICATION.md)
- [Entra ID integration test setup](docs/entraid/integration-setup.md)
- [Entra ID integration tests](docs/entraid/integration-tests.md)
- [FastAPI Entra ID integration tests](docs/fastapi/entraid-integration-tests.md)
- [Historical implementation plan](docs/archive/IMPLEMENTATION_PLAN.md)

## Development

From the repository root, install [uv](https://docs.astral.sh/uv/) and run:

```bash
uv sync --all-packages --all-groups --frozen
uv run --frozen pytest lks-idprovider-api/tests_api lks-idprovider-fastapi/tests --ignore-glob='**/integration/**'
```

GitHub Actions runs unit tests and builds; live integration tests have separate
service and credential requirements. See the relevant guides above.

## License

This project is licensed under [AGPL-3.0-only](LICENSE).