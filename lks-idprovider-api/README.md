# LKS-idprovider API


 API specification for the LKS Identity Provider library, providing protocols, models, and contracts for identity provider implementations.

## Overview

This package contains the core API specification for the LKS-idprovider ecosystem:

- **Protocols**: Define contracts for identity provider implementations
- **Models**: Data models for authentication context, identities, tokens, and configuration
- **Types**: Enums and type definitions for consistency across implementations
- **Contracts**: Validation and lifecycle contracts for provider compliance

## Key Features

- **Unified Identity Model**: Support for both user and client identities through a common interface
- **Protocol-Based Design**: Clear contracts for implementing identity providers
- **Type Safety**: Full type hints and Pydantic models for validation
- **Framework Agnostic**: Pure API specification without implementation dependencies
- **Extensible**: Easy to extend for custom identity providers and use cases


## Core Components

### Protocols

- **IdentityProvider**: Main protocol for token validation and authentication
- **ClientCredentialsProvider**: Protocol for OAuth2 client credentials flow

### Models

- **AuthContext**: Complete authentication context with identity and authorization info
- **Identity**: Base class for all identities (users and clients)
- **User**: Represents authenticated users with profile information
- **ClientIdentity**: Represents authenticated clients (service-to-service)
- **Role**: User roles and permissions
- **Token**: Token information and metadata

### Configuration

- **ProviderConfig**: Base configuration for identity providers
- Provider-specific configuration is supplied by each implementation.

See the [API specification](https://github.com/lksnext-ai-lab/lks-idprovider/blob/main/docs/API_SPECIFICATION.md)
and [partner integration guide](https://github.com/lksnext-ai-lab/lks-idprovider/blob/main/docs/partner-integration.md).
