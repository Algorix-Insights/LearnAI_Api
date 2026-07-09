CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS profile_image_path TEXT,
ADD COLUMN IF NOT EXISTS profile_image_mime_type TEXT,
ADD COLUMN IF NOT EXISTS profile_image_size_bytes BIGINT CHECK (
    profile_image_size_bytes IS NULL OR profile_image_size_bytes >= 0
);

INSERT INTO storage.buckets (id, name, public)
VALUES
    ('documents', 'documents', FALSE),
    ('profile', 'profile', FALSE)
ON CONFLICT (id) DO NOTHING;

UPDATE members_rooms
SET role = 'user'
WHERE role = 'member';

ALTER TABLE members_rooms
ALTER COLUMN role SET DEFAULT 'user';

DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    SELECT conname
    INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'members_rooms'::regclass
      AND contype = 'c'
      AND pg_get_constraintdef(oid) ILIKE '%role%'
    LIMIT 1;

    IF constraint_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE members_rooms DROP CONSTRAINT %I', constraint_name);
    END IF;
END $$;

ALTER TABLE members_rooms
ADD CONSTRAINT members_rooms_role_check
CHECK (role IN ('user', 'admin'));

CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding VECTOR(1536),
    match_notebook_id UUID,
    match_count INT DEFAULT 6
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    notebook_id UUID,
    content TEXT,
    model TEXT,
    token_count INT,
    document_name TEXT,
    storage_path TEXT,
    similarity DOUBLE PRECISION
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        dc.chunk_id,
        dc.document_id,
        d.notebook_id,
        dc.content,
        dc.model,
        dc.token_count,
        d.name AS document_name,
        d.storage_path,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    JOIN documents d ON d.document_id = dc.document_id
    WHERE d.notebook_id = match_notebook_id
      AND d.status = 'active'
      AND d.processing_status = 'completed'
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
$$;

CREATE INDEX IF NOT EXISTS ai_conversations_notebook_id_updated_at_idx
ON ai_conversations (notebook_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS messages_conversation_id_order_idx
ON messages (conversation_id, order_message);
