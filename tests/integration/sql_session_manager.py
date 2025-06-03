from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

import sqlalchemy as sa
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConnectionDetails:
    connection_string: str
    # BDIRKS extract this from connection string
    dialect: str


@dataclass(frozen=True)
class PoolConfig:
    pool_size: int
    max_overflow: int
    pool_recycle: int
    pool_timeout: int
    pool_pre_ping: bool


class SessionSQLEngineManager:
    POOL_CONFIG = PoolConfig(
        pool_size=2,
        max_overflow=3,
        pool_recycle=5400,  # 1.5 hours
        pool_timeout=30,  # 30 seconds
        pool_pre_ping=True,
    )

    def __init__(self):
        self._engine_cache: dict[ConnectionDetails, sa.engine.Engine] = {}

    def get_engine(
        self,
        connection_details: ConnectionDetails,
    ) -> sa.engine.Engine:
        cache_key = connection_details
        if cache_key not in self._engine_cache:
            logger.info(f"Cache miss for engine: {cache_key}. Creating new engine.")
            engine_kwargs = asdict(self.POOL_CONFIG)
            logger.info(
                f"Creating engine for {connection_details.dialect} with settings: {engine_kwargs}"
            )
            self._engine_cache[cache_key] = sa.create_engine(
                connection_details.connection_string, **engine_kwargs
            )
        else:
            logger.info(f"Cache hit for engine: {cache_key}")
        return self._engine_cache[cache_key]

    def dispose_all_engines(self):
        logger.info("Disposing all cached SQLAlchemy engines.")
        for key, engine in self._engine_cache.items():
            logger.info(f"Disposing engine: {key}")
            try:
                engine.dispose()
            except Exception:
                logger.exception(f"Error disposing engine '{key}'")
        self._engine_cache.clear()

    def get_all_pool_statistics(
        self,
    ) -> dict[ConnectionDetails, dict[str, Any]]:
        stats: dict[ConnectionDetails, dict[str, Any]] = {}
        for key, engine in self._engine_cache.items():
            try:
                pool = engine.pool
                if isinstance(pool, QueuePool):
                    stats[key] = {
                        "size": pool.size(),
                        "checked_in": pool.checkedin(),
                        "overflow": pool.overflow(),
                        "checked_out": pool.checkedout(),
                    }
                else:
                    logger.warning(
                        f"Pool for engine {key} is not a QueuePool. It is a {type(pool)}."
                    )
                    stats[key] = {
                        "type": f"{type(pool)}",
                        "status": f"{pool.status()}",
                    }
            except Exception as e:
                logger.exception(f"Error getting pool status for engine '{key}'")
                stats[key] = {"error": str(e)}
        return stats
