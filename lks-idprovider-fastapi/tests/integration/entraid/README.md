# Entra ID Integration Tests for FastAPI

This directory contains integration tests for the Entra ID provider with FastAPI dependencies.

## Overview

These tests verify that the `lks-idprovider-entraid` package works correctly with FastAPI through the `lks-idprovider-fastapi` dependencies:

- ✅ Authentication via ID tokens
- ✅ Auth context retrieval
- ✅ Login required dependency
- ✅ Role-based access control
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
cd ../lks-idprovider-entraid
poetry run python get_id_token.py
```

This will display your ID token which you can use for testing.

### 3. Environment Variables

Create a `.env` file in the `lks-idprovider-fastapi` directory (copy from `.env.example`):

```bash
ENTRAID_TENANT_ID=your-tenant-id
ENTRAID_CLIENT_ID=your-client-id
AZURE_TEST_USER_TOKEN=your-id-token-here
```

## Running the Tests

### Install Dependencies

First, install the required packages:

```bash
# From lks-idprovider-fastapi directory
poetry install
```

### Run Integration Tests

```bash
# Run all Entra ID integration tests
poetry run pytest tests/integration/entraid/ -v

# Run specific test
poetry run pytest tests/integration/entraid/test_entraid_dependencies_integration.py::test_auth_context_user -v

# Skip integration tests
poetry run pytest tests/ -v -m "not integration"
```

## Test Coverage

| Test | Description | Expected Result |
|------|-------------|-----------------|
| `test_auth_context_user` | Get auth context with valid ID token | Returns User identity with roles |
| `test_auth_context_invalid_token` | Try invalid token | Returns 401 Unauthorized |
| `test_auth_context_missing_token` | Request without token | Returns 403 Forbidden |
| `test_login_required_user` | Login required with valid token | Returns User identity |
| `test_login_required_invalid` | Login required with invalid token | Returns 401 Unauthorized |
| `test_requires_role_with_token` | Role check with token | Returns 200 or 403 based on roles |
| `test_requires_role_invalid_token` | Role check with invalid token | Returns 401 Unauthorized |
| `test_requires_any_role_with_token` | Multiple role check | Returns 200 or 403 based on roles |
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

The role-based tests (`test_requires_role_*`, `test_requires_any_role_*`) will:
- Return **200** if your test user has the required role(s)
- Return **403** if your test user doesn't have the required role(s)

Both outcomes are valid - the tests verify the dependency works correctly.

To test with specific roles:
1. Configure App Roles in your Azure AD application
2. Assign roles to your test user
3. The roles will appear in the ID token claims

## Troubleshooting

### Token Expired

ID tokens typically expire after 1 hour. If tests start failing with authentication errors:

```bash
# Get a fresh token
cd ../lks-idprovider-entraid
poetry run python get_id_token.py
# Update AZURE_TEST_USER_TOKEN in .env
```

### Import Errors

If you get import errors:

```bash
# Make sure both packages are installed
poetry install
cd ../lks-idprovider-entraid
poetry install
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
    cd lks-idprovider-fastapi
    poetry install
    poetry run pytest tests/integration/entraid/ -v
```

Store the credentials as repository secrets.

## Related Documentation

- [lks-idprovider-entraid README](../../lks-idprovider-entraid/README.md)
- [Integration Tests Setup](../../lks-idprovider-entraid/tests_entraid/integration/README.md)
- [Azure AD Token Types](../../lks-idprovider-entraid/AZURE_TOKEN_TYPES.md)
