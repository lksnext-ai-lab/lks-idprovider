"""
Unit tests for EntraIDConfig.
"""

import pytest
from pydantic import ValidationError


def test_entraid_config_basic(entraid_config):
    """Test basic EntraID configuration."""
    assert entraid_config.provider_name == "entraid"
    assert entraid_config.tenant_id == "test-tenant-id"
    assert entraid_config.client_id == "test-client-id"
    assert entraid_config.client_secret == "test-client-secret"
    assert entraid_config.base_url == "https://login.microsoftonline.com"


def test_entraid_config_computed_properties(entraid_config):
    """Test computed properties of EntraIDConfig."""
    assert (
        entraid_config.authority == "https://login.microsoftonline.com/test-tenant-id"
    )
    assert (
        entraid_config.token_endpoint
        == "https://login.microsoftonline.com/test-tenant-id/oauth2/v2.0/token"
    )
    assert (
        entraid_config.authorization_endpoint
        == "https://login.microsoftonline.com/test-tenant-id/oauth2/v2.0/authorize"
    )
    assert (
        entraid_config.jwks_endpoint
        == "https://login.microsoftonline.com/test-tenant-id/discovery/v2.0/keys"
    )
    assert (
        entraid_config.well_known_endpoint
        == "https://login.microsoftonline.com/test-tenant-id/v2.0/.well-known/openid-configuration"
    )
    assert (
        entraid_config.issuer == "https://login.microsoftonline.com/test-tenant-id/v2.0"
    )


def test_entraid_config_api_version():
    """Test API version configuration."""
    from lks_idprovider_entraid.config import EntraIDConfig

    # Test v1.0 (default)
    config = EntraIDConfig(
        tenant_id="test-tenant-id",
        client_id="test-client-id",
        client_secret="test-secret",
    )
    assert config.api_version == "v1.0"

    # Test beta
    config_beta = EntraIDConfig(
        tenant_id="test-tenant-id",
        client_id="test-client-id",
        client_secret="test-secret",
        api_version="beta",
    )
    assert config_beta.api_version == "beta"


def test_entraid_config_invalid_api_version():
    """Test invalid API version raises error."""
    from lks_idprovider_entraid.config import EntraIDConfig

    with pytest.raises(ValidationError) as exc_info:
        EntraIDConfig(
            tenant_id="test-tenant-id",
            client_id="test-client-id",
            client_secret="test-secret",
            api_version="invalid",
        )
    assert "api_version must be either 'v1.0' or 'beta'" in str(exc_info.value)


def test_entraid_config_validation_empty_tenant_id():
    """Test empty tenant_id raises error."""
    from lks_idprovider_entraid.config import EntraIDConfig

    with pytest.raises(ValidationError) as exc_info:
        EntraIDConfig(
            tenant_id="",
            client_id="test-client-id",
            client_secret="test-secret",
        )
    assert "tenant_id cannot be empty" in str(exc_info.value)


def test_entraid_config_validation_empty_client_id():
    """Test empty client_id raises error."""
    from lks_idprovider_entraid.config import EntraIDConfig

    with pytest.raises(ValidationError) as exc_info:
        EntraIDConfig(
            tenant_id="test-tenant-id",
            client_id="",
            client_secret="test-secret",
        )
    assert "client_id cannot be empty" in str(exc_info.value)


def test_entraid_config_validation_settings():
    """Test validation settings."""
    from lks_idprovider_entraid.config import EntraIDConfig

    config = EntraIDConfig(
        tenant_id="test-tenant-id",
        client_id="test-client-id",
        client_secret="test-secret",
        validate_audience=False,
        validate_issuer=False,
        leeway=60,
    )
    assert config.validate_audience is False
    assert config.validate_issuer is False
    assert config.leeway == 60


def test_entraid_config_caching_settings():
    """Test caching settings."""
    from lks_idprovider_entraid.config import EntraIDConfig

    config = EntraIDConfig(
        tenant_id="test-tenant-id",
        client_id="test-client-id",
        client_secret="test-secret",
        jwks_cache_ttl=600,
        token_cache_ttl=120,
    )
    assert config.jwks_cache_ttl == 600
    assert config.token_cache_ttl == 120


def test_entraid_config_get_credential_type_client_secret(entraid_config):
    """Test get_credential_type with client secret."""
    assert entraid_config.get_credential_type() == "client_secret"


def test_entraid_config_get_credential_type_certificate(
    entraid_config_with_certificate,
):
    """Test get_credential_type with certificate."""
    assert entraid_config_with_certificate.get_credential_type() == "certificate"


def test_entraid_config_get_credential_type_managed_identity(
    entraid_config_with_managed_identity,
):
    """Test get_credential_type with managed identity."""
    assert (
        entraid_config_with_managed_identity.get_credential_type() == "managed_identity"
    )


def test_entraid_config_get_credential_type_no_credentials():
    """Test get_credential_type with no credentials raises error."""
    from lks_idprovider_entraid.config import EntraIDConfig

    config = EntraIDConfig(
        tenant_id="test-tenant-id",
        client_id="test-client-id",
    )

    with pytest.raises(ValueError) as exc_info:
        config.get_credential_type()
    assert "No valid credential configuration" in str(exc_info.value)


def test_entraid_config_multi_tenant_common():
    """Test configuration for multi-tenant with 'common'."""
    from lks_idprovider_entraid.config import EntraIDConfig

    config = EntraIDConfig(
        tenant_id="common",
        client_id="test-client-id",
        client_secret="test-secret",
    )
    assert config.tenant_id == "common"
    assert config.authority == "https://login.microsoftonline.com/common"


def test_entraid_config_multi_tenant_organizations():
    """Test configuration for multi-tenant with 'organizations'."""
    from lks_idprovider_entraid.config import EntraIDConfig

    config = EntraIDConfig(
        tenant_id="organizations",
        client_id="test-client-id",
        client_secret="test-secret",
    )
    assert config.tenant_id == "organizations"
    assert config.authority == "https://login.microsoftonline.com/organizations"


def test_entraid_config_invalid_provider_name():
    """Test invalid provider_name raises error."""
    from lks_idprovider_entraid.config import EntraIDConfig

    with pytest.raises(ValidationError) as exc_info:
        EntraIDConfig(
            provider_name="invalid",
            tenant_id="test-tenant-id",
            client_id="test-client-id",
            client_secret="test-secret",
        )
    assert "provider_name must be 'entraid'" in str(exc_info.value)


def test_entraid_config_default_scope():
    """Test default scope configuration."""
    from lks_idprovider_entraid.config import EntraIDConfig

    config = EntraIDConfig(
        tenant_id="test-tenant-id",
        client_id="test-client-id",
        client_secret="test-secret",
    )
    assert config.default_scope == "https://graph.microsoft.com/.default"

    # Test custom scope
    config_custom = EntraIDConfig(
        tenant_id="test-tenant-id",
        client_id="test-client-id",
        client_secret="test-secret",
        default_scope="https://custom.api/.default",
    )
    assert config_custom.default_scope == "https://custom.api/.default"
