import json
import time
import random
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from lru_cache import LRUCache
from rate_limiter import TokenBucket

app = FastAPI()

cache = LRUCache(capacity=50)
limiter = TokenBucket(capacity=5, refill_rate=1.0)

stats = {
    "total_requests": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "rate_limited": 0,
}


def get_client_id(request: Request) -> str:
    return request.headers.get("x-client-id") or request.client.host


def get_cache_key(request: Request) -> str:
    return f"{request.method}:{request.url.path}?{request.url.query}"


class RateLimitCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        stats["total_requests"] += 1
        client_id = get_client_id(request)

        if not limiter.allow_request(client_id):
            stats["rate_limited"] += 1
            return JSONResponse(status_code=429, content={"error": "rate_limit_exceeded"})

        key = get_cache_key(request)

        if request.method == "GET":
            cached = cache.get(key)
            if cached is not None:
                stats["cache_hits"] += 1
                response = JSONResponse(content=cached)
                response.headers["X-Cache"] = "HIT"
                return response

        response = await call_next(request)

        # On a GET miss, actually store the response in the cache
        if request.method == "GET" and response.status_code == 200:
            stats["cache_misses"] += 1

            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            try:
                data = json.loads(body)
                cache.put(key, data)
            except (json.JSONDecodeError, TypeError):
                pass

            new_response = Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
            new_response.headers["X-Cache"] = "MISS"
            return new_response

        return response


app.add_middleware(RateLimitCacheMiddleware)


@app.get("/items/{item_id}")
def get_item(item_id: int):
    time.sleep(0.3)  # simulate slow DB call
    return {"item_id": item_id, "value": random.randint(1, 999999)}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats")
def get_stats():
    return stats