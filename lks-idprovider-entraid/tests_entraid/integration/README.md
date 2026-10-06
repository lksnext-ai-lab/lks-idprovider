# Integration Tests for lks-idprovider-entraid

This directory contains integration tests that make real API calls to Azure Entra ID and Microsoft Graph API.

## Prerequisites

1. **Azure Entra ID Tenant**: You need access to an Azure AD tenant
2. **App Registration**: Create an app registration in Azure AD with:
   - Client secret configured
   - API permissions: `User.Read`, `User.ReadBasic.All` (for Graph API calls)
   - Optional: Enable "Resource Owner Password Credentials" flow for user token tests

## Configuration

### Option 1: Using .env file (Recommended)

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Azure credentials:
   ```env
   # Required (for basic tests)
   ENTRAID_TENANT_ID=your-tenant-id
   ENTRAID_CLIENT_ID=your-client-id
   ENTRAID_CLIENT_SECRET=your-client-secret

   # Optional (for user token tests)
   AZURE_TEST_USER_TOKEN=your-valid-user-token

   # Optional (for ROPC flow - NOT recommended)
   # AZURE_TEST_USERNAME=user@yourtenant.com
   # AZURE_TEST_PASSWORD=user-password
   ```

3. The `.env` file is automatically loaded by pytest-dotenv (configured in `pyproject.toml`)

### Option 2: Environment Variables

Set environment variables directly in your shell:

#### PowerShell:
```powershell
$env:ENTRAID_TENANT_ID = "your-tenant-id"
$env:ENTRAID_CLIENT_ID = "your-client-id"
$env:ENTRAID_CLIENT_SECRET = "your-client-secret"
```

#### Bash/Zsh:
```bash
export ENTRAID_TENANT_ID="your-tenant-id"
export ENTRAID_CLIENT_ID="your-client-id"
export ENTRAID_CLIENT_SECRET="your-client-secret"
```

## Running Tests

### Run all integration tests:
```bash
poetry run pytest tests_entraid/integration/ -v
```

### Run specific integration test file:
```bash
poetry run pytest tests_entraid/integration/test_provider_integration.py -v
```

### Run only tests that don't require user tokens:
```bash
poetry run pytest tests_entraid/integration/ -v -k "not user_token and not ropc"
```

### Skip integration tests (run only unit tests):
```bash
poetry run pytest tests_entraid/ -v --ignore=tests_entraid/integration
```

## Test Coverage

### Basic Connectivity Tests
- ✅ `test_connection_to_azure_ad` - Verify connectivity to Azure AD
- ✅ `test_get_well_known_config` - Retrieve OpenID Connect discovery document
- ✅ `test_health_check` - Provider health check
- ✅ `test_get_provider_info` - Provider metadata

### Token Validation Tests
- ✅ `test_validate_client_credentials_token` - Validate app-only token
- ✅ `test_validate_expired_token` - Handle expired tokens
- ✅ `test_invalid_token_validation` - Handle malformed tokens
- ✅ `test_validate_user_token` - Validate user token (requires AZURE_TEST_USER_TOKEN)

### User Information Tests
- ✅ `test_get_user_info_with_user_token` - Get user profile (requires token)
- ✅ `test_get_user_roles_from_token` - Extract roles from token
- ✅ `test_get_auth_context_with_user_token` - Full auth context (requires token)

### Complete Flow Tests
- ✅ `test_ropc_flow_full_scenario` - End-to-end with ROPC (requires username/password)

## Important Notes

### About ROPC (Resource Owner Password Credentials) Flow

⚠️ **WARNING**: ROPC is **NOT recommended** for production use. It's only included in tests for convenience.

**Why ROPC is problematic:**
- Bypasses modern authentication protocols
- Cannot work with MFA/conditional access
- Violates OAuth2 best practices
- Microsoft recommends against it

**For production applications**, use:
- Authorization Code flow (web apps)
- Authorization Code + PKCE flow (SPAs, mobile apps)
- Client Credentials flow (service-to-service)
- Device Code flow (CLI/IoT devices)

### Getting a User Token for Tests

**Recommended approach** for integration tests:

1. **Manual token acquisition**:
   - Use Azure Portal or Azure CLI to get a token
   - Set `AZURE_TEST_USER_TOKEN` environment variable

   ```bash
   # Using Azure CLI
   az account get-access-token --resource https://graph.microsoft.com --query accessToken -o tsv
   ```

2. **Automated CI/CD**:
   - Use a service principal with delegated permissions
   - Store credentials securely in CI/CD secrets
   - Generate tokens programmatically

## CI/CD Integration

### GitHub Actions Example:
```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      - name: Run integration tests
        env:
          ENTRAID_TENANT_ID: ${{ secrets.ENTRAID_TENANT_ID }}
          ENTRAID_CLIENT_ID: ${{ secrets.ENTRAID_CLIENT_ID }}
          ENTRAID_CLIENT_SECRET: ${{ secrets.ENTRAID_CLIENT_SECRET }}
        run: |
          poetry run pytest tests_entraid/integration/ -v
```

### Jenkins Example:
```groovy
stage('Integration Tests') {
    environment {
        ENTRAID_TENANT_ID = credentials('azure-tenant-id')
        ENTRAID_CLIENT_ID = credentials('azure-client-id')
        ENTRAID_CLIENT_SECRET = credentials('azure-client-secret')
    }
    steps {
        sh 'poetry run pytest tests_entraid/integration/ -v'
    }
}
```

## Troubleshooting

### Tests are skipped
- Check that all required environment variables are set
- Verify credentials are valid and not expired

### "ROPC may not be enabled"
- ROPC must be explicitly enabled in Azure AD app registration
- User account cannot have MFA enabled
- Use manual token acquisition instead

### "Invalid audience" or "Invalid issuer"
- Check that `ENTRAID_CLIENT_ID` matches your app registration
- Verify token is not expired
- Ensure token has correct scopes

### Connection timeout
- Check network connectivity to Azure AD endpoints
- Verify firewall/proxy settings
- Check if Azure AD is experiencing issues

## Security Considerations

1. **Never commit credentials** to version control
2. **Use secrets management** in CI/CD (GitHub Secrets, Azure Key Vault, etc.)
3. **Rotate credentials regularly**
4. **Use least-privilege permissions** for test app registrations
5. **Monitor test app usage** in Azure AD audit logs

## Related Documentation

- [Azure AD Authentication Flows](https://docs.microsoft.com/en-us/azure/active-directory/develop/authentication-flows-app-scenarios)
- [Microsoft Graph API](https://docs.microsoft.com/en-us/graph/overview)
- [App Registration in Azure AD](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
