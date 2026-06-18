BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE users (
    user_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name varchar(255) NOT NULL,
    email varchar(320) NOT NULL UNIQUE,
    password_hash varchar(255) NOT NULL,
    avatar_url varchar(2048),
    role varchar(50) NOT NULL DEFAULT 'student',
    account_status varchar(50) NOT NULL DEFAULT 'active',
    timezone varchar(100) NOT NULL DEFAULT 'UTC',
    last_login_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT users_email_lowercase_chk CHECK (email = lower(email)),
    CONSTRAINT users_role_chk CHECK (role IN ('student', 'teacher', 'admin')),
    CONSTRAINT users_account_status_chk CHECK (account_status IN ('active', 'inactive', 'suspended', 'deleted'))
);

CREATE TABLE notebooks_tags (
    tag_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name varchar(120) NOT NULL,
    color varchar(32),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT notebooks_tags_user_name_uk UNIQUE (user_id, name),
    CONSTRAINT notebooks_tags_tag_id_user_id_uk UNIQUE (tag_id, user_id)
);

CREATE TABLE notebooks (
    notebook_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title varchar(255) NOT NULL,
    description text,
    visibility varchar(50) NOT NULL DEFAULT 'private',
    status varchar(50) NOT NULL DEFAULT 'active',
    metadata jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT notebooks_visibility_chk CHECK (visibility IN ('private', 'shared', 'public')),
    CONSTRAINT notebooks_status_chk CHECK (status IN ('active', 'archived', 'deleted')),
    CONSTRAINT notebooks_notebook_id_user_id_uk UNIQUE (notebook_id, user_id)
);

CREATE TABLE flashcards (
    flashcard_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id uuid NOT NULL REFERENCES notebooks(notebook_id) ON DELETE CASCADE,
    study_room_id uuid REFERENCES study_rooms(study_room_id) ON DELETE SET NULL,
    user_id uuid NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    question text NOT NULL,
    answer text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT flashcards_question_not_empty CHECK (question <> ''),
    CONSTRAINT flashcards_answer_not_empty CHECK (answer <> '')
);

CREATE TABLE notebooks_tags_assignments (
    notebook_id uuid NOT NULL,
    tag_id uuid NOT NULL,
    user_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (notebook_id, tag_id),
    CONSTRAINT notebooks_tags_assignments_notebook_user_fk
        FOREIGN KEY (notebook_id, user_id)
        REFERENCES notebooks(notebook_id, user_id)
        ON DELETE CASCADE,
    CONSTRAINT notebooks_tags_assignments_tag_user_fk
        FOREIGN KEY (tag_id, user_id)
        REFERENCES notebooks_tags(tag_id, user_id)
        ON DELETE CASCADE,
    CONSTRAINT notebooks_tags_assignments_user_fk
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE documents (
    document_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id uuid NOT NULL REFERENCES notebooks(notebook_id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title varchar(255) NOT NULL,
    original_filename varchar(255) NOT NULL,
    file_type varchar(100) NOT NULL,
    file_size_bytes bigint NOT NULL,
    storage_path varchar(2048) NOT NULL,
    processing_status varchar(50) NOT NULL DEFAULT 'pending',
    processing_error text,
    metadata jsonb,
    uploaded_at timestamptz NOT NULL DEFAULT now(),
    processed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT documents_file_size_chk CHECK (file_size_bytes >= 0),
    CONSTRAINT documents_processing_status_chk CHECK (
        processing_status IN ('pending', 'processing', 'processed', 'failed')
    )
);

CREATE TABLE documents_chunks (
    chunk_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id uuid NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    chunk_index int NOT NULL,
    page_start int,
    page_end int,
    content text NOT NULL,
    embedding vector,
    token_count int,
    embedding_model varchar(120),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT documents_chunks_document_index_uk UNIQUE (document_id, chunk_index),
    CONSTRAINT documents_chunks_index_chk CHECK (chunk_index >= 0),
    CONSTRAINT documents_chunks_pages_chk CHECK (
        (page_start IS NULL OR page_start >= 0)
        AND (page_end IS NULL OR page_end >= 0)
        AND (page_start IS NULL OR page_end IS NULL OR page_end >= page_start)
    ),
    CONSTRAINT documents_chunks_token_count_chk CHECK (token_count IS NULL OR token_count >= 0)
);

CREATE TABLE summaries (
    summary_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id uuid NOT NULL REFERENCES notebooks(notebook_id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    study_room_id uuid REFERENCES study_rooms(study_room_id) ON DELETE SET NULL,
    title varchar(255) NOT NULL,
    content text NOT NULL,
    summary_type varchar(80) NOT NULL,
    model_name varchar(120),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE chat_ai_notebooks (
    chat_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id uuid NOT NULL REFERENCES notebooks(notebook_id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title varchar(255),
    status varchar(50) NOT NULL DEFAULT 'active',
    model_name varchar(120),
    temperature numeric(4,3),
    max_context_chunks int NOT NULL DEFAULT 8,
    started_at timestamptz NOT NULL DEFAULT now(),
    last_message_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chat_ai_notebooks_status_chk CHECK (status IN ('active', 'archived', 'deleted')),
    CONSTRAINT chat_ai_notebooks_temperature_chk CHECK (
        temperature IS NULL OR (temperature >= 0 AND temperature <= 2)
    ),
    CONSTRAINT chat_ai_notebooks_context_chk CHECK (max_context_chunks >= 0)
);

CREATE TABLE chat_ai_notebooks_messages (
    message_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id uuid NOT NULL REFERENCES chat_ai_notebooks(chat_id) ON DELETE CASCADE,
    user_id uuid REFERENCES users(user_id) ON DELETE SET NULL,
    role varchar(50) NOT NULL,
    content text NOT NULL,
    model_name varchar(120),
    retrieved_chunks jsonb NOT NULL DEFAULT '[]'::jsonb,
    citations jsonb NOT NULL DEFAULT '[]'::jsonb,
    token_input int,
    token_output int,
    latency_ms numeric(12,3),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chat_ai_notebooks_messages_role_chk CHECK (role IN ('system', 'user', 'assistant', 'tool')),
    CONSTRAINT chat_ai_notebooks_messages_tokens_chk CHECK (
        (token_input IS NULL OR token_input >= 0)
        AND (token_output IS NULL OR token_output >= 0)
        AND (latency_ms IS NULL OR latency_ms >= 0)
    )
);

CREATE TABLE base_prompt (
    prompt_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES users(user_id) ON DELETE CASCADE,
    prompt_key varchar(120) NOT NULL UNIQUE,
    module varchar(120) NOT NULL,
    system_prompt text,
    developer_prompt text,
    model_name varchar(120),
    temperature numeric(4,3),
    max_tokens int,
    is_active boolean NOT NULL DEFAULT true,
    version int NOT NULL DEFAULT 1,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT base_prompt_temperature_chk CHECK (
        temperature IS NULL OR (temperature >= 0 AND temperature <= 2)
    ),
    CONSTRAINT base_prompt_limits_chk CHECK (
        version > 0
        AND (max_tokens IS NULL OR max_tokens > 0)
    )
);

CREATE TABLE mocks_tests (
    mock_test_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    notebook_id uuid REFERENCES notebooks(notebook_id) ON DELETE CASCADE,
    study_room_id uuid REFERENCES study_rooms(study_room_id) ON DELETE SET NULL,
    user_id uuid NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title varchar(255) NOT NULL,
    test_type varchar(80) NOT NULL,
    difficulty varchar(50),
    total_questions int NOT NULL DEFAULT 0,
    questions jsonb NOT NULL DEFAULT '[]'::jsonb,
    model_name varchar(120),
    token_input int,
    token_output int,
    latency_ms numeric(12,3),
    status varchar(50) NOT NULL DEFAULT 'draft',
    generated_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT mocks_tests_total_questions_chk CHECK (total_questions >= 0),
    CONSTRAINT mocks_tests_difficulty_chk CHECK (
        difficulty IS NULL OR difficulty IN ('easy', 'medium', 'hard')
    ),
    CONSTRAINT mocks_tests_status_chk CHECK (status IN ('draft', 'generated', 'published', 'archived')),
    CONSTRAINT mocks_tests_tokens_chk CHECK (
        (token_input IS NULL OR token_input >= 0)
        AND (token_output IS NULL OR token_output >= 0)
        AND (latency_ms IS NULL OR latency_ms >= 0)
    )
);

CREATE TABLE test_results (
    result_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    mock_test_id uuid NOT NULL REFERENCES mocks_tests(mock_test_id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    score numeric(5,2),
    total_questions int NOT NULL DEFAULT 0,
    correct_answers int NOT NULL DEFAULT 0,
    incorrect_answers int NOT NULL DEFAULT 0,
    skipped_answers int NOT NULL DEFAULT 0,
    time_spent_seconds int NOT NULL DEFAULT 0,
    user_answers jsonb NOT NULL DEFAULT '[]'::jsonb,
    grading_details jsonb NOT NULL DEFAULT '{}'::jsonb,
    result_status varchar(50) NOT NULL DEFAULT 'in_progress',
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT test_results_score_chk CHECK (score IS NULL OR (score >= 0 AND score <= 100)),
    CONSTRAINT test_results_counts_chk CHECK (
        total_questions >= 0
        AND correct_answers >= 0
        AND incorrect_answers >= 0
        AND skipped_answers >= 0
        AND time_spent_seconds >= 0
    ),
    CONSTRAINT test_results_status_chk CHECK (result_status IN ('in_progress', 'completed', 'abandoned'))
);

CREATE TABLE logs (
    log_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES users(user_id) ON DELETE SET NULL,
    notebook_id uuid REFERENCES notebooks(notebook_id) ON DELETE SET NULL,
    document_id uuid REFERENCES documents(document_id) ON DELETE SET NULL,
    request_id uuid,
    correlation_id uuid,
    transaction_id uuid,
    trace_id varchar(128),
    span_id varchar(128),
    parent_span_id varchar(128),
    log_level varchar(20) NOT NULL,
    event_type varchar(120),
    http_method varchar(20),
    endpoint varchar(2048),
    status_code int,
    latency_ms numeric(12,3),
    service_name varchar(120),
    module_name varchar(120),
    action_name varchar(120),
    entity_type varchar(120),
    entity_id uuid,
    source_ip varchar(64),
    user_agent text,
    message text NOT NULL,
    request_payload jsonb,
    response_payload jsonb,
    error_details jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT logs_log_level_chk CHECK (log_level IN ('debug', 'info', 'warning', 'error', 'critical')),
    CONSTRAINT logs_status_latency_chk CHECK (
        (status_code IS NULL OR (status_code >= 100 AND status_code <= 599))
        AND (latency_ms IS NULL OR latency_ms >= 0)
    )
);

CREATE TABLE study_rooms (
    study_room_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_user_id uuid NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name varchar(255) NOT NULL,
    description text,
    visibility varchar(50) NOT NULL DEFAULT 'private',
    access_code varchar(80) UNIQUE,
    status varchar(50) NOT NULL DEFAULT 'active',
    members_count int NOT NULL DEFAULT 1,
    documents_count int NOT NULL DEFAULT 0,
    summaries_count int NOT NULL DEFAULT 0,
    average_score numeric(5,2) NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT study_rooms_visibility_chk CHECK (visibility IN ('private', 'public', 'invite_only')),
    CONSTRAINT study_rooms_status_chk CHECK (status IN ('active', 'archived', 'deleted')),
    CONSTRAINT study_rooms_counts_chk CHECK (
        members_count >= 0
        AND documents_count >= 0
        AND summaries_count >= 0
        AND average_score >= 0
        AND average_score <= 100
    )
);

CREATE TABLE study_rooms_members (
    study_room_id uuid NOT NULL REFERENCES study_rooms(study_room_id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    member_role varchar(50) NOT NULL DEFAULT 'member',
    member_status varchar(50) NOT NULL DEFAULT 'active',
    can_upload_documents boolean NOT NULL DEFAULT false,
    can_create_channels boolean NOT NULL DEFAULT false,
    can_generate_summaries boolean NOT NULL DEFAULT false,
    can_use_ai_chat boolean NOT NULL DEFAULT true,
    joined_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (study_room_id, user_id),
    CONSTRAINT study_rooms_members_role_chk CHECK (member_role IN ('owner', 'admin', 'member')),
    CONSTRAINT study_rooms_members_status_chk CHECK (member_status IN ('active', 'invited', 'blocked', 'left'))
);

-- CREATE TABLE study_rooms_documents (
--     study_room_document_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
--     study_room_id uuid NOT NULL REFERENCES study_rooms(study_room_id) ON DELETE CASCADE,
--     uploaded_by_user_id uuid NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
--     title varchar(255) NOT NULL,
--     original_filename varchar(255) NOT NULL,
--     file_type varchar(100) NOT NULL,
--     file_size_bytes bigint NOT NULL,
--     storage_path varchar(2048) NOT NULL,
--     processing_status varchar(50) NOT NULL DEFAULT 'pending',
--     processing_error text,
--     total_pages int,
--     total_chunks int NOT NULL DEFAULT 0,
--     checksum_sha256 varchar(64),
--     uploaded_at timestamptz NOT NULL DEFAULT now(),
--     processed_at timestamptz,
--     created_at timestamptz NOT NULL DEFAULT now(),
--     updated_at timestamptz NOT NULL DEFAULT now(),
--     deleted_at timestamptz,
--     CONSTRAINT study_rooms_documents_file_size_chk CHECK (file_size_bytes >= 0),
--     CONSTRAINT study_rooms_documents_pages_chunks_chk CHECK (
--         (total_pages IS NULL OR total_pages >= 0)
--         AND total_chunks >= 0
--     ),
--     CONSTRAINT study_rooms_documents_processing_status_chk CHECK (
--         processing_status IN ('pending', 'processing', 'processed', 'failed')
--     ),
--     CONSTRAINT study_rooms_documents_checksum_sha256_chk CHECK (
--         checksum_sha256 IS NULL OR checksum_sha256 ~ '^[A-Fa-f0-9]{64}$'
--     )
-- );

-- CREATE TABLE study_rooms_documents_chunks (
--     chunk_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
--     study_room_document_id uuid NOT NULL REFERENCES study_rooms_documents(study_room_document_id) ON DELETE CASCADE,
--     chunk_index int NOT NULL,
--     page_start int,
--     page_end int,
--     content text NOT NULL,
--     embedding vector,
--     token_count int,
--     embedding_model varchar(120),
--     created_at timestamptz NOT NULL DEFAULT now(),
--     updated_at timestamptz NOT NULL DEFAULT now(),
--     CONSTRAINT study_rooms_documents_chunks_document_index_uk UNIQUE (study_room_document_id, chunk_index),
--     CONSTRAINT study_rooms_documents_chunks_index_chk CHECK (chunk_index >= 0),
--     CONSTRAINT study_rooms_documents_chunks_pages_chk CHECK (
--         (page_start IS NULL OR page_start >= 0)
--         AND (page_end IS NULL OR page_end >= 0)
--         AND (page_start IS NULL OR page_end IS NULL OR page_end >= page_start)
--     ),
--     CONSTRAINT study_rooms_documents_chunks_token_count_chk CHECK (token_count IS NULL OR token_count >= 0)
-- );

-- CREATE TABLE study_rooms_channels (
--     channel_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
--     study_room_id uuid NOT NULL REFERENCES study_rooms(study_room_id) ON DELETE CASCADE,
--     created_by_user_id uuid NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
--     name varchar(120) NOT NULL,
--     description text,
--     channel_type varchar(50) NOT NULL DEFAULT 'text',
--     status varchar(50) NOT NULL DEFAULT 'active',
--     is_private boolean NOT NULL DEFAULT false,
--     created_at timestamptz NOT NULL DEFAULT now(),
--     updated_at timestamptz NOT NULL DEFAULT now(),
--     deleted_at timestamptz,
--     CONSTRAINT study_rooms_channels_room_name_uk UNIQUE (study_room_id, name),
--     CONSTRAINT study_rooms_channels_type_chk CHECK (channel_type IN ('text', 'ai_chat', 'announcements')),
--     CONSTRAINT study_rooms_channels_status_chk CHECK (status IN ('active', 'archived', 'deleted'))
-- );

-- CREATE TABLE study_rooms_channels_messages (
--     message_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
--     channel_id uuid NOT NULL REFERENCES study_rooms_channels(channel_id) ON DELETE CASCADE,
--     study_room_id uuid NOT NULL REFERENCES study_rooms(study_room_id) ON DELETE CASCADE,
--     user_id uuid REFERENCES users(user_id) ON DELETE SET NULL,
--     content text NOT NULL,
--     message_type varchar(50) NOT NULL DEFAULT 'text',
--     attachments jsonb NOT NULL DEFAULT '[]'::jsonb,
--     mentions jsonb NOT NULL DEFAULT '[]'::jsonb,
--     is_edited boolean NOT NULL DEFAULT false,
--     created_at timestamptz NOT NULL DEFAULT now(),
--     updated_at timestamptz NOT NULL DEFAULT now(),
--     deleted_at timestamptz,
--     CONSTRAINT study_rooms_channels_messages_type_chk CHECK (
--         message_type IN ('text', 'file', 'system', 'ai')
--     )
-- );

-- CREATE TABLE study_rooms_chat_ai (
--     chat_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
--     study_room_id uuid NOT NULL REFERENCES study_rooms(study_room_id) ON DELETE CASCADE,
--     channel_id uuid REFERENCES study_rooms_channels(channel_id) ON DELETE SET NULL,
--     created_by_user_id uuid NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
--     title varchar(255),
--     status varchar(50) NOT NULL DEFAULT 'active',
--     model_name varchar(120),
--     temperature numeric(4,3),
--     max_context_chunks int NOT NULL DEFAULT 8,
--     started_at timestamptz NOT NULL DEFAULT now(),
--     last_message_at timestamptz,
--     created_at timestamptz NOT NULL DEFAULT now(),
--     updated_at timestamptz NOT NULL DEFAULT now(),
--     CONSTRAINT study_rooms_chat_ai_status_chk CHECK (status IN ('active', 'archived', 'deleted')),
--     CONSTRAINT study_rooms_chat_ai_temperature_chk CHECK (
--         temperature IS NULL OR (temperature >= 0 AND temperature <= 2)
--     ),
--     CONSTRAINT study_rooms_chat_ai_context_chk CHECK (max_context_chunks >= 0)
-- );

CREATE TABLE study_rooms_chat_ai_messages (
    message_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id uuid NOT NULL REFERENCES study_rooms_chat_ai(chat_id) ON DELETE CASCADE,
    study_room_id uuid NOT NULL REFERENCES study_rooms(study_room_id) ON DELETE CASCADE,
    user_id uuid REFERENCES users(user_id) ON DELETE SET NULL,
    role varchar(50) NOT NULL,
    content text NOT NULL,
    model_name varchar(120),
    retrieved_chunks jsonb NOT NULL DEFAULT '[]'::jsonb,
    citations jsonb NOT NULL DEFAULT '[]'::jsonb,
    token_input int,
    token_output int,
    latency_ms numeric(12,3),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT study_rooms_chat_ai_messages_role_chk CHECK (role IN ('system', 'user', 'assistant', 'tool')),
    CONSTRAINT study_rooms_chat_ai_messages_tokens_chk CHECK (
        (token_input IS NULL OR token_input >= 0)
        AND (token_output IS NULL OR token_output >= 0)
        AND (latency_ms IS NULL OR latency_ms >= 0)
    )
);

-- CREATE TABLE study_rooms_summaries (
--     summary_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
--     study_room_id uuid NOT NULL REFERENCES study_rooms(study_room_id) ON DELETE CASCADE,
--     generated_by_user_id uuid NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
--     title varchar(255) NOT NULL,
--     content text NOT NULL,
--     summary_type varchar(80) NOT NULL,
--     model_name varchar(120),
--     source_documents_count int NOT NULL DEFAULT 0,
--     source_chunks_count int NOT NULL DEFAULT 0,
--     token_input int,
--     token_output int,
--     latency_ms numeric(12,3),
--     generated_at timestamptz NOT NULL DEFAULT now(),
--     created_at timestamptz NOT NULL DEFAULT now(),
--     updated_at timestamptz NOT NULL DEFAULT now(),
--     CONSTRAINT study_rooms_summaries_counts_chk CHECK (
--         source_documents_count >= 0
--         AND source_chunks_count >= 0
--         AND (token_input IS NULL OR token_input >= 0)
--         AND (token_output IS NULL OR token_output >= 0)
--         AND (latency_ms IS NULL OR latency_ms >= 0)
--     )
-- );

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_account_status ON users(account_status);
CREATE INDEX idx_notebooks_user_id ON notebooks(user_id);
CREATE INDEX idx_notebooks_status ON notebooks(status);
CREATE INDEX idx_notebooks_tags_assignments_tag_id ON notebooks_tags_assignments(tag_id);
CREATE INDEX idx_notebooks_tags_assignments_user_id ON notebooks_tags_assignments(user_id);
CREATE INDEX idx_documents_notebook_id ON documents(notebook_id);
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_processing_status ON documents(processing_status);
CREATE INDEX idx_documents_chunks_document_id ON documents_chunks(document_id);
CREATE INDEX idx_summaries_notebook_id ON summaries(notebook_id);
CREATE INDEX idx_summaries_user_id ON summaries(user_id);
CREATE INDEX idx_chat_ai_notebooks_notebook_id ON chat_ai_notebooks(notebook_id);
CREATE INDEX idx_chat_ai_notebooks_user_id ON chat_ai_notebooks(user_id);
CREATE INDEX idx_chat_ai_notebooks_messages_chat_id ON chat_ai_notebooks_messages(chat_id);
CREATE INDEX idx_chat_ai_notebooks_messages_user_id ON chat_ai_notebooks_messages(user_id);
CREATE INDEX idx_base_prompt_user_id ON base_prompt(user_id);
CREATE INDEX idx_base_prompt_module ON base_prompt(module);
CREATE INDEX idx_mocks_tests_notebook_id ON mocks_tests(notebook_id);
CREATE INDEX idx_mocks_tests_user_id ON mocks_tests(user_id);
CREATE INDEX idx_test_results_mock_test_id ON test_results(mock_test_id);
CREATE INDEX idx_test_results_user_id ON test_results(user_id);
CREATE INDEX idx_logs_user_id ON logs(user_id);
CREATE INDEX idx_logs_notebook_id ON logs(notebook_id);
CREATE INDEX idx_logs_document_id ON logs(document_id);
CREATE INDEX idx_logs_correlation_id ON logs(correlation_id);
CREATE INDEX idx_logs_created_at ON logs(created_at);
CREATE INDEX idx_logs_log_level ON logs(log_level);
CREATE INDEX idx_study_rooms_owner_user_id ON study_rooms(owner_user_id);
CREATE INDEX idx_study_rooms_visibility ON study_rooms(visibility);
CREATE INDEX idx_study_rooms_members_user_id ON study_rooms_members(user_id);
CREATE INDEX idx_study_rooms_documents_study_room_id ON study_rooms_documents(study_room_id);
CREATE INDEX idx_study_rooms_documents_uploaded_by_user_id ON study_rooms_documents(uploaded_by_user_id);
CREATE INDEX idx_study_rooms_documents_chunks_document_id ON study_rooms_documents_chunks(study_room_document_id);
-- CREATE INDEX idx_study_rooms_channels_study_room_id ON study_rooms_channels(study_room_id);
-- CREATE INDEX idx_study_rooms_channels_created_by_user_id ON study_rooms_channels(created_by_user_id);
-- CREATE INDEX idx_study_rooms_channels_messages_channel_id ON study_rooms_channels_messages(channel_id);
-- CREATE INDEX idx_study_rooms_channels_messages_study_room_id ON study_rooms_channels_messages(study_room_id);
-- CREATE INDEX idx_study_rooms_channels_messages_user_id ON study_rooms_channels_messages(user_id);
CREATE INDEX idx_study_rooms_chat_ai_study_room_id ON study_rooms_chat_ai(study_room_id);
CREATE INDEX idx_study_rooms_chat_ai_channel_id ON study_rooms_chat_ai(channel_id);
CREATE INDEX idx_study_rooms_chat_ai_created_by_user_id ON study_rooms_chat_ai(created_by_user_id);
CREATE INDEX idx_study_rooms_chat_ai_messages_chat_id ON study_rooms_chat_ai_messages(chat_id);
CREATE INDEX idx_study_rooms_chat_ai_messages_study_room_id ON study_rooms_chat_ai_messages(study_room_id);
CREATE INDEX idx_study_rooms_chat_ai_messages_user_id ON study_rooms_chat_ai_messages(user_id);
-- CREATE INDEX idx_study_rooms_summaries_study_room_id ON study_rooms_summaries(study_room_id);
-- CREATE INDEX idx_study_rooms_summaries_generated_by_user_id ON study_rooms_summaries(generated_by_user_id);

CREATE TRIGGER set_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_notebooks_tags_updated_at
BEFORE UPDATE ON notebooks_tags
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_notebooks_updated_at
BEFORE UPDATE ON notebooks
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_chat_ai_notebooks_updated_at
BEFORE UPDATE ON chat_ai_notebooks
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_base_prompt_updated_at
BEFORE UPDATE ON base_prompt
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_mocks_tests_updated_at
BEFORE UPDATE ON mocks_tests
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_study_rooms_updated_at
BEFORE UPDATE ON study_rooms
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_study_rooms_members_updated_at
BEFORE UPDATE ON study_rooms_members
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_study_rooms_documents_updated_at
BEFORE UPDATE ON study_rooms_documents
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_study_rooms_documents_chunks_updated_at
BEFORE UPDATE ON study_rooms_documents_chunks
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- CREATE TRIGGER set_study_rooms_channels_updated_at
-- BEFORE UPDATE ON study_rooms_channels
-- FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- CREATE TRIGGER set_study_rooms_channels_messages_updated_at
-- BEFORE UPDATE ON study_rooms_channels_messages
-- FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_study_rooms_chat_ai_updated_at
BEFORE UPDATE ON study_rooms_chat_ai
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- CREATE TRIGGER set_study_rooms_summaries_updated_at
-- BEFORE UPDATE ON study_rooms_summaries
-- FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMIT;
