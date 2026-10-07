ALTER TABLE reporting_sync_state
    ADD COLUMN last_started_at DATETIME NULL,
    ADD COLUMN last_completed_at DATETIME NULL,
    ADD COLUMN last_duration_ms BIGINT NULL,
    ADD COLUMN last_received_count INT NOT NULL DEFAULT 0,
    ADD COLUMN last_inserted_count INT NOT NULL DEFAULT 0,
    ADD COLUMN last_updated_count INT NOT NULL DEFAULT 0,
    ADD COLUMN last_ignored_count INT NOT NULL DEFAULT 0,
    ADD COLUMN last_deleted_count INT NOT NULL DEFAULT 0,
    ADD COLUMN last_indexed_count INT NOT NULL DEFAULT 0,
    ADD COLUMN last_error_count INT NOT NULL DEFAULT 0,
    ADD COLUMN last_error TEXT NULL;
