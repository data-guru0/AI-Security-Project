import json
import uuid
import redis.asyncio as aioredis

STREAM_KEY = "research:jobs"
RESULT_TTL = 3600
CONSUMER_GROUP = "workers"
CONSUMER_NAME = "worker-1"


async def push_job(redis: aioredis.Redis, topic: str, session_id: str, output_format: str) -> str:
    job_id = str(uuid.uuid4())
    await redis.xadd(STREAM_KEY, {
        "job_id": job_id,
        "topic": topic,
        "session_id": session_id,
        "output_format": output_format,
    })
    return job_id


async def get_result(redis: aioredis.Redis, job_id: str) -> dict | None:
    data = await redis.get(f"result:{job_id}")
    return json.loads(data) if data else None


async def set_result(redis: aioredis.Redis, job_id: str, result: dict) -> None:
    await redis.setex(f"result:{job_id}", RESULT_TTL, json.dumps(result))


async def ensure_group(redis: aioredis.Redis) -> None:
    try:
        await redis.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
    except Exception:
        pass


async def consume_jobs(redis: aioredis.Redis) -> list[dict]:
    messages = await redis.xreadgroup(
        CONSUMER_GROUP, CONSUMER_NAME, {STREAM_KEY: ">"}, count=1, block=5000
    )
    if not messages:
        return []
    jobs = []
    for _, entries in messages:
        for msg_id, data in entries:
            jobs.append({"msg_id": msg_id, "data": data})
    return jobs


async def ack_job(redis: aioredis.Redis, msg_id: str) -> None:
    await redis.xack(STREAM_KEY, CONSUMER_GROUP, msg_id)
