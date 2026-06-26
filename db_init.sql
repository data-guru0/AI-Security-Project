CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS reports (
    id          TEXT PRIMARY KEY,
    topic       TEXT NOT NULL,
    report      TEXT NOT NULL,
    embedding   vector(384),
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS reports_embedding_idx
    ON reports USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS reports_topic_idx ON reports (topic);
CREATE INDEX IF NOT EXISTS reports_created_idx ON reports (created_at DESC);
