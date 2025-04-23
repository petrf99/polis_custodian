-- Utterances table
CREATE TABLE IF NOT EXISTS sage_questions_cache (
    question_id UUID PRIMARY KEY,
    speaker TEXT,
    question TEXT,
    context TEXT,
    question_dttm TIMESTAMP,
    created_at TIMESTAMP DEFAULT now(),
    lang TEXT,
    answered BOOLEAN DEFAULT false,
    context_score FLOAT,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS sage_feedback (
    question_id UUID PRIMARY KEY,
    rate INTEGER,
    created_at TIMESTAMP DEFAULT now()
)