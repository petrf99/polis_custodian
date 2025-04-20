-- Тopics table
CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    color TEXT,
    metadata JSONB
);

-- Dialogs table
CREATE TABLE IF NOT EXISTS dialogs (
    id UUID PRIMARY KEY,
    title TEXT,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    topic_id INTEGER,
    tags TEXT[],
    source TEXT,
    participants TEXT[],
    summary TEXT,
    metadata JSONB
);

-- Utterances table
CREATE TABLE IF NOT EXISTS utterances (
    id UUID PRIMARY KEY,
    dialog_id UUID REFERENCES dialogs(id),
    speaker TEXT,
    content TEXT,
    start_time DOUBLE PRECISION,
    end_time DOUBLE PRECISION,
    segment_number INTEGER,
    created_at TIMESTAMP DEFAULT now(),
    metadata JSONB
);