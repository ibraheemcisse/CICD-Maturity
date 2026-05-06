"""
Redis queue client for job distribution.
"""
from typing import Optional

import redis.asyncio as aioredis  # type: ignore[import-untyped]

from .config import Config
from .logger import setup_logger
from .models import Job

logger = setup_logger("queue")


class QueueClient:
    """Redis-based job queue."""
    
    QUEUE_KEY = "jobs:pending"
    PROCESSING_KEY = "jobs:processing"
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
    
    async def connect(self):
        """Establish Redis connection."""
        self.redis = await aioredis.from_url(
            Config.get_redis_url(),
            encoding="utf-8",
            decode_responses=True
        )
        logger.info(f"Connected to Redis at {Config.REDIS_HOST}:{Config.REDIS_PORT}")
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
    
    async def enqueue(self, job: Job) -> bool:
        try:
            assert self.redis is not None
            job_data = job.model_dump_json()
            await self.redis.rpush(self.QUEUE_KEY, job_data)
            logger.info(f"Enqueued job {job.job_id} (type: {job.job_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue job {job.job_id}: {e}")
            return False

    async def dequeue(self, timeout: int = 5) -> Optional[Job]:
        try:
            assert self.redis is not None
            result = await self.redis.blpop(self.QUEUE_KEY, timeout=timeout)
            if result:
                _, job_data = result
                job = Job.model_validate_json(job_data)
                logger.info(f"Dequeued job {job.job_id}")
                return job
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue job: {e}")
            return None

    async def get_queue_depth(self) -> int:
        try:
            assert self.redis is not None
            depth = await self.redis.llen(self.QUEUE_KEY)
            return depth
        except Exception as e:
            logger.error(f"Failed to get queue depth: {e}")
            return 0
