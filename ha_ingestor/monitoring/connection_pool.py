"""Connection pool management for efficient resource utilization."""

import asyncio
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from ..metrics import get_metrics_collector
from ..utils.logging import get_logger


class ConnectionState(Enum):
    """Connection state enumeration."""

    IDLE = "idle"
    ACTIVE = "active"
    CONNECTING = "connecting"
    ERROR = "error"
    CLOSED = "closed"


T = TypeVar("T")


@dataclass
class PooledConnection(Generic[T]):
    """A connection in the pool."""

    id: str
    connection: T
    state: ConnectionState
    created_at: datetime
    last_used: datetime
    use_count: int = 0
    error_count: int = 0
    last_error: str | None = None

    def is_healthy(self) -> bool:
        """Check if connection is healthy."""
        return self.state in [ConnectionState.IDLE, ConnectionState.ACTIVE]

    def is_expired(self, max_idle_time: float) -> bool:
        """Check if connection has been idle too long."""

        idle_time = (datetime.now(UTC) - self.last_used).total_seconds()
        return idle_time > max_idle_time

    def mark_used(self) -> None:
        """Mark connection as used."""

        self.last_used = datetime.now(UTC)
        self.use_count += 1
        if self.state == ConnectionState.IDLE:
            self.state = ConnectionState.ACTIVE

    def mark_idle(self) -> None:
        """Mark connection as idle."""
        self.state = ConnectionState.IDLE

    def mark_error(self, error: str) -> None:
        """Mark connection as having an error."""
        self.state = ConnectionState.ERROR
        self.error_count += 1
        self.last_error = error


class ConnectionPool:
    """Generic connection pool for managing multiple connections."""

    def __init__(
        self,
        name: str,
        max_connections: int = 10,
        min_connections: int = 2,
        max_idle_time: float = 300.0,  # 5 minutes
        connection_timeout: float = 30.0,
        health_check_interval: float = 60.0,
    ):
        """Initialize connection pool.

        Args:
            name: Pool name for identification
            max_connections: Maximum number of connections in pool
            min_connections: Minimum number of connections to maintain
            max_idle_time: Maximum time a connection can be idle
            connection_timeout: Timeout for connection operations
            health_check_interval: Interval for health checks
        """
        self.name = name
        self.logger = get_logger(__name__)
        self.metrics_collector = get_metrics_collector()

        # Pool configuration
        self.max_connections = max_connections
        self.min_connections = min_connections
        self.max_idle_time = max_idle_time
        self.connection_timeout = connection_timeout
        self.health_check_interval = health_check_interval

        # Connection management
        self._connections: dict[str, PooledConnection] = {}
        self._connection_factory: Callable | None = None
        self._health_checker: Callable | None = None
        self._connection_validator: Callable | None = None

        # Pool state
        self._active_connections = 0
        self._idle_connections = 0
        self._error_connections = 0
        self._total_connections_created = 0
        self._total_connections_destroyed = 0

        # Management task
        self._management_task: asyncio.Task | None = None
        self._running = False

        # Statistics
        self._last_health_check = time.time()

    def set_connection_factory(self, factory: Callable) -> None:
        """Set the connection factory function.

        Args:
            factory: Function that creates new connections
        """
        self._connection_factory = factory
        self.logger.info("Set connection factory", pool=self.name)

    def set_health_checker(self, checker: Callable) -> None:
        """Set the health check function.

        Args:
            checker: Function that checks connection health
        """
        self._health_checker = checker
        self.logger.info("Set health checker", pool=self.name)

    def set_connection_validator(self, validator: Callable) -> None:
        """Set the connection validation function.

        Args:
            validator: Function that validates connections
        """
        self._connection_validator = validator
        self.logger.info("Set connection validator", pool=self.name)

    async def start(self) -> None:
        """Start the connection pool management."""
        if self._running:
            self.logger.warning("Pool already running", pool=self.name)
            return

        self._running = True
        self._management_task = asyncio.create_task(self._management_loop())

        # Initialize minimum connections
        await self._initialize_min_connections()

        self.logger.info(
            "Started connection pool",
            pool=self.name,
            min_connections=self.min_connections,
            max_connections=self.max_connections,
        )

    async def stop(self) -> None:
        """Stop the connection pool management."""
        if not self._running:
            return

        self._running = False
        if self._management_task:
            self._management_task.cancel()
            try:
                await self._management_task
            except asyncio.CancelledError:
                pass
            self._management_task = None

        # Close all connections
        await self._close_all_connections()

        self.logger.info("Stopped connection pool", pool=self.name)

    async def get_connection(self) -> Any | None:
        """Get a connection from the pool.

        Returns:
            Connection object or None if unavailable
        """
        # Try to get an idle connection
        connection = await self._get_idle_connection()
        if connection:
            return connection

        # Try to create a new connection
        if len(self._connections) < self.max_connections:
            connection = await self._create_connection()
            if connection:
                return connection

        # Wait for a connection to become available
        connection = await self._wait_for_connection()
        return connection

    async def return_connection(self, connection: Any) -> None:
        """Return a connection to the pool.

        Args:
            connection: Connection to return
        """
        connection_id = self._find_connection_id(connection)
        if not connection_id:
            self.logger.warning("Connection not found in pool", pool=self.name)
            return

        pooled_connection = self._connections[connection_id]
        pooled_connection.mark_idle()

        # Update pool state
        self._active_connections -= 1
        self._idle_connections += 1

        # Update metrics
        self._update_pool_metrics()

        self.logger.debug(
            "Returned connection to pool", pool=self.name, connection_id=connection_id
        )

    async def close_connection(self, connection: Any) -> None:
        """Close and remove a connection from the pool.

        Args:
            connection: Connection to close
        """
        connection_id = self._find_connection_id(connection)
        if not connection_id:
            return

        await self._destroy_connection(connection_id)

    @asynccontextmanager
    async def get_connection_context(self) -> AsyncIterator[Any]:
        """Context manager for getting and returning connections.

        Yields:
            Connection object
        """
        connection = await self.get_connection()
        if not connection:
            raise RuntimeError(f"Failed to get connection from pool {self.name}")

        try:
            yield connection
        finally:
            await self.return_connection(connection)

    async def _management_loop(self) -> None:
        """Main pool management loop."""
        try:
            while self._running:
                await self._perform_maintenance()
                await asyncio.sleep(self.health_check_interval)
        except asyncio.CancelledError:
            self.logger.debug("Pool management loop cancelled", pool=self.name)
        except Exception as e:
            self.logger.error(
                "Error in pool management loop", pool=self.name, error=str(e)
            )
        finally:
            self.logger.debug("Pool management loop stopped", pool=self.name)

    async def _perform_maintenance(self) -> None:
        """Perform pool maintenance tasks."""
        try:
            # Health check connections
            await self._health_check_connections()

            # Clean up expired connections
            await self._cleanup_expired_connections()

            # Maintain minimum connections
            await self._maintain_min_connections()

            # Update metrics
            self._update_pool_metrics()

        except Exception as e:
            self.logger.error(
                "Error during pool maintenance", pool=self.name, error=str(e)
            )

    async def _initialize_min_connections(self) -> None:
        """Initialize minimum number of connections."""
        for _ in range(self.min_connections):
            await self._create_connection()

    async def _create_connection(self) -> Any | None:
        """Create a new connection.

        Returns:
            New connection object or None if creation failed
        """
        if not self._connection_factory:
            self.logger.error("No connection factory set", pool=self.name)
            return None

        try:
            # Create connection
            if asyncio.iscoroutinefunction(self._connection_factory):
                connection = await self._connection_factory()
            else:
                connection = self._connection_factory()

            if not connection:
                return None

            # Create pooled connection
            connection_id = f"{self.name}_{self._total_connections_created}"
            pooled_connection = PooledConnection(
                id=connection_id,
                connection=connection,
                state=ConnectionState.IDLE,
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
            )

            # Add to pool
            self._connections[connection_id] = pooled_connection
            self._idle_connections += 1
            self._total_connections_created += 1

            self.logger.debug(
                "Created new connection",
                pool=self.name,
                connection_id=connection_id,
                total_connections=len(self._connections),
            )

            return connection

        except Exception as e:
            self.logger.error("Error creating connection", pool=self.name, error=str(e))
            return None

    async def _destroy_connection(self, connection_id: str) -> None:
        """Destroy a connection.

        Args:
            connection_id: ID of connection to destroy
        """
        if connection_id not in self._connections:
            return

        pooled_connection = self._connections[connection_id]

        try:
            # Close connection if it has a close method
            if hasattr(pooled_connection.connection, "close"):
                if asyncio.iscoroutinefunction(pooled_connection.connection.close):
                    await pooled_connection.connection.close()
                else:
                    pooled_connection.connection.close()

            # Remove from pool
            del self._connections[connection_id]
            self._total_connections_destroyed += 1

            # Update pool state
            if pooled_connection.state == ConnectionState.ACTIVE:
                self._active_connections -= 1
            elif pooled_connection.state == ConnectionState.IDLE:
                self._idle_connections -= 1
            elif pooled_connection.state == ConnectionState.ERROR:
                self._error_connections -= 1

            self.logger.debug(
                "Destroyed connection", pool=self.name, connection_id=connection_id
            )

        except Exception as e:
            self.logger.error(
                "Error destroying connection",
                pool=self.name,
                connection_id=connection_id,
                error=str(e),
            )

    async def _get_idle_connection(self) -> Any | None:
        """Get an idle connection from the pool.

        Returns:
            Connection object or None if no idle connections
        """
        for pooled_connection in self._connections.values():
            if pooled_connection.state == ConnectionState.IDLE:
                # Validate connection if validator is set
                if self._connection_validator:
                    try:
                        if asyncio.iscoroutinefunction(self._connection_validator):
                            is_valid = await self._connection_validator(
                                pooled_connection.connection
                            )
                        else:
                            is_valid = self._connection_validator(
                                pooled_connection.connection
                            )

                        if not is_valid:
                            # Mark as error and continue
                            pooled_connection.mark_error("Connection validation failed")
                            continue
                    except Exception as e:
                        pooled_connection.mark_error(f"Validation error: {str(e)}")
                        continue

                # Mark as used
                pooled_connection.mark_used()

                # Update pool state
                self._idle_connections -= 1
                self._active_connections += 1

                return pooled_connection.connection

        return None

    async def _wait_for_connection(self) -> Any | None:
        """Wait for a connection to become available.

        Returns:
            Connection object or None if timeout
        """
        # Simple polling approach - could be enhanced with asyncio.Event
        timeout = self.connection_timeout
        start_time = time.time()

        while time.time() - start_time < timeout:
            connection = await self._get_idle_connection()
            if connection:
                return connection

            await asyncio.sleep(0.1)

        self.logger.warning(
            "Timeout waiting for connection", pool=self.name, timeout=timeout
        )
        return None

    async def _health_check_connections(self) -> None:
        """Perform health checks on all connections."""
        if not self._health_checker:
            return

        current_time = time.time()
        if current_time - self._last_health_check < self.health_check_interval:
            return

        self._last_health_check = current_time

        for connection_id, pooled_connection in list(self._connections.items()):
            try:
                if asyncio.iscoroutinefunction(self._health_checker):
                    is_healthy = await self._health_checker(
                        pooled_connection.connection
                    )
                else:
                    is_healthy = self._health_checker(pooled_connection.connection)

                if not is_healthy:
                    pooled_connection.mark_error("Health check failed")
                    self.logger.warning(
                        "Connection health check failed",
                        pool=self.name,
                        connection_id=connection_id,
                    )

            except Exception as e:
                pooled_connection.mark_error(f"Health check error: {str(e)}")
                self.logger.error(
                    "Error during health check",
                    pool=self.name,
                    connection_id=connection_id,
                    error=str(e),
                )

    async def _cleanup_expired_connections(self) -> None:
        """Clean up expired connections."""
        current_time = datetime.utcnow()

        for connection_id, pooled_connection in list(self._connections.items()):
            if (
                pooled_connection.state == ConnectionState.IDLE
                and pooled_connection.is_expired(self.max_idle_time)
            ):

                self.logger.debug(
                    "Cleaning up expired connection",
                    pool=self.name,
                    connection_id=connection_id,
                    idle_time=(
                        current_time - pooled_connection.last_used
                    ).total_seconds(),
                )

                await self._destroy_connection(connection_id)

    async def _maintain_min_connections(self) -> None:
        """Maintain minimum number of connections."""
        while len(self._connections) < self.min_connections:
            await self._create_connection()

    async def _close_all_connections(self) -> None:
        """Close all connections in the pool."""
        for connection_id in list(self._connections.keys()):
            await self._destroy_connection(connection_id)

    def _find_connection_id(self, connection: Any) -> str | None:
        """Find the ID of a connection in the pool.

        Args:
            connection: Connection object to find

        Returns:
            Connection ID or None if not found
        """
        for connection_id, pooled_connection in self._connections.items():
            if pooled_connection.connection is connection:
                return connection_id
        return None

    def _update_pool_metrics(self) -> None:
        """Update pool metrics."""
        self.metrics_collector.collect_component_metrics(
            f"{self.name}_pool",
            {
                "total_connections": len(self._connections),
                "active_connections": self._active_connections,
                "idle_connections": self._idle_connections,
                "error_connections": self._error_connections,
                "total_created": self._total_connections_created,
                "total_destroyed": self._total_connections_destroyed,
            },
        )

    def get_pool_stats(self) -> dict[str, Any]:
        """Get pool statistics.

        Returns:
            Dictionary with pool statistics
        """
        return {
            "name": self.name,
            "running": self._running,
            "max_connections": self.max_connections,
            "min_connections": self.min_connections,
            "total_connections": len(self._connections),
            "active_connections": self._active_connections,
            "idle_connections": self._idle_connections,
            "error_connections": self._error_connections,
            "total_created": self._total_connections_created,
            "total_destroyed": self._total_connections_destroyed,
            "utilization_percent": (
                self._active_connections / max(len(self._connections), 1)
            )
            * 100,
        }

    def get_connection_details(self) -> list[dict[str, Any]]:
        """Get detailed information about all connections.

        Returns:
            List of connection details
        """
        details = []
        for connection_id, pooled_connection in self._connections.items():
            details.append(
                {
                    "id": connection_id,
                    "state": pooled_connection.state.value,
                    "created_at": pooled_connection.created_at.isoformat(),
                    "last_used": pooled_connection.last_used.isoformat(),
                    "use_count": pooled_connection.use_count,
                    "error_count": pooled_connection.error_count,
                    "last_error": pooled_connection.last_error,
                    "is_healthy": pooled_connection.is_healthy(),
                    "is_expired": pooled_connection.is_expired(self.max_idle_time),
                }
            )
        return details
