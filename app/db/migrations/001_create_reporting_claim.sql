CREATE TABLE reporting_claim (
    id BIGINT NOT NULL AUTO_INCREMENT,
    source_claim_id BIGINT NOT NULL,
    source_code VARCHAR(255),
    client_code VARCHAR(255),
    claim_type VARCHAR(40) NOT NULL,
    status VARCHAR(40),
    category VARCHAR(255),
    motif VARCHAR(255),
    product VARCHAR(255),
    service_point VARCHAR(255),
    agency VARCHAR(255),
    channel VARCHAR(255),
    team VARCHAR(255),
    content TEXT,
    solution TEXT,
    ai_urgency VARCHAR(40),
    ai_sentiment VARCHAR(40),
    risk_level VARCHAR(40),
    ai_risk_score DOUBLE,
    ai_summary TEXT,
    created_at DATETIME,
    receipt_at DATETIME,
    source_updated_at DATETIME,
    affected_at DATETIME,
    resolved_at DATETIME,
    sla_due_at DATETIME,
    satisfaction_status VARCHAR(40),
    synced_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_reporting_claim_source_id UNIQUE (source_claim_id)
);

CREATE INDEX ix_reporting_claim_source_updated_at ON reporting_claim (source_updated_at);
CREATE INDEX ix_reporting_claim_created_at ON reporting_claim (created_at);
CREATE INDEX ix_reporting_claim_claim_type ON reporting_claim (claim_type);
CREATE INDEX ix_reporting_claim_status ON reporting_claim (status);
CREATE INDEX ix_reporting_claim_category ON reporting_claim (category);
CREATE INDEX ix_reporting_claim_agency ON reporting_claim (agency);
CREATE INDEX ix_reporting_claim_channel ON reporting_claim (channel);
CREATE INDEX ix_reporting_claim_risk_level ON reporting_claim (risk_level);
