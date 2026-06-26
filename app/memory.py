import json
import asyncio
from datetime import datetime
import asyncpg
import redis.asyncio as aioredis
from sentence_transformers import SentenceTransformer
from app.config import Config

SESSION_TTL = 1800
MAX_MESSAGES = 5
_model = SentenceTransformer("all-MiniLM-L6-v2")


async def session_add(redis: aioredis.Redis, session_id: str, role: str, content: str) -> None:
    key = f"session:{session_id}"
    await redis.rpush(key, json.dumps({"role": role, "content": content}))
    await redis.ltrim(key, -MAX_MESSAGES, -1)
    await redis.expire(key, SESSION_TTL)


async def session_get(redis: aioredis.Redis, session_id: str) -> list[dict]:
    messages = await redis.lrange(f"session:{session_id}", 0, -1)
    return [json.loads(m) for m in messages]


async def _pg_connect(config: Config):
    return await asyncpg.connect(config.database_url)


async def db_migrate(config: Config) -> None:
    conn = await _pg_connect(config)
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id         TEXT PRIMARY KEY,
                topic      TEXT NOT NULL,
                report     TEXT NOT NULL,
                embedding  vector(384),
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS reports_embedding_idx
            ON reports USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS reports_topic_idx ON reports (topic)")
        await conn.execute("CREATE INDEX IF NOT EXISTS reports_created_idx ON reports (created_at DESC)")
    finally:
        await conn.close()


async def ltm_store(config: Config, topic: str, report: str, report_id: str) -> None:
    embedding = await asyncio.to_thread(lambda: _model.encode(topic).tolist())
    conn = await _pg_connect(config)
    try:
        await conn.execute(
            "INSERT INTO reports (id, topic, report, embedding, created_at) VALUES ($1, $2, $3, $4::vector, $5)",
            report_id, topic, report, str(embedding), datetime.utcnow(),
        )
    finally:
        await conn.close()


async def ltm_search(config: Config, topic: str, days: int = 7) -> dict | None:
    embedding = await asyncio.to_thread(lambda: _model.encode(topic).tolist())
    conn = await _pg_connect(config)
    try:
        row = await conn.fetchrow(
            """
            SELECT id, topic, report, created_at,
                   1 - (embedding <=> $1::vector) AS similarity
            FROM reports
            WHERE created_at > NOW() - ($2 || ' days')::INTERVAL
              AND 1 - (embedding <=> $1::vector) > 0.88
            ORDER BY similarity DESC LIMIT 1
            """,
            str(embedding), str(days),
        )
        return dict(row) if row else None
    finally:
        await conn.close()


async def ltm_diff(config: Config, topic: str) -> str | None:
    conn = await _pg_connect(config)
    try:
        rows = await conn.fetch(
            "SELECT report, created_at FROM reports WHERE topic = $1 ORDER BY created_at DESC LIMIT 2",
            topic,
        )
        if len(rows) < 2:
            return None
        old_sentences = set(rows[1]["report"].split(". "))
        new_sentences = set(rows[0]["report"].split(". "))
        added = [f"[NEW] {s}" for s in list(new_sentences - old_sentences)[:5]]
        removed = [f"[REMOVED] {s}" for s in list(old_sentences - new_sentences)[:5]]
        return "\n".join(added + removed) or "No significant changes detected."
    finally:
        await conn.close()
