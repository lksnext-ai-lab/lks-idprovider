# LKS-idprovider Implementation Plan

## Overview

This document outlines the step-by-step implementation plan for the LKS-idprovider project, which consists of two separate packages designed for **REST API Security**:

1. **lks-idprovider-api**: Pure API specification with protocols, models, and contracts
2. **lks-idprovider-keycloak**: Keycloak provider implementation with FastAPI integration

**Important**: This library is designed for **REST API securization** where users and services are already authenticated and have tokens. The library focuses on:
- **Token validation and verification** (not initial authentication)
- **Identity extraction from tokens** (users are already authenticated)
- **Authorization and access control** (roles, permissions, scopes)
- **API middleware and security decorators** for FastAPI and other frameworks

The implementation follows a unified Identity model where both users and clients are represented as Identity instances with User and ClientIdentity subclasses.

## Identity Model Architecture

The library uses a unified Identity model to represent both users and clients:

```python
class Identity(BaseModel):
    """Base class for all identities (users and clients)."""

    id: str
    provider: str
    claims: Dict[str, Any]


class User(Identity):
    """Represents a user identity."""

    username: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class ClientIdentity(Identity):
    """Represents a client identity (service-to-service communication)."""

    client_id: str
    client_name: Optional[str] = None


class AuthContext(BaseModel):
    """Authentication context containing identity and authorization info."""

    identity: Identity  # Always contains either User or ClientIdentity
    roles: List[Role]
    permissions: List[Permission]
    token_info: Dict[str, Any]
```

This design allows:
- **Unified handling**: All authentication flows return AuthContext with Identity
- **Type safety**: FastAPI dependencies can request specific identity types
- **Extensibility**: Easy to add new identity types in the future
- **Clarity**: Clear distinction between user and client authentication

## Implementation Roadmap

### Sprint 1: Foundation (API Package Core)
**Priority: HIGH - Core models and protocols**
- Step 1.1: Project Structure Setup
- Step 1.2: Core Data Models - Identity Hierarchy
- Step 1.3: Token Models and Types
- Step 1.5: Protocol Definitions

**Deliverable**: Working API package with Identity model and protocols

### Sprint 2: API Package Completion
**Priority: HIGH - Complete API specification**
- Step 1.4: Configuration Models
- Step 1.6: Package Exports and API
- Step 1.7: Testing Setup
- Step 1.8: Build and Distribution Setup

**Deliverable**: Complete, installable API package

### Sprint 3: Keycloak Core Implementation
**Priority: HIGH - Basic Keycloak integration**
- Step 2.1: Project Structure Setup
- Step 2.2: Keycloak Configuration
- Step 2.4: HTTP Client Utilities
- Step 2.5: Keycloak REST API Client
- Step 2.6: Token Validator Implementation (REST API Based)

**Deliverable**: Working token validation with Keycloak via REST API

### Sprint 4: Identity and Provider Implementation
**Priority: HIGH - Core provider functionality**
- Step 2.7: User Info Service
- Step 2.8: Client Credentials Service
- Step 2.9: Claims Extractor (with Identity model support)
- Step 2.10: Keycloak Provider Implementation
- Step 2.11: Client Credentials Provider Implementation
- Step 2.15: Unit Tests (core functionality)

**Deliverable**: Complete provider with User/ClientIdentity support via REST API

### Sprint 5: FastAPI Integration
**Priority: MEDIUM - Web framework integration**
- Step 2.11: FastAPI Security Schemes
- Step 2.12: FastAPI Dependencies (with Identity-aware dependencies)
- Step 2.13: FastAPI Decorators
- Step 2.14: FastAPI Middleware
- Step 2.15: FastAPI Exception Handlers

**Deliverable**: Complete FastAPI integration

### Sprint 6: Testing and Polish
**Priority: MEDIUM - Quality assurance**
- Step 2.16: Integration Tests
- Step 2.14: Testing Utilities
- Final testing and validation

**Deliverable**: Production-ready library

### Sprint 7: Advanced Features
**Priority: LOW - Nice-to-have features**
- Step 2.3: HTTP Client Utilities (advanced features)
- Step 2.11: Caching Implementation (Redis support)
- Performance optimizations
- Additional provider support

**Deliverable**: Enhanced library with advanced features

## Phase 1: API Specification Package (lks-idprovider-api)

### Step 1.1: Project Structure Setup ✅ COMPLETED
- [x] Create basic project structure with src/ layout
- [x] Set up pyproject.toml with Poetry configuration (Updated to Poetry 2.0+ PEP 621)
- [x] Create initial README.md with project description
- [x] Set up basic package structure under src/lks_idprovider/
- [x] **BONUS**: Created separate project directories for API and Keycloak packages
- [x] **BONUS**: Updated to Poetry 2.0+ with PEP 621 compliance

**Files created:**
- `lks-idprovider-api/pyproject.toml` ✅
- `lks-idprovider-api/README.md` ✅
- `lks-idprovider-api/src/lks_idprovider/__init__.py` ✅
- `lks-idprovider-api/.gitignore` ✅
- `lks-idprovider-keycloak/pyproject.toml` ✅
- `lks-idprovider-keycloak/README.md` ✅
- Root `README.md` explaining project structure ✅

### Step 1.2: Core Data Models - Identity Hierarchy ✅ COMPLETED
- [x] Create base exception hierarchy (refactored into separate error files)
- [x] Implement base Identity class in separate file
- [x] Implement User subclass in separate file
- [x] Implement ClientIdentity subclass in separate file
- [x] Implement Role model in separate file
- [x] Implement Permission model in separate file
- [x] Implement AuthContext model (containing Identity)
- [x] **BONUS**: Refactored all models into separate files for better organization
- [x] **BONUS**: Created proper directory structure for identity and error models

**Files created:**
- `src/lks_idprovider/models/__init__.py` ✅
- `src/lks_idprovider/models/errors/` directory with individual error files ✅
  - `base.py`, `token.py`, `client_credentials.py`, `provider.py`, `configuration.py`, `auth.py`
- `src/lks_idprovider/models/identity/` directory ✅
  - `identity.py`, `user.py`, `client_identity.py`
- `src/lks_idprovider/models/auth.py` (AuthContext) ✅
- `src/lks_idprovider/models/role.py` ✅
- `src/lks_idprovider/models/permission.py` ✅

### Step 1.3: Token Models and Types ✅ COMPLETED
- [x] Create Token models in separate token directory
- [x] Define TokenType enum in `types/enums.py`
- [x] Define AuthMethod enum in `types/enums.py`
- [x] Create type aliases in `types/aliases.py`
- [x] **BONUS**: Created TokenValidationResult model for validation operations

**Files created:**
- `src/lks_idprovider/models/token/` directory ✅
  - `token_info.py` (TokenInfo model) ✅
  - `validation_result.py` (TokenValidationResult model) ✅
  - `__init__.py` ✅
- `src/lks_idprovider/types/__init__.py` ✅
- `src/lks_idprovider/types/enums.py` ✅
- `src/lks_idprovider/types/aliases.py` ✅

### Step 1.4: Configuration Models ✅ COMPLETED
- [x] Create base configuration classes in `models/config/`
- [x] Define provider configuration interface (BaseProviderConfig)
- [x] Create JWT configuration model (JWTConfig)
- [x] Create caching configuration model (CacheConfig)
- [x] Create client credentials configuration model (ClientCredentialsConfig)
- [x] Add validation using Pydantic
- [x] **BONUS**: All configuration models in separate files for better organization

**Files created:**
- `src/lks_idprovider/models/config/` directory ✅
  - `base.py` (BaseProviderConfig) ✅
  - `jwt.py` (JWTConfig) ✅
  - `cache.py` (CacheConfig) ✅
  - `client_credentials.py` (ClientCredentialsConfig) ✅
  - `__init__.py` ✅

### Step 1.5: Protocol Definitions ✅ COMPLETED - UPDATED FOR REST API SECURITY
- [x] Create IdentityProvider protocol in `protocols/provider.py` (focused on token validation)
- [x] Create ClientCredentialsProvider protocol in `protocols/client_credentials.py` (service-to-service tokens)
- [x] Create TokenValidator protocol in `protocols/token_validator.py` (comprehensive token validation)
- [x] Create CacheProvider protocol in `protocols/cache.py` (optional caching support)
- [x] Add comprehensive docstrings with examples for REST API security use cases
- [x] Ensure protocols work with unified Identity model (User/ClientIdentity)
- [x] **IMPORTANT**: Updated protocols to focus on REST API security (token validation, not authentication)
- [x] **BONUS**: Added CacheProvider protocol for optional caching capabilities
- [x] **BONUS**: Extensive documentation and examples for FastAPI middleware and dependencies

**Key Changes for REST API Security:**
- Removed `authenticate_user()` - users are already authenticated with tokens
- Removed `refresh_token()` and `logout()` - handled by auth service, not API service
- Focus on `validate_token()` and `get_auth_context()` as primary methods
- Updated all examples to show FastAPI middleware and dependency patterns
- Emphasized token-based identity extraction rather than credential-based authentication

**Files created:**
- `src/lks_idprovider/protocols/__init__.py` ✅
- `src/lks_idprovider/protocols/provider.py` ✅ (Updated for REST API security)
- `src/lks_idprovider/protocols/client_credentials.py` ✅ (Updated for service-to-service API security)
- `src/lks_idprovider/protocols/token_validator.py` ✅
- `src/lks_idprovider/protocols/cache.py` ✅
- Updated `src/lks_idprovider/__init__.py` with protocol exports ✅

### Step 1.6: Package Exports and API ✅ COMPLETED
- [x] Update main `__init__.py` with focused public API exports
- [x] Update sub-package `__init__.py` files with proper exports
- [x] Ensure clean import paths and package structure
- [x] Add version information and metadata
- [x] **BONUS**: Organized package structure with both convenience and explicit imports

**Files updated:**
- `src/lks_idprovider/__init__.py` ✅ (Focused API with package structure)
- All sub-package `__init__.py` files ✅

### Step 1.7: Testing Setup ✅ COMPLETED
- [x] Create basic test structure with organized test files
- [x] Add comprehensive tests for data models (identity, auth, token, config, errors)
- [x] Add thorough tests for protocol definitions with mock implementations
- [x] Set up pytest configuration with async support and coverage
- [x] **BONUS**: Created test runner script for convenient development testing
- [x] **BONUS**: Comprehensive test fixtures and mock implementations for all protocols

**Files created:**
- `tests/__init__.py` ✅
- `tests/conftest.py` ✅ (Comprehensive fixtures and mock implementations)
- `tests/test_models.py` ✅ (Complete model testing with validation)
- `tests/test_protocols.py` ✅ (Protocol testing with workflow validation)
- `run_tests.py` ✅ (Test runner script)
- Updated `pyproject.toml` with pytest configuration ✅

### Step 1.8: Build and Distribution Setup
- [x] Configure build system in pyproject.toml
- [x] Set up development dependencies
- [x] Configure linting and formatting tools
- [x] Create Docker-based build system for CI/CD
- [x] Set up Jenkins pipeline for automated builds
- [x] Configure Nexus repository publishing
- [x] Test package installation and build process

**Files created/updated:**
- `pyproject.toml` (already configured)
- `Dockerfile` (multi-stage build)
- `Jenkinsfile` (CI/CD pipeline)
- `docker-compose.yml` (development environment)
- `Makefile` (updated with Docker commands)
- `.dockerignore` (build optimization)
- `DOCKER_BUILD.md` (documentation)

## Phase 2: Keycloak Provider Package (lks-idprovider-keycloak)

### Step 2.1: Development Environment & Project Structure Setup

**First: Create Tests**
- [ ] Create test environment configuration (`tests/conftest.py`)
- [ ] Create integration test helper functions
- [ ] Create test fixtures for Keycloak tokens and users
- [ ] Write tests that verify package structure and imports

**Then: Implementation**
- [ ] Create project structure with src/ layout
- [ ] Set up pyproject.toml with dependencies on API package
- [ ] Create README.md with Keycloak-specific documentation
- [ ] Set up package structure under src/lks_idprovider_keycloak

**Files to create:**
- `docker-compose.dev.yml` ✅ COMPLETED
- `keycloak-config/lks-test-realm.json` ✅ COMPLETED
- `keycloak-config/README.md` ✅ COMPLETED
- `tests/conftest.py`
- `tests/test_project_structure.py`
- `pyproject.toml`
- `README.md`
- `src/lks_idprovider_keycloak/__init__.py`
- `.gitignore`

### Step 2.2: Keycloak Configuration

**First: Create Tests**
- [ ] Write tests for `KeycloakConfig` validation (`tests/test_config.py`)
- [ ] Test environment variable loading
- [ ] Test SSL and timeout configuration validation
- [ ] Test invalid configuration scenarios

**Then: Implementation**
- [ ] Create KeycloakConfig class in `provider/config.py`
- [ ] Add validation for required Keycloak parameters
- [ ] Support environment variable configuration
- [ ] Add SSL and timeout configuration options

**Files to create:**
- `tests/test_config.py`
- `src/lks_idprovider_keycloak/provider/__init__.py`
- `src/lks_idprovider_keycloak/provider/config.py`

### Step 2.3: HTTP Client Utilities

**First: Create Tests**
- [ ] Write tests for HTTP client creation (`tests/test_http_client.py`)
- [ ] Test SSL verification and timeout handling
- [ ] Test retry logic and error handling
- [ ] Test connection pooling and async operations
- [ ] Mock Keycloak endpoints for testing

**Then: Implementation**
- [ ] Create async HTTP client for Keycloak REST API
- [ ] Implement proper error handling and retries
- [ ] Support for SSL verification and timeout configuration
- [ ] Add connection pooling and keep-alive

**Files to create:**
- `tests/test_http_client.py`
- `src/lks_idprovider_keycloak/utils/__init__.py`
- `src/lks_idprovider_keycloak/utils/http_client.py`

**Implementation Strategy:**
- Primary validation through token introspection (RFC 7662 compliant)
- Client credentials flow through token endpoint (RFC 6749 Section 4.4)
- User info enrichment through userinfo endpoint
- Optional JWT validation using JWK keys for performance optimization
- Well-known endpoint for dynamic configuration discovery

### Step 2.4: Keycloak REST API Client

**First: Create Tests**
- [ ] Write tests for Keycloak REST API endpoints (`tests/test_keycloak_api.py`)
- [ ] Test well-known configuration endpoint
- [ ] Test token introspection endpoint
- [ ] Test user info endpoint
- [ ] Test token endpoint (client credentials)
- [ ] Test certificate endpoint (JWK keys)
- [ ] Mock all external HTTP calls

**Then: Implementation**
- [ ] Implement REST API client for core Keycloak endpoints:
  - **Well-known Configuration**: `/realms/{realm}/.well-known/openid-connect-configuration`
  - **Token Introspection**: `/realms/{realm}/protocol/openid-connect/token/introspect`
  - **User Info**: `/realms/{realm}/protocol/openid-connect/userinfo`
  - **Token Endpoint**: `/realms/{realm}/protocol/openid-connect/token` (for client credentials)
  - **Certificate Endpoint**: `/realms/{realm}/protocol/openid-connect/certs` (for JWK keys)

**Files to create:**
- `tests/test_keycloak_api.py`
- `src/lks_idprovider_keycloak/provider/keycloak_api.py`

### Step 2.5: Token Validator Implementation

**First: Create Tests**
- [ ] Write tests for token validation (`tests/test_token_validator.py`)
- [ ] Test JWT signature verification
- [ ] Test token expiration validation
- [ ] Test issuer and audience validation
- [ ] Test JWKS key rotation handling
- [ ] Test local vs remote validation strategies
- [ ] Test error scenarios (expired, malformed, invalid tokens)

**Then: Implementation**
- [ ] Implement JWT token validation using Keycloak's REST API
- [ ] Support both local JWT validation and remote token introspection
- [ ] Handle JWKS key rotation and caching
- [ ] Implement clock skew tolerance
- [ ] Add comprehensive error handling

**Files to create:**
- `tests/test_token_validator.py`
- `src/lks_idprovider_keycloak/provider/token_validator.py`

### Step 2.6: Claims Extractor & Identity Mapping

**First: Create Tests**
- [ ] Write tests for claims extraction (`tests/test_claims_extractor.py`)
- [ ] Test user claims to User model mapping
- [ ] Test client claims to ClientIdentity model mapping
- [ ] Test role and permission extraction
- [ ] Test custom attribute handling
- [ ] Test error scenarios (missing claims, invalid format)

**Then: Implementation**
- [ ] Extract user information from tokens
- [ ] Extract client information from tokens
- [ ] Map Keycloak claims to unified Identity model (User/ClientIdentity)
- [ ] Handle custom attributes and additional claims
- [ ] Extract roles and permissions from token claims

**Files to create:**
- `tests/test_claims_extractor.py`
- `src/lks_idprovider_keycloak/provider/claims_extractor.py`

### Step 2.7: User Info Service

**First: Create Tests**
- [ ] Write tests for user info service (`tests/test_user_info_service.py`)
- [ ] Test user profile retrieval from Keycloak
- [ ] Test user profile mapping to User model
- [ ] Test caching of user information
- [ ] Test error handling (user not found, invalid token)

**Then: Implementation**
- [ ] Implement user information retrieval from Keycloak
- [ ] Handle user profile mapping to User model
- [ ] Add caching for user profile information
- [ ] Implement proper error handling

**Files to create:**
- `tests/test_user_info_service.py`
- `src/lks_idprovider_keycloak/provider/user_info_service.py`

### Step 2.8: Client Credentials Service

**First: Create Tests**
- [ ] Write tests for client credentials (`tests/test_client_credentials.py`)
- [ ] Test client credentials token request
- [ ] Test scope-based token requests
- [ ] Test client authentication methods
- [ ] Test token caching and refresh logic
- [ ] Test error handling (invalid credentials, network errors)

**Then: Implementation**
- [ ] Implement client credentials flow
- [ ] Support scope-based token requests
- [ ] Handle client authentication
- [ ] Add token caching and refresh logic
- [ ] Implement comprehensive error handling

**Files to create:**
- `tests/test_client_credentials.py`
- `src/lks_idprovider_keycloak/provider/client_credentials_service.py`

### Step 2.9: Main Provider Implementation

**First: Create Tests**
- [ ] Write tests for main provider (`tests/test_keycloak_provider.py`)
- [ ] Test IdentityProvider protocol implementation
- [ ] Test ClientCredentialsProvider protocol implementation
- [ ] Test unified AuthContext creation with Identity
- [ ] Test user token validation returning User identity
- [ ] Test client token validation returning ClientIdentity
- [ ] Test error handling and provider-specific exceptions
- [ ] Integration tests with live Keycloak instance

**Then: Implementation**
- [ ] Implement `KeycloakProvider` (IdentityProvider protocol)
- [ ] Implement `KeycloakClientCredentialsProvider` (ClientCredentialsProvider protocol)
- [ ] Ensure both return unified AuthContext with Identity
- [ ] Integrate all services (token validator, claims extractor, user info, client credentials)
- [ ] Add comprehensive logging and monitoring

**Files to create:**
- `tests/test_keycloak_provider.py`
- `tests/test_integration.py`
- `src/lks_idprovider_keycloak/provider/keycloak_provider.py`

### Step 2.10: Caching Implementation

**First: Create Tests**
- [ ] Write tests for caching (`tests/test_cache.py`)
- [ ] Test in-memory cache for JWKS keys
- [ ] Test Redis cache integration (optional)
- [ ] Test TTL configuration and expiration
- [ ] Test cache key strategies for multi-tenant scenarios
- [ ] Test cache invalidation and refresh

**Then: Implementation**
- [ ] Create cache interface implementation
- [ ] Support in-memory caching for JWKS keys
- [ ] Support Redis caching (optional) for production environments
- [ ] Add TTL configuration for different cache types
- [ ] Implement cache key strategies for multi-tenant scenarios

**Files to create:**
- `tests/test_cache.py`
- `src/lks_idprovider_keycloak/utils/cache.py`

### Step 2.11: FastAPI Security Schemes

**First: Create Tests**
- [ ] Write tests for security schemes (`tests/fastapi/test_security.py`)
- [ ] Test OpenAPI security scheme generation
- [ ] Test Bearer token authentication scheme
- [ ] Test OAuth2 password flow support
- [ ] Test security scheme documentation

**Then: Implementation**
- [ ] Create OpenAPI security schemes
- [ ] Support Bearer token authentication
- [ ] Add OAuth2 password flow support
- [ ] Configure security scheme documentation

**Files to create:**
- `tests/fastapi/__init__.py`
- `tests/fastapi/test_security.py`
- `src/lks_idprovider_keycloak/fastapi/__init__.py`
- `src/lks_idprovider_keycloak/fastapi/security.py`

### Step 2.12: FastAPI Dependencies

**First: Create Tests**
- [ ] Write tests for FastAPI dependencies (`tests/fastapi/test_dependencies.py`)
- [ ] Test `get_auth_context()` dependency (returns AuthContext with Identity)
- [ ] Test `get_user()` dependency (returns User, fails if ClientIdentity)
- [ ] Test `get_client_identity()` dependency (returns ClientIdentity, fails if User)
- [ ] Test `get_identity()` dependency (returns Identity base class)
- [ ] Test provider injection dependency
- [ ] Test optional authentication dependency
- [ ] Test error handling for each dependency

**Then: Implementation**
- [ ] Create authentication dependencies
- [ ] Implement get_auth_context dependency (returns AuthContext with Identity)
- [ ] Implement get_user dependency (returns User, raises error if ClientIdentity)
- [ ] Implement get_client_identity dependency (returns ClientIdentity, raises error if User)
- [ ] Implement get_identity dependency (returns Identity base class)
- [ ] Add provider injection dependency
- [ ] Create optional authentication dependency

**Files to create:**
- `tests/fastapi/test_dependencies.py`
- `src/lks_idprovider_keycloak/fastapi/dependencies.py`

### Step 2.13: FastAPI Decorators & Middleware

**First: Create Tests**
- [ ] Write tests for decorators (`tests/fastapi/test_decorators.py`)
- [ ] Test role-based access decorators
- [ ] Test permission-based decorators
- [ ] Test route protection decorators
- [ ] Test custom authorization logic
- [ ] Write tests for middleware (`tests/fastapi/test_middleware.py`)
- [ ] Test automatic token validation middleware
- [ ] Test middleware error handling

**Then: Implementation**
- [ ] Create role-based decorators
- [ ] Create permission-based decorators
- [ ] Add route protection decorators
- [ ] Support custom authorization logic
- [ ] Create authentication middleware
- [ ] Support automatic token validation

**Files to create:**
- `tests/fastapi/test_decorators.py`
- `tests/fastapi/test_middleware.py`
- `src/lks_idprovider_keycloak/fastapi/decorators.py`
- `src/lks_idprovider_keycloak/fastapi/middleware.py`

### Step 2.14: Integration Testing & Documentation

**First: Create Tests**
- [ ] Write comprehensive integration tests (`tests/integration/`)
- [ ] Test complete user authentication flow
- [ ] Test complete client credentials flow
- [ ] Test FastAPI application integration
- [ ] Test error scenarios and edge cases
- [ ] Performance and load testing

**Then: Implementation**
- [ ] Create testing utilities and fixtures
- [ ] Complete README and API documentation
- [ ] Add code examples and usage guides
- [ ] Create troubleshooting guide
- [ ] Add performance optimization notes

**Files to create:**
- `tests/integration/test_user_flow.py`
- `tests/integration/test_client_flow.py`
- `tests/integration/test_fastapi_integration.py`
- `README.md` (comprehensive)
- `docs/` (additional documentation)

### Step 2.15: Build & Distribution

**First: Create Tests**
- [ ] Write tests for package distribution (`tests/test_packaging.py`)
- [ ] Test package installation and imports
- [ ] Test version compatibility
- [ ] Test Docker container builds

**Then: Implementation**
- [ ] Finalize build configuration
- [ ] Set up continuous integration
- [ ] Configure automated testing
- [ ] Prepare for distribution

**Files to create:**
- `tests/test_packaging.py`
- `Dockerfile` (if not exists)
- `Jenkinsfile` (if not exists)
- `.github/workflows/` (if using GitHub Actions)

## Test-Driven Development Workflow

For each implementation step:

1. **🧪 TESTS FIRST**: Write comprehensive tests that define the expected behavior
2. **✅ VALIDATE TESTS**: Review tests with stakeholders to ensure they match requirements
3. **🔨 IMPLEMENT**: Write the minimum code needed to make tests pass
4. **🔄 REFACTOR**: Clean up code while keeping tests green
5. **📖 DOCUMENT**: Update documentation and examples

## Development Environment Commands

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Run tests for a specific step (example: config tests)
docker-compose -f docker-compose.dev.yml exec python-dev python -m pytest tests/test_config.py -v

# Run all tests
docker-compose -f docker-compose.dev.yml exec python-dev python -m pytest tests/ -v

# Access development shell
docker-compose -f docker-compose.dev.yml exec python-dev bash

# Stop environment
docker-compose -f docker-compose.dev.yml down
```
