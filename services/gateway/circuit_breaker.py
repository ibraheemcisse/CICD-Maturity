"""
Circuit breaker implementation for protecting downstream services.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Failure threshold exceeded, requests fail fast
- HALF_OPEN: Testing if service recovered
"""
import time
from dataclasses import dataclass
from enum import Enum


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5  # Failures before opening
    timeout: int = 60  # Seconds to wait before half-open
    success_threshold: int = 2  # Successes in half-open before closing


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.
    
    Usage:
        breaker = CircuitBreaker(name="worker_service")
        
        if breaker.allow_request():
            try:
                result = await call_service()
                breaker.record_success()
            except Exception:
                breaker.record_failure()
        else:
            # Circuit is open, fail fast
            raise ServiceUnavailableError()
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig | None = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
    
    def allow_request(self) -> bool:
        """
        Check if request should be allowed through.
        
        Returns:
            True if request allowed, False if circuit open
        """
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
            return False
        
        # HALF_OPEN state - allow limited requests
        return True
    
    def record_success(self):
        """Record successful request."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._close_circuit()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            # Failure in half-open, reopen circuit
            self._open_circuit()
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self._open_circuit()
    
    def _open_circuit(self):
        """Transition to OPEN state."""
        self.state = CircuitState.OPEN
        self.last_failure_time = time.time()
    
    def _close_circuit(self):
        """Transition to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.config.timeout
    
    def get_state(self) -> dict:
        """Get current circuit breaker state for monitoring."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "timeout": self.config.timeout,
                "success_threshold": self.config.success_threshold
            }
        }
