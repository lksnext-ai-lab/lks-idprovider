"""Cache Provider protocol definition.

This module defines the CacheProvider protocol for caching operations.
This is an optional protocol that can be implemented to provide caching
capabilities for tokens, user data, and other frequently accessed information.
"""

from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class CacheProvider(Protocol):
    """Protocol for cache provider implementations.

    This protocol defines the interface for caching services that can be used
    by identity providers to cache tokens, user information, and other data
    to improve performance.

    Example:
        ```python
        class RedisCacheProvider(CacheProvider):
            async def get(self, key: str) -> Optional[Any]:
                # Implementation specific to Redis
                pass

            async def set(self, key: str, value: Any,
                ttl: Optional[int] = None) -> bool:
                # Implementation specific to Redis
                pass
        ```
    """

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache.

        Args:
            key: The cache key

        Returns:
            The cached value or None if not found

        Raises:
            CacheError: If there's an error accessing the cache

        Example:
            ```python
            user_data = await cache.get("user:123")
            if user_data:
                print(f"Found cached user: {user_data['username']}")
            ```
        """
        ...

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in the cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds (optional)

        Returns:
            True if the value was set successfully

        Raises:
            CacheError: If there's an error setting the cache value

        Example:
            ```python
            success = await cache.set(
                "user:123",
                {"username": "john", "email": "john@example.com"},
                ttl=3600  # 1 hour
            )
            ```
        """
        ...

    async def delete(self, key: str) -> bool:
        """Delete a value from the cache.

        Args:
            key: The cache key to delete

        Returns:
            True if the key was deleted successfully

        Raises:
            CacheError: If there's an error deleting from cache

        Example:
            ```python
            success = await cache.delete("user:123")
            if success:
                print("User data removed from cache")
            ```
        """
        ...

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: The cache key to check

        Returns:
            True if the key exists, False otherwise

        Raises:
            CacheError: If there's an error checking the cache

        Example:
            ```python
            if await cache.exists("user:123"):
                print("User data is cached")
            ```
        """
        ...

    async def get_ttl(self, key: str) -> Optional[int]:
        """Get the time to live for a cache key.

        Args:
            key: The cache key

        Returns:
            Time to live in seconds, or None if key doesn't exist or has no TTL

        Raises:
            CacheError: If there's an error accessing the cache

        Example:
            ```python
            ttl = await cache.get_ttl("user:123")
            if ttl:
                print(f"Cache expires in {ttl} seconds")
            ```
        """
        ...

    async def set_ttl(self, key: str, ttl: int) -> bool:
        """Set the time to live for a cache key.

        Args:
            key: The cache key
            ttl: Time to live in seconds

        Returns:
            True if TTL was set successfully

        Raises:
            CacheError: If there's an error setting the TTL

        Example:
            ```python
            success = await cache.set_ttl("user:123", 3600)  # 1 hour
            ```
        """
        ...

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from the cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary mapping keys to values (missing keys are omitted)

        Raises:
            CacheError: If there's an error accessing the cache

        Example:
            ```python
            data = await cache.get_many(["user:123", "user:456"])
            for key, value in data.items():
                print(f"{key}: {value}")
            ```
        """
        ...

    async def set_many(
        self, mapping: dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """Set multiple values in the cache.

        Args:
            mapping: Dictionary of key-value pairs to cache
            ttl: Time to live in seconds (optional)

        Returns:
            True if all values were set successfully

        Raises:
            CacheError: If there's an error setting cache values

        Example:
            ```python
            success = await cache.set_many({
                "user:123": {"username": "john"},
                "user:456": {"username": "jane"}
            }, ttl=3600)
            ```
        """
        ...

    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple keys from the cache.

        Args:
            keys: List of cache keys to delete

        Returns:
            Number of keys that were successfully deleted

        Raises:
            CacheError: If there's an error deleting from cache

        Example:
            ```python
            deleted_count = await cache.delete_many(["user:123", "user:456"])
            print(f"Deleted {deleted_count} cache entries")
            ```
        """
        ...

    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries, optionally matching a pattern.

        Args:
            pattern: Optional pattern to match keys (implementation-specific)

        Returns:
            Number of keys that were cleared

        Raises:
            CacheError: If there's an error clearing the cache

        Example:
            ```python
            # Clear all user cache entries
            cleared = await cache.clear("user:*")
            print(f"Cleared {cleared} user cache entries")

            # Clear entire cache
            total_cleared = await cache.clear()
            print(f"Cleared {total_cleared} total cache entries")
            ```
        """
        ...

    async def increment(self, key: str, delta: int = 1) -> int:
        """Increment a numeric value in the cache.

        Args:
            key: The cache key
            delta: The amount to increment by (default: 1)

        Returns:
            The new value after incrementing

        Raises:
            CacheError: If there's an error accessing the cache

        Example:
            ```python
            # Increment login counter
            new_count = await cache.increment("login_count:user:123")
            print(f"User has logged in {new_count} times")
            ```
        """
        ...

    async def decrement(self, key: str, delta: int = 1) -> int:
        """Decrement a numeric value in the cache.

        Args:
            key: The cache key
            delta: The amount to decrement by (default: 1)

        Returns:
            The new value after decrementing

        Raises:
            CacheError: If there's an error accessing the cache

        Example:
            ```python
            # Decrement rate limit counter
            remaining = await cache.decrement("rate_limit:user:123")
            print(f"User has {remaining} requests remaining")
            ```
        """
        ...

    # Hash operations for structured data

    async def hget(self, key: str, field: str) -> Optional[Any]:
        """Get a field value from a hash stored in cache.

        Args:
            key: The cache key for the hash
            field: The field name within the hash

        Returns:
            The field value or None if not found

        Raises:
            CacheError: If there's an error accessing the cache

        Example:
            ```python
            email = await cache.hget("user:123", "email")
            if email:
                print(f"User email: {email}")
            ```
        """
        ...

    async def hset(self, key: str, field: str, value: Any) -> bool:
        """Set a field value in a hash stored in cache.

        Args:
            key: The cache key for the hash
            field: The field name within the hash
            value: The value to set

        Returns:
            True if the field was set successfully

        Raises:
            CacheError: If there's an error setting the cache value

        Example:
            ```python
            success = await cache.hset("user:123", "email", "new@example.com")
            ```
        """
        ...

    async def hgetall(self, key: str) -> dict[str, Any]:
        """Get all fields and values from a hash stored in cache.

        Args:
            key: The cache key for the hash

        Returns:
            Dictionary containing all fields and values

        Raises:
            CacheError: If there's an error accessing the cache

        Example:
            ```python
            user_data = await cache.hgetall("user:123")
            print(f"User: {user_data}")
            ```
        """
        ...

    # Optional configuration and health check methods

    async def ping(self) -> bool:
        """Ping the cache to check connectivity.

        Returns:
            True if cache is accessible

        Example:
            ```python
            if await cache.ping():
                print("Cache is accessible")
            ```
        """
        ...

    async def get_cache_info(self) -> dict[str, Any]:
        """Get cache information and statistics.

        Returns:
            Dictionary containing cache information

        Example:
            ```python
            info = await cache.get_cache_info()
            print(f"Cache type: {info['type']}")
            print(f"Memory usage: {info['memory_usage']}")
            ```
        """
        ...

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the cache provider.

        Returns:
            Dictionary containing health status information

        Example:
            ```python
            health = await cache.health_check()
            if health["status"] == "healthy":
                print("Cache provider is healthy")
            ```
        """
        ...
