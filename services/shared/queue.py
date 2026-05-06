"""
Redis queue client for job distribution.
"""
import json
from typing import Optional

import redis.asyncio as aioredis  # type: ignore[import-untyped]

from .logger import setup_logger
from .models import Job

logger = setup_logger("queue")


class QueueClient:
    """Async Redis queue client for job distribution."""
    
    QUEUE_KEY = "jobs:queue"
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis: Optional[aioredis.Redis] = None
    
    async def connect(self):
        """Connect to Redis."""
        self.redis = await aioredis.from_url(
            f"redis://{self.redis_host}:{self.redis_port}",
            encoding="utf-8",
            decode_responses=True
        )
        logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
    
    async def enqueue(self, job: Job) -> bool:
        """
        Add job to queue.
        
        Args:
            job: Job to enqueue
            
        Returns:
            True if successful
        """
        try:
            if self.redis:
                await self.redis.rpush(self.QUEUE_KEY, job.model_dump_json())  # type: ignore[union-attr]
                logger.debug(f"Enqueued job {job.job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to enqueue job: {e}")
            return False
    
    async def dequeue(self, timeout: int = 5) -> Optional[Job]:
        """
        Remove and return job from queue.
        
        Args:
            timeout: Block timeout in seconds
            
        Returns:
            Job if available, None otherwise
        """
        try:
            if self.redis:
                result = await self.redis.blpop(self.QUEUE_KEY, timeout=timeout)  # type: ignore[union-attr,arg-type]
                if result:
                    _, job_json = result
                    job_data = json.loads(job_json)
                    return Job(**job_data)
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue job: {e}")
            return None
    
    async def get_queue_depth(self) -> int:
        """Get current queue depth."""
        try:
            if self.redis:
                depth = await self.redis.llen(self.QUEUE_KEY)  # type: ignore[union-attr]
                return depth
            return 0
        except Exception as e:
            logger.error(f"Failed to get queue depth: {e}")
            return 0
