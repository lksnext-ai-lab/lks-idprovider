"""
Script to obtain an ID token from Azure Entra ID using ROPC flow.

This script uses the Resource Owner Password Credentials (ROPC) flow to obtain
an ID token for testing purposes. The token can be used to test the Entra ID
provider integration.

IMPORTANT: ROPC flow is NOT recommended for production use. It's only for testing.

Environment Variables Required:
    ENTRAID_TENANT_ID: Your Azure tenant ID
    ENTRAID_CLIENT_ID: Your Azure application (client) ID
    AZURE_TEST_USERNAME: Test user's UPN (e.g., user@domain.com)
    AZURE_TEST_PASSWORD: Test user's password

Usage:
    python get_id_token.py
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


def get_id_token_via_ropc():
    """
    Get an ID token using Resource Owner Password Credentials flow.

    Returns:
        str: The ID token, or None if failed
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

    # Request both ID token and access token
    data = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "username": USERNAME,
        "password": PASSWORD,
        "scope": "openid profile email",  # Request ID token scopes
    }

    print(f"🔐 Authenticating as: {USERNAME}")
    print(f"🏢 Tenant ID: {TENANT_ID}")
    print(f"📱 Client ID: {CLIENT_ID}")
    print("\n⏳ Requesting tokens from Azure AD...")

    try:
        response = httpx.post(token_endpoint, data=data, timeout=30.0)
        response.raise_for_status()

        token_data = response.json()

        # Check if we got an ID token
        if "id_token" not in token_data:
            print("\n❌ Error: No ID token in response")
            print("Make sure your Azure AD app is configured to issue ID tokens")
            return None

        id_token = token_data["id_token"]
        access_token = token_data.get("access_token", "N/A")

        print("\n✅ Successfully obtained tokens!\n")
        print("=" * 80)
        print("ID TOKEN (use this for backend authentication):")
        print("=" * 80)
        print(id_token)
        print("=" * 80)

        if access_token != "N/A":
            print("\nℹ️  Access token was also obtained (for Microsoft Graph API)")
            print(f"   Length: {len(access_token)} characters")

        print("\n📋 To use this token in tests:")
        print("   1. Copy the ID token above")
        print("   2. Update your .env file:")
        print(f"      AZURE_TEST_USER_TOKEN={id_token[:50]}...")
        print("\n⏱️  Note: ID tokens typically expire after 1 hour")

        return id_token

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
                    " Check Azure AD app settings > Authentication > Advanced settings"
                )
        except Exception:
            print(f"Response: {e.response.text}")
        return None

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None


if __name__ == "__main__":
    print("🚀 Azure Entra ID - Get ID Token (ROPC Flow)\n")
    token = get_id_token_via_ropc()

    if token:
        sys.exit(0)
    else:
        print("\n❌ Failed to obtain ID token")
        sys.exit(1)
