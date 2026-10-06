"""
Tests for authentication and authorization dependencies.
"""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from lks_idprovider.models.auth import AuthContext
from lks_idprovider_fastapi.dependencies import (
    get_auth_context,
    get_default_provider,
    login_required,
    requires_any_role,
    requires_role,
)

# Import common fixtures and utilities
from .conftest import (
    MockUserProvider,
    override_get_auth_context_factory,
    override_provider_factory,
)

# Create a FastAPI app for testing
app = FastAPI()


# Test endpoints using the dependencies
@app.get("/profile")
async def get_profile(auth_context: AuthContext = Depends(login_required)):
    return {"username": auth_context.identity.id}


@app.get("/admin")
async def get_admin(auth_context: AuthContext = Depends(requires_role("admin"))):
    return {"message": "admin access"}


@app.get("/manager")
async def get_manager(
    auth_context: AuthContext = Depends(requires_role("manager", client="app1")),
):
    return {"message": "manager access"}


@app.get("/editor")
async def get_editor(
    auth_context: AuthContext = Depends(requires_any_role("editor", "admin")),
):
    return {"message": "editor access"}


provider = MockUserProvider()  # type: ignore
client = TestClient(app)


# Ensure all dependency overrides are cleared after each test
@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    yield
    app.dependency_overrides.clear()


class TestAuthDependencies:
    """Test the authentication and authorization dependencies with a TestClient."""

    def test_login_required_success(self, mock_auth_context):
        app.dependency_overrides[get_default_provider] = override_provider_factory(
            provider
        )
        app.dependency_overrides[get_auth_context] = override_get_auth_context_factory(
            mock_auth_context
        )
        response = client.get(
            "/profile", headers={"Authorization": "Bearer user_token"}
        )
        assert response.status_code == 200
        assert response.json() == {"username": "testuser"}

    def test_login_required_failure(self, mock_auth_context):
        app.dependency_overrides[get_default_provider] = override_provider_factory(
            provider
        )
        app.dependency_overrides[get_auth_context] = override_get_auth_context_factory(
            mock_auth_context
        )
        response = client.get(
            "/profile", headers={"Authorization": "Bearer false_token"}
        )
        assert response.status_code == 401

    def test_requires_role_success(self, mock_auth_context):
        app.dependency_overrides[get_auth_context] = override_get_auth_context_factory(
            mock_auth_context
        )
        response = client.get("/admin", headers={"Authorization": "Bearer user_token"})
        assert response.status_code == 200
        assert response.json() == {"message": "admin access"}

    def test_requires_role_failure(self, mock_auth_context_no_roles):
        app.dependency_overrides[get_auth_context] = override_get_auth_context_factory(
            mock_auth_context_no_roles
        )
        response = client.get("/admin", headers={"Authorization": "Bearer user_token"})
        assert response.status_code == 403
        assert "Required role 'admin'" in response.json()["detail"]

    def test_requires_client_role_success(self, mock_auth_context):
        app.dependency_overrides[get_auth_context] = override_get_auth_context_factory(
            mock_auth_context
        )
        response = client.get(
            "/manager", headers={"Authorization": "Bearer user_token"}
        )
        assert response.status_code == 200
        assert response.json() == {"message": "manager access"}

    def test_requires_any_role_success(self, mock_auth_context):
        app.dependency_overrides[get_auth_context] = override_get_auth_context_factory(
            mock_auth_context
        )
        response = client.get("/editor", headers={"Authorization": "Bearer user_token"})
        assert response.status_code == 200
        assert response.json() == {"message": "editor access"}

    def test_requires_any_role_failure(self, mock_auth_context_no_roles):
        app.dependency_overrides[get_auth_context] = override_get_auth_context_factory(
            mock_auth_context_no_roles
        )
        response = client.get("/editor", headers={"Authorization": "Bearer user_token"})
        assert response.status_code == 403
        assert "At least one of roles" in response.json()["detail"]
