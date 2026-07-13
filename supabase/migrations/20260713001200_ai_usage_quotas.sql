BEGIN;

CREATE TABLE IF NOT EXISTS public.ai_usage_events (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    operation VARCHAR(32) NOT NULL CHECK (
        operation IN (
            'chat',
            'document_embedding',
            'flashcards',
            'exam',
            'exam_grading'
        )
    ),
    units INTEGER NOT NULL DEFAULT 1 CHECK (units BETWEEN 1 AND 100),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ai_usage_events_user_operation_time_idx
ON public.ai_usage_events (user_id, operation, occurred_at DESC);

ALTER TABLE public.ai_usage_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_usage_events FORCE ROW LEVEL SECURITY;
REVOKE ALL PRIVILEGES ON TABLE public.ai_usage_events
FROM PUBLIC, anon, authenticated;
GRANT ALL PRIVILEGES ON TABLE public.ai_usage_events TO service_role;

CREATE OR REPLACE FUNCTION public.reserve_ai_usage(
    p_actor_id UUID,
    p_operation TEXT,
    p_units INTEGER
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
SET timezone = 'UTC'
AS $$
DECLARE
    now_at TIMESTAMPTZ := statement_timestamp();
    hourly_limit INTEGER;
    daily_limit INTEGER;
    hourly_count BIGINT;
    daily_count BIGINT;
BEGIN
    IF p_actor_id IS NULL
       OR NOT EXISTS (
           SELECT 1
           FROM public.users u
           WHERE u.user_id = p_actor_id
             AND u.status = 'active'
       ) THEN
        RAISE EXCEPTION 'resource not found' USING ERRCODE = 'P0002';
    END IF;
    IF p_units IS NULL OR p_units NOT BETWEEN 1 AND 100 THEN
        RAISE EXCEPTION 'invalid ai units' USING ERRCODE = '22023';
    END IF;

    CASE p_operation
        WHEN 'chat' THEN
            hourly_limit := 30;
            daily_limit := 200;
        WHEN 'document_embedding' THEN
            hourly_limit := 20;
            daily_limit := 100;
        WHEN 'flashcards' THEN
            hourly_limit := 10;
            daily_limit := 30;
        WHEN 'exam' THEN
            hourly_limit := 5;
            daily_limit := 15;
        WHEN 'exam_grading' THEN
            -- One unit equals one open answer sent to the semantic verifier.
            hourly_limit := 30;
            daily_limit := 100;
        ELSE
            RAISE EXCEPTION 'invalid ai operation' USING ERRCODE = '22023';
    END CASE;

    PERFORM pg_advisory_xact_lock(
        hashtextextended(p_actor_id::TEXT || ':' || p_operation, 0)
    );

    DELETE FROM public.ai_usage_events event
    WHERE event.user_id = p_actor_id
      AND event.occurred_at < now_at - INTERVAL '30 days';

    SELECT
        COALESCE(SUM(event.units) FILTER (
            WHERE event.occurred_at >= now_at - INTERVAL '1 hour'
        ), 0)::BIGINT,
        COALESCE(SUM(event.units) FILTER (
            WHERE event.occurred_at >= date_trunc('day', now_at)
        ), 0)::BIGINT
    INTO hourly_count, daily_count
    FROM public.ai_usage_events event
    WHERE event.user_id = p_actor_id
      AND event.operation = p_operation;

    IF hourly_count + p_units > hourly_limit
       OR daily_count + p_units > daily_limit THEN
        RAISE EXCEPTION 'ai_usage_rate_limit' USING ERRCODE = 'P0001';
    END IF;

    INSERT INTO public.ai_usage_events (user_id, operation, units, occurred_at)
    VALUES (p_actor_id, p_operation, p_units, now_at);
END;
$$;

REVOKE ALL ON FUNCTION public.reserve_ai_usage(UUID, TEXT, INTEGER)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.reserve_ai_usage(UUID, TEXT, INTEGER)
TO service_role;

COMMIT;
