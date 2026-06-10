BEGIN;

ALTER TABLE notebooks
    ADD CONSTRAINT notebooks_notebook_id_user_id_uk UNIQUE (notebook_id, user_id);

ALTER TABLE notebooks_tags
    ADD CONSTRAINT notebooks_tags_tag_id_user_id_uk UNIQUE (tag_id, user_id);

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

INSERT INTO notebooks_tags_assignments (notebook_id, tag_id, user_id)
SELECT notebook_id, tag_id, user_id
FROM notebooks
WHERE tag_id IS NOT NULL
ON CONFLICT (notebook_id, tag_id) DO NOTHING;

DROP INDEX IF EXISTS idx_notebooks_tag_id;

ALTER TABLE notebooks
    DROP CONSTRAINT IF EXISTS notebooks_tag_id_fkey;

ALTER TABLE notebooks
    DROP COLUMN IF EXISTS tag_id;

CREATE INDEX idx_notebooks_tags_assignments_tag_id
    ON notebooks_tags_assignments(tag_id);

CREATE INDEX idx_notebooks_tags_assignments_user_id
    ON notebooks_tags_assignments(user_id);

COMMIT;
