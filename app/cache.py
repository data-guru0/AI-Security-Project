import json
import numpy as np
import redis.asyncio as aioredis
from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("all-MiniLM-L6-v2")
CACHE_TTL = 3600
SIMILARITY_THRESHOLD = 0.92
CACHE_PREFIX = "semantic:"
EMB_PREFIX = "emb:"


def _cosine_similarity(a: list, b: list) -> float:
    va, vb = np.array(a), np.array(b)
    return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb)))


def _embed(text: str) -> list:
    return _model.encode(text).tolist()


async def cache_get(redis: aioredis.Redis, query: str) -> str | None:
    query_emb = _embed(query)
    async for key in redis.scan_iter(f"{EMB_PREFIX}*"):
        stored_emb = json.loads(await redis.get(key))
        if _cosine_similarity(query_emb, stored_emb) >= SIMILARITY_THRESHOLD:
            cache_key = key.replace(EMB_PREFIX, CACHE_PREFIX)
            return await redis.get(cache_key)
    return None


async def cache_set(redis: aioredis.Redis, query: str, result: str) -> None:
    key_suffix = abs(hash(query))
    await redis.setex(f"{CACHE_PREFIX}{key_suffix}", CACHE_TTL, result)
    await redis.setex(f"{EMB_PREFIX}{key_suffix}", CACHE_TTL, json.dumps(_embed(query)))
