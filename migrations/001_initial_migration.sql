CREATE EXTENSION IF NOT EXISTS VECTOR;

CREATE TABLE IF NOT EXISTS health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
)

INSERT INTO health (status) VALUES ('healthy');


CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hash_password TEXT NOT NULL,
    streak INTEGER NOT NULL DEFAULT 0, -- In days
    status varchar(20) NOT NULL DEFAULT 'active',
    CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
)


CREATE TABLE IF NOT EXISTS notebooks(
    notebook_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    grade INTEGER NOT NULL DEFAULT 0,
    summary TEXT,
    is_dominated BOOLEAN NOT NULL DEFAULT FALSE,
    is_favorite BOOLEAN NOT NULL DEFAULT FALSE,
    status varchar(20) NOT NULL DEFAULT 'active',
    CHECK (status IN ('active', 'archived', 'deleted')),
    spent_time INTEGER NOT NULL DEFAULT 0, -- In seconds
    last_seen_at TIMESTAMP,
    due_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)

CREATE TABLE IF NOT EXISTS personal_notebooks(
    notebook_id UUID PRIMARY KEY DEFAULT gen_random_uuid() REFERENCES notebooks(notebook_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    notebook_id UUID UNIQUE NOT NULL REFERENCES notebooks(notebook_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)

CREATE TABLE IF NOT EXISTS room_notebooks(
    notebook_id UUID PRIMARY KEY DEFAULT gen_random_uuid() REFERENCES notebooks(notebook_id) ON DELETE CASCADE,
    room_id UUID NOT NULL REFERENCES rooms(room_id) ON DELETE CASCADE,
    notebook_id UUID UNIQUE NOT NULL REFERENCES notebooks(notebook_id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES study_members(member_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)

CREATE TABLE IF NOT EXISTS study_members(
    member_id UUID PRIMARY KEY DEFAULT gen_random_uuid() REFERENCES users(user_id) ON DELETE CASCADE,
    nickname TEXT NOT NULL,
    role varchar(20) NOT NULL DEFAULT 'member',
    CHECK (role IN ('member', 'admin')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
    )

CREATE TABLE IF NOT EXISTS rooms(
    room_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)

CREATE TABLE IF NOT EXISTS members_rooms (
    member_id UUID REFERENCES study_members(member_id) ON DELETE CASCADE,
    room_id UUID REFERENCES rooms(room_id) ON DELETE CASCADE,
    PRIMARY KEY (member_id, room_id)
)

CREATE TABLE IF NOT EXISTS exams(
    exam_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id UUID NOT NULL REFERENCES notebooks(notebook_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    status varchar(20) NOT NULL DEFAULT 'active',
    CHECK (status IN ('active', 'archived', 'deleted')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)

CREATE TABLE IF NOT EXISTS attempts(
    attempt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id UUID NOT NULL REFERENCES exams(exam_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    score INTEGER NOT NULL DEFAULT 0,
    status varchar(20) NOT NULL DEFAULT 'in_progress',
    CHECK (status IN ('in_progress', 'completed', 'failed', 'not_started')),
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    started_at TIMESTAMP,
    spent_time INTEGER NOT NULL DEFAULT 0 -- In seconds
)

CREATE TABLE IF NOT EXISTS user_answers(
    answer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attempt_id UUID NOT NULL REFERENCES attempts(attempt_id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    user_answer TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE,
    points_awarded INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
)

CREATE TABLE IF NOT EXISTS questions(
    question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id UUID NOT NULL REFERENCES exams(exam_id) ON DELETE CASCADE,
    type varchar(20) NOT NULL DEFAULT 'multiple_choice',
    CHECK (type IN ('multiple_choice', 'true_false', 'open')),
    statement TEXT NOT NULL,
    order INTEGER NOT NULL,
    expected_answer TEXT NOT NULL,
    points INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
)

CREATE TABLE IF NOT EXISTS questions_options(
    option_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE,
    option_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
)

CREATE TABLE IF NOT EXISTS flashcards(
    flashcard_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id UUID NOT NULL REFERENCES notebooks(notebook_id) ON DELETE CASCADE,
    question_id UUID UNIQUE NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    spent_time INTEGER NOT NULL DEFAULT 0, -- In seconds
    created_at TIMESTAMP DEFAULT NOW(),
)

CREATE TABLE IF NOT EXISTS documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id UUID NOT NULL REFERENCES notebooks(notebook_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    storage_path TEXT NOT NULL,
    status varchar(20) NOT NULL DEFAULT 'active',
    CHECK (status IN ('active', 'archived', 'deleted')),
    mime_type TEXT NOT NULL,
    content_text TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    size INTEGER NOT NULL, -- In bytes
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)

CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    model TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
)

CREATE TABLE IF NOT EXISTS ai_conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id UUID NOT NULL REFERENCES notebooks(notebook_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    summary TEXT,
    spent_time INTEGER NOT NULL DEFAULT 0, -- In seconds
    status varchar(20) NOT NULL DEFAULT 'active',
    CHECK (status IN ('active', 'archived', 'deleted')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)

CREATE TABLE IF NOT EXISTS messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES ai_conversations(conversation_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    role varchar(20) NOT NULL DEFAULT 'user',
    CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    order_message INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
)