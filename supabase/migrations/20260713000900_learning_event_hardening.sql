BEGIN;

-- Every client-originated event has a stable replay key. Existing rows receive a
-- deterministic legacy key so the migration is safe on populated databases.
ALTER TABLE public.user_learning_events
ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(128);

UPDATE public.user_learning_events
SET idempotency_key = 'legacy:' || event_id::TEXT
WHERE idempotency_key IS NULL;

ALTER TABLE public.user_learning_events
ALTER COLUMN idempotency_key SET DEFAULT gen_random_uuid()::TEXT,
ALTER COLUMN idempotency_key SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'user_learning_events_idempotency_key_format_check'
          AND conrelid = 'public.user_learning_events'::regclass
    ) THEN
        ALTER TABLE public.user_learning_events
        ADD CONSTRAINT user_learning_events_idempotency_key_format_check
        CHECK (
            idempotency_key ~ '^[A-Za-z0-9][A-Za-z0-9._:-]{15,127}$'
        );
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS user_learning_events_user_idempotency_uidx
ON public.user_learning_events (user_id, idempotency_key);

-- Direct inserts allowed clients to fabricate arbitrary totals and made quota
-- checks racy. All client writes now pass through the atomic RPC below.
DROP POLICY IF EXISTS user_learning_events_insert_client_activity
ON public.user_learning_events;
REVOKE INSERT, UPDATE, DELETE ON public.user_learning_events
FROM anon, authenticated;
GRANT SELECT ON public.user_learning_events TO authenticated;

CREATE OR REPLACE FUNCTION public.record_user_learning_event(
    p_notebook_id UUID,
    p_activity_type TEXT,
    p_quantity INTEGER,
    p_duration_seconds INTEGER,
    p_idempotency_key TEXT
)
RETURNS SETOF public.user_learning_events
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
SET timezone = 'UTC'
AS $$
DECLARE
    v_user_id UUID := auth.uid();
    v_existing public.user_learning_events%ROWTYPE;
    v_now TIMESTAMPTZ := statement_timestamp();
    v_day_start TIMESTAMPTZ;
    v_recent_events INTEGER;
    v_daily_events INTEGER;
    v_daily_duration BIGINT;
    v_daily_flashcards BIGINT;
BEGIN
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'not_authenticated'
            USING ERRCODE = '42501';
    END IF;
    IF NOT public.current_user_is_active() THEN
        RAISE EXCEPTION 'inactive_user'
            USING ERRCODE = '42501';
    END IF;

    IF p_idempotency_key IS NULL
       OR p_idempotency_key !~ '^[A-Za-z0-9][A-Za-z0-9._:-]{15,127}$' THEN
        RAISE EXCEPTION 'invalid_idempotency_key'
            USING ERRCODE = '22023';
    END IF;

    -- Serialize counters per actor. This prevents concurrent requests from
    -- passing the quota independently and makes replay handling deterministic.
    PERFORM pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended(v_user_id::TEXT, 0)
    );

    SELECT event.*
    INTO v_existing
    FROM public.user_learning_events AS event
    WHERE event.user_id = v_user_id
      AND event.idempotency_key = p_idempotency_key;

    IF FOUND THEN
        IF v_existing.notebook_id IS DISTINCT FROM p_notebook_id
           OR v_existing.activity_type IS DISTINCT FROM p_activity_type
           OR v_existing.quantity IS DISTINCT FROM p_quantity
           OR v_existing.duration_seconds IS DISTINCT FROM p_duration_seconds THEN
            RAISE EXCEPTION 'idempotency_key_reused'
                USING ERRCODE = '23505';
        END IF;
        RETURN NEXT v_existing;
        RETURN;
    END IF;

    IF p_activity_type NOT IN ('study_session', 'flashcard_reviewed')
       OR p_quantity IS NULL
       OR p_duration_seconds IS NULL
       OR p_quantity < 1
       OR p_quantity > 50
       OR p_duration_seconds < 0
       OR p_duration_seconds > 14400
       OR (
           p_activity_type = 'study_session'
           AND (p_quantity <> 1 OR p_duration_seconds < 30)
       )
       OR (
           p_activity_type = 'flashcard_reviewed'
           AND p_duration_seconds > 3600
       ) THEN
        RAISE EXCEPTION 'invalid_learning_event'
            USING ERRCODE = '22023';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM public.personal_notebooks AS personal
        WHERE personal.notebook_id = p_notebook_id
          AND personal.user_id = v_user_id
        UNION ALL
        SELECT 1
        FROM public.room_notebooks AS room_notebook
        JOIN public.members_rooms AS membership
          ON membership.room_id = room_notebook.room_id
        JOIN public.study_members AS member
          ON member.member_id = membership.member_id
        WHERE room_notebook.notebook_id = p_notebook_id
          AND member.user_id = v_user_id
    ) THEN
        RAISE EXCEPTION 'notebook_access_denied'
            USING ERRCODE = '42501';
    END IF;

    SELECT COUNT(*)::INTEGER
    INTO v_recent_events
    FROM public.user_learning_events AS event
    WHERE event.user_id = v_user_id
      AND event.occurred_at >= v_now - INTERVAL '60 seconds';

    IF v_recent_events >= 30 THEN
        RAISE EXCEPTION 'learning_event_rate_limit'
            USING ERRCODE = 'P0001';
    END IF;

    v_day_start := date_trunc('day', v_now);
    SELECT
        COUNT(*)::INTEGER,
        COALESCE(SUM(event.duration_seconds), 0)::BIGINT,
        COALESCE(
            SUM(event.quantity) FILTER (
                WHERE event.activity_type = 'flashcard_reviewed'
            ),
            0
        )::BIGINT
    INTO v_daily_events, v_daily_duration, v_daily_flashcards
    FROM public.user_learning_events AS event
    WHERE event.user_id = v_user_id
      AND event.occurred_at >= v_day_start;

    -- These are abuse ceilings, not engagement goals: 1000 event batches,
    -- 12 reported hours or 1000 reviewed cards per UTC day.
    IF v_daily_events >= 1000
       OR v_daily_duration + p_duration_seconds > 43200
       OR (
           p_activity_type = 'flashcard_reviewed'
           AND v_daily_flashcards + p_quantity > 1000
       ) THEN
        RAISE EXCEPTION 'learning_event_daily_limit'
            USING ERRCODE = 'P0001';
    END IF;

    RETURN QUERY
    INSERT INTO public.user_learning_events AS event (
        user_id,
        notebook_id,
        activity_type,
        quantity,
        duration_seconds,
        idempotency_key,
        occurred_at
    )
    VALUES (
        v_user_id,
        p_notebook_id,
        p_activity_type,
        p_quantity,
        p_duration_seconds,
        p_idempotency_key,
        v_now
    )
    RETURNING event.*;
END;
$$;

REVOKE ALL ON FUNCTION public.record_user_learning_event(
    UUID, TEXT, INTEGER, INTEGER, TEXT
) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.record_user_learning_event(
    UUID, TEXT, INTEGER, INTEGER, TEXT
) TO authenticated;

COMMIT;
