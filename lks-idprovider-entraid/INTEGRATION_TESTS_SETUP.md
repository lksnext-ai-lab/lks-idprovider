# Quick Start: Setting Up Integration Tests

## Step-by-Step Guide

### 1. Create your `.env` file

In the root of the `lks-idprovider-entraid` directory:

```bash
cp .env.example .env
```

### 2. Get your Azure credentials

You need an **App Registration** in Azure AD. Here's how to get the values:

#### In Azure Portal:

1. Go to **Azure Active Directory** → **App registrations**
2. Select your app (or create a new one)
3. Get the values:
   - **ENTRAID_TENANT_ID**: Directory (tenant) ID from the Overview page
   - **ENTRAID_CLIENT_ID**: Application (client) ID from the Overview page
   - **ENTRAID_CLIENT_SECRET**: Create one in **Certificates & secrets** → **Client secrets**

#### Or using Azure CLI:

```bash
# Login to Azure
az login

# Get tenant ID
az account show --query tenantId -o tsv

# Create app registration (if needed)
az ad app create --display-name "lks-idprovider-entraid-tests"

# Get client ID
az ad app list --display-name "lks-idprovider-entraid-tests" --query "[0].appId" -o tsv

# Create client secret (save this, it won't be shown again!)
az ad app credential reset --id <your-app-id> --append
```

### 3. Configure API Permissions

Your app registration needs these Microsoft Graph permissions:

1. In Azure Portal → App registration → **API permissions**
2. Add permissions:
   - `User.Read` (Delegated)
   - `User.ReadBasic.All` (Application) - optional, for service-to-service

3. Grant admin consent if required

### 4. Fill in your `.env` file

```env
ENTRAID_TENANT_ID=12345678-1234-1234-1234-123456789abc
ENTRAID_CLIENT_ID=87654321-4321-4321-4321-cba987654321
ENTRAID_CLIENT_SECRET=your-secret-value-here~1234567890
```

### 5. Run the tests

```bash
# Run all integration tests
poetry run pytest tests_entraid/integration/ -v

# Run only basic connectivity tests (no user token needed)
poetry run pytest tests_entraid/integration/ -v -k "not user_token and not ropc"

# Run with coverage
poetry run pytest tests_entraid/integration/ -v --cov=src
```

## Getting a User Token (Optional)

For tests that require a user access token (`test_get_user_info_with_user_token`, etc.):

### Easy way - Using Azure CLI:

```bash
# Get a token for Microsoft Graph
az account get-access-token --resource https://graph.microsoft.com --query accessToken -o tsv
```

Copy the token and add to `.env`:
```env
AZURE_TEST_USER_TOKEN=eyJ0eXAiOiJKV1QiLCJub25jZSI6...
```

**Note**: Tokens expire after 1 hour, so you'll need to regenerate periodically.

### Alternative - Using PowerShell:

```powershell
# Connect to Azure AD
Connect-AzAccount

# Get access token
$token = (Get-AzAccessToken -ResourceUrl "https://graph.microsoft.com").Token
echo $token
```

## Troubleshooting

### "Azure credentials not configured"
- Make sure your `.env` file exists in the project root
- Check that variable names match exactly (case-sensitive)
- Verify the `.env` file is not empty

### "Invalid client secret"
- Client secrets expire - check if yours is still valid in Azure Portal
- Make sure you copied the secret **value**, not the secret ID
- Secrets can only be viewed once when created - you may need to create a new one

### "Insufficient privileges"
- Your app needs the correct API permissions
- Admin consent may be required for your tenant
- Check in Azure Portal → App registration → API permissions

### Tests are slow
- Integration tests make real API calls to Azure AD
- First test may be slower due to token acquisition
- Subsequent tests use cached tokens when possible

## What Gets Tested

✅ With just **ENTRAID_TENANT_ID, ENTRAID_CLIENT_ID, ENTRAID_CLIENT_SECRET**:
- Connection to Azure AD
- Well-known configuration retrieval
- Health checks
- Client credentials token validation
- Provider metadata

✅ With **AZURE_TEST_USER_TOKEN** added:
- User token validation
- Getting user profile information
- Extracting user roles
- Complete auth context

⚠️ **ROPC tests** (username/password) are optional and NOT recommended for production.

## Security Reminders

- ✅ `.env` is already in `.gitignore` - your secrets won't be committed
- ✅ Never commit the `.env` file to version control
- ✅ Use different credentials for testing vs production
- ✅ Rotate secrets regularly
- ✅ Use Azure Key Vault for production secrets

## Next Steps

Once tests pass, you can use the same credentials in your actual application:

```python
from lks_idprovider_entraid import EntraIDConfig, EntraIDProvider

config = EntraIDConfig(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret",
)

async with EntraIDProvider(config) as provider:
    result = await provider.validate_token(user_token)
    if result.is_valid:
        user = await provider.get_user_info(user_token)
        print(f"Authenticated user: {user.username}")
```
