CREATE TABLE reporting_sync_state (
    id BIGINT NOT NULL AUTO_INCREMENT,
    sync_name VARCHAR(100) NOT NULL,
    last_successful_sync_at DATETIME NULL,
    updated_at DATETIME NOT NULL,
    last_started_at DATETIME NULL,
    last_completed_at DATETIME NULL,
    last_duration_ms BIGINT NULL,
    last_received_count INT NOT NULL DEFAULT 0,
    last_inserted_count INT NOT NULL DEFAULT 0,
    last_updated_count INT NOT NULL DEFAULT 0,
    last_ignored_count INT NOT NULL DEFAULT 0,
    last_deleted_count INT NOT NULL DEFAULT 0,
    last_indexed_count INT NOT NULL DEFAULT 0,
    last_error_count INT NOT NULL DEFAULT 0,
    last_error TEXT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_reporting_sync_state_name UNIQUE (sync_name)
);
