CREATE TABLE reporting_alert (
    id BIGINT NOT NULL AUTO_INCREMENT,
    source_key VARCHAR(150) NOT NULL,
    alert_type VARCHAR(80) NOT NULL,
    severity VARCHAR(30) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    subtitle TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'new',
    owner VARCHAR(255),
    detected_at DATETIME NOT NULL,
    resolved_at DATETIME,
    source_rule VARCHAR(100) NOT NULL,
    action TEXT,
    evidence TEXT,
    PRIMARY KEY (id),
    CONSTRAINT uq_reporting_alert_source_key UNIQUE (source_key)
);

CREATE INDEX ix_reporting_alert_status ON reporting_alert (status);
CREATE INDEX ix_reporting_alert_detected_at ON reporting_alert (detected_at);
