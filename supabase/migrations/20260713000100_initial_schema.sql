CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO health (status)
SELECT 'healthy'
WHERE NOT EXISTS (
    SELECT 1
    FROM health
    WHERE status = 'healthy'
);

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hash_password TEXT NOT NULL,
    streak INTEGER NOT NULL DEFAULT 0 CHECK (streak >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS notebooks (
    notebook_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    grade INTEGER NOT NULL DEFAULT 0 CHECK (grade >= 0),
    summary TEXT,
    is_dominated BOOLEAN NOT NULL DEFAULT FALSE,
    is_favorite BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'archived', 'deleted')),
    spent_time INTEGER NOT NULL DEFAULT 0 CHECK (spent_time >= 0),
    last_seen_at TIMESTAMPTZ,
    due_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rooms (
    room_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS study_members (
    member_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL
        REFERENCES users(user_id)
        ON DELETE CASCADE,
    nickname TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS members_rooms (
    member_id UUID NOT NULL
        REFERENCES study_members(member_id)
        ON DELETE CASCADE,
    room_id UUID NOT NULL
        REFERENCES rooms(room_id)
        ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'member'
        CHECK (role IN ('member', 'admin')),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (member_id, room_id)
);

CREATE TABLE IF NOT EXISTS personal_notebooks (
    notebook_id UUID PRIMARY KEY
        REFERENCES notebooks(notebook_id)
        ON DELETE CASCADE,
    user_id UUID NOT NULL
        REFERENCES users(user_id)
        ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS room_notebooks (
    notebook_id UUID PRIMARY KEY
        REFERENCES notebooks(notebook_id)
        ON DELETE CASCADE,
    room_id UUID NOT NULL
        REFERENCES rooms(room_id)
        ON DELETE CASCADE,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_room_notebook_creator_membership
        FOREIGN KEY (created_by, room_id)
        REFERENCES members_rooms(member_id, room_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS exams (
    exam_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id UUID NOT NULL
        REFERENCES notebooks(notebook_id)
        ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'archived', 'deleted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS questions (
    question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(20) NOT NULL DEFAULT 'multiple_choice'
        CHECK (type IN ('multiple_choice', 'true_false', 'open')),
    statement TEXT NOT NULL,
    expected_answer TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_expected_answer_by_type CHECK (
        (type = 'open' AND expected_answer IS NOT NULL)
        OR
        (type IN ('multiple_choice', 'true_false') AND expected_answer IS NULL)
    )
);

CREATE TABLE IF NOT EXISTS exam_questions (
    exam_id UUID NOT NULL
        REFERENCES exams(exam_id)
        ON DELETE CASCADE,
    question_id UUID NOT NULL
        REFERENCES questions(question_id)
        ON DELETE CASCADE,
    question_order INTEGER NOT NULL CHECK (question_order > 0),
    points NUMERIC(7,2) NOT NULL DEFAULT 1 CHECK (points >= 0),
    PRIMARY KEY (exam_id, question_id),
    UNIQUE (exam_id, question_order)
);

CREATE TABLE IF NOT EXISTS questions_options (
    option_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL
        REFERENCES questions(question_id)
        ON DELETE CASCADE,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE,
    option_order INTEGER NOT NULL CHECK (option_order > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (question_id, option_order),
    UNIQUE (option_id, question_id)
);

CREATE TABLE IF NOT EXISTS attempts (
    attempt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id UUID NOT NULL
        REFERENCES exams(exam_id)
        ON DELETE CASCADE,
    user_id UUID NOT NULL
        REFERENCES users(user_id)
        ON DELETE CASCADE,
    score NUMERIC(7,2) NOT NULL DEFAULT 0 CHECK (score >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress'
        CHECK (status IN ('in_progress', 'completed', 'failed', 'not_started')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    spent_time INTEGER NOT NULL DEFAULT 0 CHECK (spent_time >= 0),
    CHECK (completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at)
);

CREATE TABLE IF NOT EXISTS user_answers (
    answer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attempt_id UUID NOT NULL
        REFERENCES attempts(attempt_id)
        ON DELETE CASCADE,
    question_id UUID NOT NULL
        REFERENCES questions(question_id)
        ON DELETE RESTRICT,
    selected_option_id UUID,
    answer_text TEXT,
    is_correct BOOLEAN,
    points_awarded NUMERIC(7,2) NOT NULL DEFAULT 0 CHECK (points_awarded >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (attempt_id, question_id),
    CONSTRAINT chk_user_answer_value CHECK (
        (selected_option_id IS NOT NULL AND answer_text IS NULL)
        OR
        (selected_option_id IS NULL AND answer_text IS NOT NULL)
    ),
    CONSTRAINT fk_selected_option_question
        FOREIGN KEY (selected_option_id, question_id)
        REFERENCES questions_options(option_id, question_id)
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS flashcards (
    flashcard_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id UUID NOT NULL
        REFERENCES notebooks(notebook_id)
        ON DELETE CASCADE,
    question_id UUID UNIQUE NOT NULL
        REFERENCES questions(question_id)
        ON DELETE CASCADE,
    spent_time INTEGER NOT NULL DEFAULT 0 CHECK (spent_time >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id UUID NOT NULL
        REFERENCES notebooks(notebook_id)
        ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    source_type VARCHAR(20) NOT NULL
        CHECK (source_type IN ('note', 'pdf', 'markdown', 'txt', 'document')),
    storage_path TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'archived', 'deleted')),
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    mime_type TEXT,
    content_text TEXT,
    content_hash TEXT NOT NULL,
    size_bytes BIGINT NOT NULL DEFAULT 0 CHECK (size_bytes >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (notebook_id, content_hash),
    CONSTRAINT chk_document_source CHECK (
        (source_type = 'note' AND content_text IS NOT NULL)
        OR
        (source_type <> 'note' AND storage_path IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL
        REFERENCES documents(document_id)
        ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    model TEXT NOT NULL,
    token_count INTEGER CHECK (token_count IS NULL OR token_count >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx
ON document_chunks
USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS ai_conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id UUID NOT NULL
        REFERENCES notebooks(notebook_id)
        ON DELETE CASCADE,
    name TEXT NOT NULL,
    summary TEXT,
    spent_time INTEGER NOT NULL DEFAULT 0 CHECK (spent_time >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'archived', 'deleted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL
        REFERENCES ai_conversations(conversation_id)
        ON DELETE CASCADE,
    sent_by_user_id UUID
        REFERENCES users(user_id)
        ON DELETE RESTRICT,
    role VARCHAR(20) NOT NULL DEFAULT 'user'
        CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    order_message INTEGER NOT NULL CHECK (order_message > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (conversation_id, order_message),
    CONSTRAINT chk_message_sender CHECK (
        (role = 'user' AND sent_by_user_id IS NOT NULL)
        OR
        (role = 'assistant' AND sent_by_user_id IS NULL)
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS users_status_created_at_idx
ON users (status, created_at DESC);

CREATE INDEX IF NOT EXISTS notebooks_status_updated_at_idx
ON notebooks (status, updated_at DESC);

CREATE INDEX IF NOT EXISTS notebooks_due_date_idx
ON notebooks (due_date)
WHERE due_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS rooms_created_at_idx
ON rooms (created_at DESC);

CREATE INDEX IF NOT EXISTS members_rooms_room_id_idx
ON members_rooms (room_id);

CREATE INDEX IF NOT EXISTS personal_notebooks_user_id_idx
ON personal_notebooks (user_id);

CREATE INDEX IF NOT EXISTS room_notebooks_room_id_idx
ON room_notebooks (room_id);

CREATE INDEX IF NOT EXISTS room_notebooks_created_by_room_id_idx
ON room_notebooks (created_by, room_id);

CREATE INDEX IF NOT EXISTS exams_notebook_id_status_idx
ON exams (notebook_id, status);

CREATE INDEX IF NOT EXISTS exam_questions_question_id_idx
ON exam_questions (question_id);

CREATE INDEX IF NOT EXISTS attempts_exam_id_status_idx
ON attempts (exam_id, status);

CREATE INDEX IF NOT EXISTS attempts_user_id_created_at_idx
ON attempts (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS user_answers_question_id_idx
ON user_answers (question_id);

CREATE INDEX IF NOT EXISTS user_answers_selected_option_question_idx
ON user_answers (selected_option_id, question_id)
WHERE selected_option_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS flashcards_notebook_id_idx
ON flashcards (notebook_id);

CREATE INDEX IF NOT EXISTS documents_notebook_id_status_idx
ON documents (notebook_id, status);

CREATE INDEX IF NOT EXISTS documents_processing_status_created_at_idx
ON documents (processing_status, created_at);

CREATE INDEX IF NOT EXISTS ai_conversations_notebook_status_updated_at_idx
ON ai_conversations (notebook_id, status, updated_at DESC);

CREATE INDEX IF NOT EXISTS messages_sent_by_user_id_idx
ON messages (sent_by_user_id)
WHERE sent_by_user_id IS NOT NULL;

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_notebooks_updated_at ON notebooks;
CREATE TRIGGER trg_notebooks_updated_at
BEFORE UPDATE ON notebooks
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_rooms_updated_at ON rooms;
CREATE TRIGGER trg_rooms_updated_at
BEFORE UPDATE ON rooms
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_study_members_updated_at ON study_members;
CREATE TRIGGER trg_study_members_updated_at
BEFORE UPDATE ON study_members
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_personal_notebooks_updated_at ON personal_notebooks;
CREATE TRIGGER trg_personal_notebooks_updated_at
BEFORE UPDATE ON personal_notebooks
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_room_notebooks_updated_at ON room_notebooks;
CREATE TRIGGER trg_room_notebooks_updated_at
BEFORE UPDATE ON room_notebooks
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_exams_updated_at ON exams;
CREATE TRIGGER trg_exams_updated_at
BEFORE UPDATE ON exams
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_documents_updated_at ON documents;
CREATE TRIGGER trg_documents_updated_at
BEFORE UPDATE ON documents
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_ai_conversations_updated_at ON ai_conversations;
CREATE TRIGGER trg_ai_conversations_updated_at
BEFORE UPDATE ON ai_conversations
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- Supabase exposes public-schema tables through the Data API. Keep every table
-- fail-closed from the migration that creates it; later migrations install the
-- operation-specific policies and grants.
ALTER TABLE public.health ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notebooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.study_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.members_rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.personal_notebooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.room_notebooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exam_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.questions_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.flashcards ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
