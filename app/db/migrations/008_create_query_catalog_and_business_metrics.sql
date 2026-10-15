-- =============================================================================
-- Migration 008 : Tables de Persistance Catalogue de Requêtes & Métriques Métier
-- Description : Crée reporting_certified_queries et reporting_business_metrics
--               pour le stockage durable, Fast-Path et gouvernance MySQL.
-- =============================================================================

-- 1. Table des Requêtes Certifiées et Candidates (reporting_certified_queries)
CREATE TABLE IF NOT EXISTS reporting_certified_queries (
    id VARCHAR(64) NOT NULL,
    contract_version VARCHAR(16) NOT NULL DEFAULT '1.0',
    natural_language_query TEXT NOT NULL,
    canonical_intent JSON NOT NULL,
    intent_hash VARCHAR(32) NULL,
    parameterized_sql TEXT NOT NULL,
    parameters_schema JSON NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'APPROVED',
    created_by VARCHAR(100) NOT NULL DEFAULT 'system',
    approved_by VARCHAR(100) NULL,
    approved_at DATETIME NULL,
    approval_comment TEXT NULL,
    rejection_reason TEXT NULL,
    deprecation_reason TEXT NULL,
    schema_version VARCHAR(32) NOT NULL DEFAULT '1.0.0',
    execution_count INT NOT NULL DEFAULT 0,
    avg_execution_time_ms FLOAT NULL,
    last_executed_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX ix_certified_queries_intent_hash (intent_hash),
    INDEX ix_certified_queries_status (status),
    INDEX ix_certified_queries_schema_version (schema_version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Table des Métriques Métier (reporting_business_metrics)
CREATE TABLE IF NOT EXISTS reporting_business_metrics (
    metric_id VARCHAR(64) NOT NULL,
    label VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    target_concept VARCHAR(64) NOT NULL DEFAULT 'plainte',
    required_tables JSON NOT NULL,
    aggregation_sql_template TEXT NOT NULL,
    is_custom BOOLEAN NOT NULL DEFAULT FALSE,
    created_by VARCHAR(100) NOT NULL DEFAULT 'system',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (metric_id),
    INDEX ix_business_metrics_target_concept (target_concept)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
