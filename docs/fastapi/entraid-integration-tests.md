# Entra ID Integration Tests for FastAPI

These integration tests cover the Entra ID provider with FastAPI dependencies.
Run commands from the repository root unless otherwise noted.

## Overview

These tests verify that the `lks-idprovider-entraid` package works correctly with FastAPI through the `lks-idprovider-fastapi` dependencies:

- ✅ Authentication via ID tokens
- ✅ Auth context retrieval
- ✅ Login required dependency
- Role-based integration cases are currently skipped
- ✅ Multiple endpoints with same token

## Prerequisites

### 1. Azure Entra ID Configuration

You need an Azure AD application configured with:
- **Application (client) ID**
- **Tenant (directory) ID**
- **Authentication** configured for your client (e.g., SPA, Web App)

### 2. Test User Token

Obtain a valid ID token for testing. You can use the `get_id_token.py` script from the `lks-idprovider-entraid` package:

```bash
uv run --frozen python lks-idprovider-entraid/get_id_token.py
```

This will display your ID token which you can use for testing.

### 3. Environment Variables

Set these variables in the environment used to run the tests:

```bash
ENTRAID_TENANT_ID=your-tenant-id
ENTRAID_CLIENT_ID=your-client-id
AZURE_TEST_USER_TOKEN=your-id-token-here
```

## Running the Tests

### Install Dependencies

First, install the required packages:

```bash
uv sync --all-packages --all-groups --frozen
```

### Run Integration Tests

```bash
# Run all Entra ID integration tests
uv run --frozen pytest lks-idprovider-fastapi/tests/integration/entraid/ -v

# Run specific test
uv run --frozen pytest lks-idprovider-fastapi/tests/integration/entraid/test_entraid_dependencies_integration.py -v

# Skip integration tests
uv run --frozen pytest lks-idprovider-fastapi/tests/ -v --ignore-glob='**/integration/**'
```

## Test Coverage

| Test | Description | Expected Result |
|------|-------------|-----------------|
| `test_auth_context_user` | Get auth context with valid ID token | Returns User identity with roles |
| `test_auth_context_invalid_token` | Try invalid token | Returns 401 Unauthorized |
| `test_auth_context_missing_token` | Request without token | Returns 403 Forbidden |
| `test_login_required_user` | Login required with valid token | Returns User identity |
| `test_login_required_invalid` | Login required with invalid token | Returns 401 Unauthorized |
| `test_requires_role_with_token` | Role check with token | Skipped |
| `test_requires_role_invalid_token` | Role check with invalid token | Skipped |
| `test_requires_any_role_with_token` | Multiple role check | Skipped |
| `test_multiple_endpoints_same_token` | Use same token on multiple endpoints | All succeed with same identity |
| `test_token_validation_with_provider_lifecycle` | Provider lifecycle management | Token validated correctly |

## Notes

### ID Token vs Access Token

These tests use **ID tokens** (default configuration), which:
- Have `aud = client_id`
- Contain user information in claims (no Graph API calls needed)
- Are suitable for authentication scenarios
- Are validated by your backend application

If you need to test with **access tokens** instead, modify the provider configuration:

```python
config = EntraIDConfig(
    tenant_id=ENTRAID_TENANT_ID,
    client_id=ENTRAID_CLIENT_ID,
    token_type=TokenType.ACCESS_TOKEN,  # Use access tokens
)
```

### Role-Based Tests

The role-based integration cases are currently skipped and do not verify role
enforcement against Entra ID.

To test with specific roles:
1. Configure App Roles in your Azure AD application
2. Assign roles to your test user
3. The roles will appear in the ID token claims

## Troubleshooting

### Token Expired

ID tokens typically expire after 1 hour. If tests start failing with authentication errors:

```bash
# Get a fresh token
uv run --frozen python lks-idprovider-entraid/get_id_token.py
# Update AZURE_TEST_USER_TOKEN in .env
```

### Import Errors

If you get import errors:

```bash
uv sync --all-packages --all-groups --frozen
```

### Connection Errors

Ensure you have internet connectivity to reach Azure AD endpoints:
- `https://login.microsoftonline.com`
- Token validation happens in real-time against Azure AD

## CI/CD Integration

To run these tests in CI/CD:

```yaml
# Example GitHub Actions
- name: Run Entra ID Integration Tests
  env:
    ENTRAID_TENANT_ID: ${{ secrets.ENTRAID_TENANT_ID }}
    ENTRAID_CLIENT_ID: ${{ secrets.ENTRAID_CLIENT_ID }}
    AZURE_TEST_USER_TOKEN: ${{ secrets.AZURE_TEST_USER_TOKEN }}
  run: |
    uv sync --all-packages --all-groups --frozen
    uv run --frozen pytest lks-idprovider-fastapi/tests/integration/entraid/ -v
```

Store the credentials as repository secrets.

## Related Documentation

- [lks-idprovider-entraid README](../../lks-idprovider-entraid/README.md)
- [Integration tests](../entraid/integration-tests.md)
