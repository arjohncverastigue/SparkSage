import time
import collections

class RateLimiter:
    def __init__(self, capacity: int, refill_rate: int):
        """
        Initializes a token bucket rate limiter.
        :param capacity: The maximum number of tokens the bucket can hold.
        :param refill_rate: How many tokens are added to the bucket per minute.
        """
        self.capacity = capacity
        self.refill_rate = refill_rate / 60.0 # tokens per second
        self.tokens = capacity
        self.last_refill_time = time.time()

    def _refill(self):
        now = time.time()
        time_passed = now - self.last_refill_time
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_refill_time = now

    def check_and_consume(self) -> bool:
        """
        Checks if a request can be processed and consumes a token if so.
        :return: True if the request is allowed, False otherwise.
        """
        self._refill()
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

class RateLimiterManager:
    def __init__(self):
        self.user_limiters = collections.defaultdict(lambda: None) # {user_id: RateLimiter}
        self.guild_limiters = collections.defaultdict(lambda: None) # {guild_id: RateLimiter}
        self.user_capacity = 0
        self.user_refill_rate = 0
        self.guild_capacity = 0
        self.guild_refill_rate = 0
        self.enabled = False

    def configure(self, user_limit: int, guild_limit: int, enabled: bool):
        self.user_capacity = user_limit
        self.user_refill_rate = user_limit
        self.guild_capacity = guild_limit
        self.guild_refill_rate = guild_limit
        self.enabled = enabled

    def get_user_limiter(self, user_id: str) -> RateLimiter:
        if self.user_limiters[user_id] is None:
            self.user_limiters[user_id] = RateLimiter(self.user_capacity, self.user_refill_rate)
        return self.user_limiters[user_id]

    def get_guild_limiter(self, guild_id: str) -> RateLimiter:
        if self.guild_limiters[guild_id] is None:
            self.guild_limiters[guild_id] = RateLimiter(self.guild_capacity, self.guild_refill_rate)
        return self.guild_limiters[guild_id]

    def check_and_consume(self, user_id: str | None, guild_id: str | None) -> tuple[bool, str]:
        """
        Checks rate limits for a user and/or guild and consumes tokens.
        :return: Tuple (allowed: bool, reason: str).
        """
        if not self.enabled:
            return True, "Rate limiting is disabled."

        if guild_id:
            guild_limiter = self.get_guild_limiter(guild_id)
            if not guild_limiter.check_and_consume():
                return False, f"Guild rate limit exceeded. Please wait a moment."

        if user_id:
            user_limiter = self.get_user_limiter(user_id)
            if not user_limiter.check_and_consume():
                # If guild limit passed, but user limit failed, refill guild token
                if guild_id:
                    guild_limiter._refill() # This adds back the token consumed by guild_limiter
                    guild_limiter.tokens = min(guild_limiter.capacity, guild_limiter.tokens + 1) # Add back one token
                return False, f"User rate limit exceeded. Please wait a moment."
        
        return True, "Allowed."

# Global instance of the RateLimiterManager
rate_limiter = RateLimiterManager()
