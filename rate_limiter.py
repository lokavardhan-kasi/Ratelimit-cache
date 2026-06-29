import time


class TokenBucket:
    def __init__(self, capacity: int = 5, refill_rate: float = 1.0):
        """
        capacity: max tokens (max burst requests allowed)
        refill_rate: tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets = {}  # client_id -> {"tokens": float, "last_check": float}

    def _refill(self, bucket):
        now = time.time()
        elapsed = now - bucket["last_check"]
        bucket["tokens"] = min(
            self.capacity,
            bucket["tokens"] + elapsed * self.refill_rate
        )
        bucket["last_check"] = now

    def allow_request(self, client_id: str) -> bool:
        if client_id not in self.buckets:
            self.buckets[client_id] = {
                "tokens": self.capacity,
                "last_check": time.time()
            }

        bucket = self.buckets[client_id]
        self._refill(bucket)

        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True
        return False