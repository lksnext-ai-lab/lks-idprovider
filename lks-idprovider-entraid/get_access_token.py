"""
Script to obtain an access token from Azure Entra ID using ROPC flow.

This script uses the Resource Owner Password Credentials (ROPC) flow to obtain
an access token for your API. The token can be used to test the Entra ID
provider integration with ACCESS_TOKEN mode.

IMPORTANT: ROPC flow is NOT recommended for production use. It's only for testing.

Environment Variables Required:
    ENTRAID_TENANT_ID: Your Azure tenant ID
    ENTRAID_CLIENT_ID: Your Azure application (client) ID
    AZURE_TEST_USERNAME: Test user's UPN (e.g., user@domain.com)
    AZURE_TEST_PASSWORD: Test user's password

Usage:
    python get_access_token.py
"""

import os
import sys

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TENANT_ID = os.getenv("ENTRAID_TENANT_ID")
CLIENT_ID = os.getenv("ENTRAID_CLIENT_ID")
USERNAME = os.getenv("AZURE_TEST_USERNAME")
PASSWORD = os.getenv("AZURE_TEST_PASSWORD")


def get_access_token_via_ropc():
    """
    Get an access token for your API using Resource Owner Password Credentials flow.

    Returns:
        str: The access token, or None if failed
    """
    if not all([TENANT_ID, CLIENT_ID, USERNAME, PASSWORD]):
        print("❌ Error: Missing required environment variables")
        print("\nRequired variables:")
        print("  ENTRAID_TENANT_ID")
        print("  ENTRAID_CLIENT_ID")
        print("  AZURE_TEST_USERNAME")
        print("  AZURE_TEST_PASSWORD")
        print("\nMake sure these are set in your .env file")
        return None

    token_endpoint = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    # Request access token for YOUR API
    # The scope should be: api://{CLIENT_ID}/access_as_user
    api_scope = f"api://{CLIENT_ID}/access_as_user"

    data = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "username": USERNAME,
        "password": PASSWORD,
        "scope": api_scope,  # Request access to your API
    }

    print(f"🔐 Authenticating as: {USERNAME}")
    print(f"🏢 Tenant ID: {TENANT_ID}")
    print(f"📱 Client ID: {CLIENT_ID}")
    print(f"🎯 API Scope: {api_scope}")
    print("\n⏳ Requesting access token from Azure AD...")

    try:
        response = httpx.post(token_endpoint, data=data, timeout=30.0)
        response.raise_for_status()

        token_data = response.json()

        # Check if we got an access token
        if "access_token" not in token_data:
            print("\n❌ Error: No access token in response")
            print("Make sure your Azure AD app has 'Expose an API' configured")
            return None

        access_token = token_data["access_token"]
        id_token = token_data.get("id_token", "N/A")

        print("\n✅ Successfully obtained access token!\n")
        print("=" * 80)
        print("ACCESS TOKEN (use this for API authorization):")
        print("=" * 80)
        print(access_token)
        print("=" * 80)

        # Decode the token to show audience
        import jwt

        try:
            decoded = jwt.decode(access_token, options={"verify_signature": False})
            print("\n📋 Token Details:")
            print(f"   Audience (aud): {decoded.get('aud')}")
            print(f"   Issuer (iss): {decoded.get('iss')}")
            print(f"   Subject (sub): {decoded.get('sub')}")
            print(f"   Scopes (scp): {decoded.get('scp', 'N/A')}")
            print(f"   Roles (roles): {decoded.get('roles', [])}")

            expected_aud = f"api://{CLIENT_ID}"
            if decoded.get("aud") == expected_aud:
                print(f"\n✅ Audience is correct: {expected_aud}")
            else:
                print(f"\n⚠️  Warning: Audience is '{decoded.get('aud')}'")
                print(f"   Expected: '{expected_aud}'")

        except Exception as e:
            print(f"\n⚠️  Could not decode token: {e}")

        if id_token != "N/A":
            print("\n\nℹ️  ID token was also obtained")
            print(f"   Length: {len(id_token)} characters")

        print("\n📋 To use this token in tests:")
        print("   1. Copy the access token above")
        print("   2. Update your .env file:")
        print(f"      AZURE_TEST_ACCESS_TOKEN={access_token[:50]}...")
        print("\n⏱️  Note: Access tokens typically expire after 1 hour")
        print("\n💡 To use ACCESS_TOKEN mode in your provider:")
        print("   config = EntraIDConfig(")
        print("       tenant_id=TENANT_ID,")
        print("       client_id=CLIENT_ID,")
        print("       token_type=TokenType.ACCESS_TOKEN,  # Use access tokens")
        print("   )")

        return access_token

    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        try:
            error_data = e.response.json()
            print(f"Error: {error_data.get('error', 'Unknown error')}")
            print(
                f"Description: {error_data.get('error_description', 'No description')}"
            )

            if "AADSTS50126" in str(error_data):
                print("\n💡 Tip: Invalid username or password")
            elif "AADSTS50076" in str(error_data):
                print("\n💡 Tip: MFA is required. ROPC doesn't support MFA.")
                print("   Consider using a test user without MFA enabled.")
            elif "AADSTS700016" in str(error_data):
                print("\n💡 Tip: ROPC flow may not be enabled for this app.")
                print(
                    "   Check Azure AD app settings > Authentication"
                    " > Advanced settings"
                )
            elif "AADSTS65001" in str(error_data):
                print("\n💡 Tip: User hasn't consented to access the API.")
                print("   The user needs to consent to the scope first.")
            elif "AADSTS500011" in str(error_data):
                print("\n💡 Tip: Resource/API not found or scope is invalid.")
                print(f"   Make sure '{api_scope}' is configured in Azure AD")
                print("   Steps:")
                print("   1. Go to Azure Portal > App registrations > Your app")
                print("   2. Click 'Expose an API'")
                print(
                    f"   3. Verify scope 'access_as_user' exists under api://{CLIENT_ID}"
                )
                print("   4. Make sure it's enabled and admins can consent")
        except Exception:
            print(f"Response: {e.response.text}")
        return None

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None


if __name__ == "__main__":
    print("🚀 Azure Entra ID - Get Access Token for YOUR API (ROPC Flow)\n")
    token = get_access_token_via_ropc()

    if token:
        sys.exit(0)
    else:
        print("\n❌ Failed to obtain access token")
        sys.exit(1)
