"""
Rate limiting middleware for LumiLens API.

Implements rate limiting to prevent abuse and ensure fair usage
of the API resources across all users.
"""

import time
import logging
from typing import Dict, Any
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict, deque

from api.config import get_settings
from api.core.exceptions import RateLimitException

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using token bucket algorithm.
    
    Tracks requests per IP address and applies rate limits based on
    configuration settings with proper cleanup of old entries.
    """
    
    def __init__(self, app):
        """Initialize rate limiting middleware."""
        super().__init__(app)
        self.settings = get_settings()
        
        # Rate limiting storage: IP -> request timestamps
        self._request_history: Dict[str, deque] = defaultdict(lambda: deque())
        self._last_cleanup = time.time()
        
        logger.info("🛡️  Rate limiting middleware initialized")
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request with rate limiting check.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response: HTTP response
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        # Skip rate limiting for health checks and documentation
        if request.url.path in ["/health", "/api/docs", "/api/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        if not self._check_rate_limit(client_ip):
            logger.warning("🚫 Rate limit exceeded for IP: %s", client_ip)
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": str(self.settings.RATE_LIMIT_WINDOW)}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self._get_remaining_requests(client_ip)
        reset_time = int(time.time()) + self.settings.RATE_LIMIT_WINDOW
        
        response.headers["X-RateLimit-Limit"] = str(self.settings.RATE_LIMIT_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.
        
        Args:
            request: HTTP request
            
        Returns:
            str: Client IP address
        """
        # Check for forwarded headers (from load balancers/proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Check real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """
        Check if client has exceeded rate limit.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            bool: True if within rate limit, False if exceeded
        """
        current_time = time.time()
        
        # Cleanup old entries periodically
        self._cleanup_old_entries(current_time)
        
        # Get request history for this IP
        ip_history = self._request_history[client_ip]
        
        # Remove old requests outside the window
        window_start = current_time - self.settings.RATE_LIMIT_WINDOW
        while ip_history and ip_history[0] < window_start:
            ip_history.popleft()
        
        # Check if limit exceeded
        if len(ip_history) >= self.settings.RATE_LIMIT_REQUESTS:
            return False
        
        # Record this request
        ip_history.append(current_time)
        
        return True
    
    def _get_remaining_requests(self, client_ip: str) -> int:
        """
        Get remaining requests for client IP.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            int: Number of remaining requests
        """
        ip_history = self._request_history[client_ip]
        current_requests = len(ip_history)
        
        return max(0, self.settings.RATE_LIMIT_REQUESTS - current_requests)
    
    def _cleanup_old_entries(self, current_time: float) -> None:
        """
        Cleanup old rate limiting entries to prevent memory leaks.
        
        Args:
            current_time: Current timestamp
        """
        # Only cleanup every 5 minutes
        if current_time - self._last_cleanup < 300:
            return
        
        self._last_cleanup = current_time
        window_start = current_time - self.settings.RATE_LIMIT_WINDOW
        
        # Remove completely old IP entries
        ips_to_remove = []
        for ip, history in self._request_history.items():
            # Remove old requests
            while history and history[0] < window_start:
                history.popleft()
            
            # If no recent requests, mark IP for removal
            if not history:
                ips_to_remove.append(ip)
        
        # Remove inactive IPs
        for ip in ips_to_remove:
            del self._request_history[ip]
        
        logger.debug("🧹 Rate limit cleanup: removed %d inactive IPs", len(ips_to_remove))
