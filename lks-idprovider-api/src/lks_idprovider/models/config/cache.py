"""
Caching configuration model for LKS Identity Provider API.

This module contains caching-related configuration options.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CacheConfig(BaseModel):
    """Caching configuration for providers."""

    enabled: bool = Field(default=True, description="Whether caching is enabled")

    # TTL settings (in seconds)
    jwks_cache_ttl: int = Field(
        default=300, ge=60, le=3600, description="JWKS cache TTL in seconds"
    )
    token_cache_ttl: int = Field(
        default=300, ge=60, le=1800, description="Token validation cache TTL in seconds"
    )
    user_info_cache_ttl: int = Field(
        default=300, ge=60, le=1800, description="User info cache TTL in seconds"
    )

    # Cache size limits
    max_cache_size: int = Field(
        default=1000, ge=100, le=10000, description="Maximum cache entries"
    )

    # Redis settings (optional)
    redis_url: Optional[str] = Field(
        None, description="Redis URL for distributed caching"
    )
    redis_prefix: str = Field(default="lks_idprovider", description="Redis key prefix")

    model_config = ConfigDict(validate_assignment=True)
