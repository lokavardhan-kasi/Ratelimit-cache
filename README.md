# Rate-Limited Caching API Gateway

A lightweight API gateway built with **FastAPI** that combines **token-bucket rate limiting** and **LRU response caching** to protect backend services from overload and cut latency on repeated requests.

## Features
- Per-client token-bucket rate limiting (configurable burst capacity & refill rate), thread-safe for concurrent requests
- LRU cache for GET responses — O(1) get/put via a doubly linked list + hash map
- Custom ASGI middleware applies rate limiting and caching transparently to every route
- `/stats` endpoint exposing live cache hit/miss ratio and rate-limit rejection counts
- `/health` endpoint for liveness checks

## How it works
1. A request arrives — the middleware extracts a client id (header or IP).
2. The token bucket checks if that client has a token available; if not, it returns `429`.
3. For GET requests, the middleware checks the LRU cache using a method + path + query key.
   - **Cache hit** → returns the cached JSON instantly (`X-Cache: HIT`)
   - **Cache miss** → forwards to the real handler, then caches the JSON result (`X-Cache: MISS`)
4. In-memory stats track total requests, hits, misses, and rejections.

## Tech stack
Python · FastAPI · Starlette ASGI middleware

## Run locally
```bash
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

## Try it
```bash
curl http://localhost:8000/items/1
curl http://localhost:8000/items/1   # instant — served from cache
curl http://localhost:8000/stats
```

## Future improvements
- Redis-backed cache/limiter for multi-instance deployments
- TTL-based cache expiration
- Per-route rate limit configuration
- Unit tests with pytest