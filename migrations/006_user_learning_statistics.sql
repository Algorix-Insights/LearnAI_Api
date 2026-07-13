CREATE TABLE IF NOT EXISTS user_learning_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    notebook_id UUID NOT NULL REFERENCES notebooks(notebook_id) ON DELETE CASCADE,
    activity_type VARCHAR(32) NOT NULL CHECK (
        activity_type IN (
            'study_session',
            'flashcard_reviewed',
            'exam_completed',
            'document_uploaded',
            'resource_generated',
            'notebook_shared'
        )
    ),
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity BETWEEN 1 AND 10000),
    duration_seconds INTEGER NOT NULL DEFAULT 0 CHECK (
        duration_seconds BETWEEN 0 AND 86400
    ),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS user_learning_events_user_occurred_idx
ON user_learning_events (user_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS user_learning_events_notebook_occurred_idx
ON user_learning_events (notebook_id, occurred_at DESC);

ALTER TABLE user_learning_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_learning_events FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS user_learning_events_select_own ON user_learning_events;
CREATE POLICY user_learning_events_select_own
ON user_learning_events
FOR SELECT
TO authenticated
USING (user_id = auth.uid());

DROP POLICY IF EXISTS user_learning_events_insert_client_activity ON user_learning_events;
CREATE POLICY user_learning_events_insert_client_activity
ON user_learning_events
FOR INSERT
TO authenticated
WITH CHECK (
    user_id = auth.uid()
    AND activity_type IN ('study_session', 'flashcard_reviewed')
    AND EXISTS (
        SELECT 1
        FROM personal_notebooks pn
        WHERE pn.notebook_id = user_learning_events.notebook_id
          AND pn.user_id = auth.uid()
        UNION ALL
        SELECT 1
        FROM room_notebooks rn
        JOIN members_rooms mr ON mr.room_id = rn.room_id
        JOIN study_members sm ON sm.member_id = mr.member_id
        WHERE rn.notebook_id = user_learning_events.notebook_id
          AND sm.user_id = auth.uid()
    )
);

REVOKE ALL ON TABLE user_learning_events FROM anon;
GRANT SELECT, INSERT ON TABLE user_learning_events TO authenticated;
