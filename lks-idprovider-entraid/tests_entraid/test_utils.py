"""
Unit tests for Entra ID utility functions.
"""

from datetime import UTC, datetime

import jwt
from lks_idprovider.types.enums import TokenType

# >=32 bytes so pyjwt does not emit InsecureKeyLengthWarning for HS256.
TEST_HMAC_KEY = "entraid-unit-test-hmac-signing-key"


def test_decode_token_without_validation():
    """Test decoding a token without validation."""
    from lks_idprovider_entraid.utils import decode_token_without_validation

    # Create a simple unsigned token
    claims = {"sub": "user123", "name": "Test User", "exp": 9999999999}
    token = jwt.encode(claims, TEST_HMAC_KEY, algorithm="HS256")

    decoded = decode_token_without_validation(token)
    assert decoded["sub"] == "user123"
    assert decoded["name"] == "Test User"


def test_map_token_to_token_info_user_token(sample_token_claims):
    """Test mapping user token claims to TokenInfo."""
    from lks_idprovider_entraid.utils import map_token_to_token_info

    token_info = map_token_to_token_info(sample_token_claims, "test-token")

    assert token_info.token == "test-token"
    assert token_info.token_type == TokenType.ACCESS_TOKEN
    assert token_info.subject == sample_token_claims["sub"]
    assert token_info.issuer == sample_token_claims["iss"]
    assert token_info.audience == sample_token_claims["aud"]
    assert "User.Read" in token_info.scopes
    assert "profile" in token_info.scopes
    assert "AdminRole" in token_info.scopes


def test_map_token_to_token_info_client_credentials(sample_client_token_claims):
    """Test mapping client credentials token claims to TokenInfo."""
    from lks_idprovider_entraid.utils import map_token_to_token_info

    token_info = map_token_to_token_info(sample_client_token_claims, "client-token")

    assert token_info.token == "client-token"
    assert token_info.token_type == TokenType.ACCESS_TOKEN
    assert token_info.subject == sample_client_token_claims["sub"]
    assert "Application.ReadWrite.All" in token_info.scopes


def test_map_token_to_token_info_with_timestamps(sample_token_claims):
    """Test TokenInfo timestamp mapping."""
    from lks_idprovider_entraid.utils import map_token_to_token_info

    token_info = map_token_to_token_info(sample_token_claims, "test-token")

    assert token_info.expires_at is not None
    assert token_info.issued_at is not None
    assert isinstance(token_info.expires_at, datetime)
    assert isinstance(token_info.issued_at, datetime)
    assert token_info.expires_at.tzinfo == UTC


def test_extract_roles_from_token(sample_token_claims):
    """Test extracting roles from token claims."""
    from lks_idprovider_entraid.utils import extract_roles_from_token

    roles = extract_roles_from_token(sample_token_claims)

    assert len(roles) == 2
    assert roles[0].name == "AdminRole"
    assert roles[1].name == "UserRole"
    assert roles[0].description is not None
    assert "Azure AD application role" in roles[0].description


def test_extract_roles_from_token_no_roles():
    """Test extracting roles when none are present."""
    from lks_idprovider_entraid.utils import extract_roles_from_token

    claims = {"sub": "user123", "name": "Test User"}
    roles = extract_roles_from_token(claims)

    assert len(roles) == 0


def test_extract_roles_from_token_single_role():
    """Test extracting a single role as string."""
    from lks_idprovider_entraid.utils import extract_roles_from_token

    claims = {"sub": "user123", "roles": "SingleRole"}
    roles = extract_roles_from_token(claims)

    assert len(roles) == 1
    assert roles[0].name == "SingleRole"


def test_map_graph_user_to_user(mock_graph_user_response):
    """Test mapping Graph API user data to User model."""
    from lks_idprovider_entraid.utils import map_graph_user_to_user

    user = map_graph_user_to_user(mock_graph_user_response)

    assert user.id == mock_graph_user_response["id"]
    assert user.username == mock_graph_user_response["userPrincipalName"]
    assert user.email == mock_graph_user_response["mail"]
    assert user.name == mock_graph_user_response["displayName"]
    assert user.first_name == mock_graph_user_response["givenName"]
    assert user.last_name == mock_graph_user_response["surname"]
    assert user.identity_type == "user"


def test_map_graph_user_to_user_with_claims(
    mock_graph_user_response, sample_token_claims
):
    """Test mapping Graph API user data with token claims."""
    from lks_idprovider_entraid.utils import map_graph_user_to_user

    user = map_graph_user_to_user(mock_graph_user_response, sample_token_claims)

    assert user.attributes["tenant_id"] == sample_token_claims["tid"]
    assert user.attributes["job_title"] == mock_graph_user_response["jobTitle"]
    assert user.attributes["department"] == mock_graph_user_response["department"]


def test_map_graph_user_to_user_fallback_email(mock_graph_user_response):
    """Test email fallback to userPrincipalName."""
    from lks_idprovider_entraid.utils import map_graph_user_to_user

    # Remove mail field
    user_data = mock_graph_user_response.copy()
    del user_data["mail"]

    user = map_graph_user_to_user(user_data)

    assert user.email == user_data["userPrincipalName"]


def test_map_graph_user_to_user_no_display_name():
    """Test display name construction from first and last name."""
    from lks_idprovider_entraid.utils import map_graph_user_to_user

    user_data = {
        "id": "user-id",
        "userPrincipalName": "test@example.com",
        "givenName": "John",
        "surname": "Doe",
    }

    user = map_graph_user_to_user(user_data)

    assert user.name == "John Doe"


def test_get_identity_type_user(sample_token_claims):
    """Test identity type detection for user token."""
    from lks_idprovider_entraid.utils import get_identity_type

    identity_type = get_identity_type(sample_token_claims)

    assert identity_type == "user"


def test_get_identity_type_service_principal(sample_client_token_claims):
    """Test identity type detection for service principal."""
    from lks_idprovider_entraid.utils import get_identity_type

    identity_type = get_identity_type(sample_client_token_claims)

    assert identity_type == "service_principal"


def test_get_identity_type_managed_identity():
    """Test identity type detection for managed identity."""
    from lks_idprovider_entraid.utils import get_identity_type

    claims = {
        "sub": "managed-identity-id",
        "xms_mirid": "/subscriptions/xxx/resourcegroups/xxx/providers/"
        "Microsoft.ManagedIdentity/userAssignedIdentities/xxx",
    }

    identity_type = get_identity_type(claims)

    assert identity_type == "managed_identity"


def test_get_identity_type_with_idtyp_claim():
    """Test identity type detection using idtyp claim."""
    from lks_idprovider_entraid.utils import get_identity_type

    # User token with idtyp
    user_claims = {"sub": "user123", "idtyp": "user"}
    assert get_identity_type(user_claims) == "user"

    # App token with idtyp
    app_claims = {"sub": "app123", "idtyp": "app"}
    assert get_identity_type(app_claims) == "service_principal"
