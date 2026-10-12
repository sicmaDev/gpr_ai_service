-- =============================================================================
-- Migration 007 : Modèle Relationnel Complet gpr_ai_reporting (Step 1)
-- Description : Crée les 10 tables de dimensions, workflows et référentiels
--               ajoute les clés étrangères sur reporting_claim
--               et effectue le rapprochement automatique des données existantes.
-- =============================================================================

-- 1. Table des Postes et Rôles (reporting_poste)
CREATE TABLE IF NOT EXISTS reporting_poste (
    id BIGINT NOT NULL AUTO_INCREMENT,
    libelle VARCHAR(255) NOT NULL,
    description TEXT,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Table des Agences et Points de Service (reporting_service_point)
CREATE TABLE IF NOT EXISTS reporting_service_point (
    id BIGINT NOT NULL AUTO_INCREMENT,
    libelle VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    type VARCHAR(50) DEFAULT 'AGENCE',
    is_principal_agence BOOLEAN DEFAULT FALSE,
    direction_id BIGINT NULL,
    PRIMARY KEY (id),
    INDEX ix_reporting_sp_libelle (libelle)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Table des Canaux de Collecte (reporting_collection_channel)
CREATE TABLE IF NOT EXISTS reporting_collection_channel (
    id BIGINT NOT NULL AUTO_INCREMENT,
    libelle VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    PRIMARY KEY (id),
    INDEX ix_reporting_cc_libelle (libelle)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Table des Produits et Services Bancaires (reporting_product)
CREATE TABLE IF NOT EXISTS reporting_product (
    id BIGINT NOT NULL AUTO_INCREMENT,
    libelle VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    is_deleted BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (id),
    INDEX ix_reporting_prod_libelle (libelle)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Table des Catégories de Motifs (reporting_categorie_objet)
CREATE TABLE IF NOT EXISTS reporting_categorie_objet (
    id BIGINT NOT NULL AUTO_INCREMENT,
    libelle VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    PRIMARY KEY (id),
    INDEX ix_reporting_cat_libelle (libelle)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Table des Motifs et Objets avec SLA (reporting_objet)
CREATE TABLE IF NOT EXISTS reporting_objet (
    id BIGINT NOT NULL AUTO_INCREMENT,
    categorie_id BIGINT NULL,
    libelle VARCHAR(255) NOT NULL,
    risque_level VARCHAR(40) NULL,
    processing_time INT DEFAULT 2,
    PRIMARY KEY (id),
    INDEX ix_reporting_obj_libelle (libelle),
    INDEX ix_reporting_obj_categorie (categorie_id),
    CONSTRAINT fk_reporting_objet_categorie FOREIGN KEY (categorie_id) 
        REFERENCES reporting_categorie_objet(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Base de Connaissances des Solutions Types (reporting_existing_solution)
CREATE TABLE IF NOT EXISTS reporting_existing_solution (
    id BIGINT NOT NULL AUTO_INCREMENT,
    objet_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    compteur BIGINT DEFAULT 0,
    PRIMARY KEY (id),
    CONSTRAINT fk_reporting_existing_sol_objet FOREIGN KEY (objet_id) 
        REFERENCES reporting_objet(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Table des Utilisateurs et Agents Internes (reporting_user)
CREATE TABLE IF NOT EXISTS reporting_user (
    id BIGINT NOT NULL AUTO_INCREMENT,
    code VARCHAR(100) UNIQUE,
    firstandlastname VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    additionalrole VARCHAR(255),
    service_point_id BIGINT NULL,
    poste_id BIGINT NULL,
    PRIMARY KEY (id),
    INDEX ix_reporting_user_code (code),
    INDEX ix_reporting_user_email (email),
    CONSTRAINT fk_reporting_user_service_point FOREIGN KEY (service_point_id) 
        REFERENCES reporting_service_point(id) ON DELETE SET NULL,
    CONSTRAINT fk_reporting_user_poste FOREIGN KEY (poste_id) 
        REFERENCES reporting_poste(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 9. Évolution de la Table Pivot Centrale : reporting_claim
-- =============================================================================

SET @dbname = DATABASE();
SET @tablename = "reporting_claim";

-- Colonne objet_id
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = "objet_id") > 0,
  "SELECT 1",
  "ALTER TABLE reporting_claim ADD COLUMN objet_id BIGINT NULL, ADD INDEX ix_reporting_claim_objet_id (objet_id)"
));
PREPARE stmt FROM @preparedStatement; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Colonne product_id
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = "product_id") > 0,
  "SELECT 1",
  "ALTER TABLE reporting_claim ADD COLUMN product_id BIGINT NULL, ADD INDEX ix_reporting_claim_product_id (product_id)"
));
PREPARE stmt FROM @preparedStatement; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Colonne service_point_id
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = "service_point_id") > 0,
  "SELECT 1",
  "ALTER TABLE reporting_claim ADD COLUMN service_point_id BIGINT NULL, ADD INDEX ix_reporting_claim_service_point_id (service_point_id)"
));
PREPARE stmt FROM @preparedStatement; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Colonne collection_channel_id
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = "collection_channel_id") > 0,
  "SELECT 1",
  "ALTER TABLE reporting_claim ADD COLUMN collection_channel_id BIGINT NULL, ADD INDEX ix_reporting_claim_collection_channel_id (collection_channel_id)"
));
PREPARE stmt FROM @preparedStatement; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Colonne collector_id
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = "collector_id") > 0,
  "SELECT 1",
  "ALTER TABLE reporting_claim ADD COLUMN collector_id BIGINT NULL, ADD INDEX ix_reporting_claim_collector_id (collector_id)"
));
PREPARE stmt FROM @preparedStatement; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- =============================================================================
-- 10. Table des Suggestions (reporting_suggestion)
-- =============================================================================
CREATE TABLE IF NOT EXISTS reporting_suggestion (
    id BIGINT NOT NULL AUTO_INCREMENT,
    source_suggestion_id BIGINT NOT NULL,
    reference VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    client_code VARCHAR(255),
    client_name VARCHAR(255),
    phone VARCHAR(255),
    email VARCHAR(255),
    channel VARCHAR(255),
    status VARCHAR(40) NOT NULL,
    impact_level VARCHAR(40),
    origine VARCHAR(100),
    objet_id BIGINT NULL,
    product_id BIGINT NULL,
    service_point_id BIGINT NULL,
    collection_channel_id BIGINT NULL,
    enregistre_par_id BIGINT NULL,
    evaluator_notes TEXT,
    recorded_at DATE NOT NULL,
    created_at DATETIME,
    updated_at DATETIME,
    synced_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_reporting_suggestion_source_id UNIQUE (source_suggestion_id),
    INDEX ix_reporting_suggestion_status (status),
    INDEX ix_reporting_suggestion_impact_level (impact_level),
    INDEX ix_reporting_suggestion_recorded_at (recorded_at),
    CONSTRAINT fk_reporting_suggestion_objet FOREIGN KEY (objet_id) 
        REFERENCES reporting_objet(id) ON DELETE SET NULL,
    CONSTRAINT fk_reporting_suggestion_product FOREIGN KEY (product_id) 
        REFERENCES reporting_product(id) ON DELETE SET NULL,
    CONSTRAINT fk_reporting_suggestion_service_point FOREIGN KEY (service_point_id) 
        REFERENCES reporting_service_point(id) ON DELETE SET NULL,
    CONSTRAINT fk_reporting_suggestion_channel FOREIGN KEY (collection_channel_id) 
        REFERENCES reporting_collection_channel(id) ON DELETE SET NULL,
    CONSTRAINT fk_reporting_suggestion_enregistre_par FOREIGN KEY (enregistre_par_id) 
        REFERENCES reporting_user(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 11. Table du Workflow d'Affectations (reporting_historique_affectations)
-- =============================================================================
CREATE TABLE IF NOT EXISTS reporting_historique_affectations (
    id BIGINT NOT NULL AUTO_INCREMENT,
    reclamation_id BIGINT NULL,
    suggestion_id BIGINT NULL,
    code_plainte VARCHAR(255),
    type_plainte VARCHAR(40),
    nom_agent VARCHAR(255),
    email_agent VARCHAR(255),
    affecteur_id BIGINT NULL,
    nom_affecteur VARCHAR(255),
    email_affecteur VARCHAR(255),
    date_affectation DATETIME NOT NULL,
    delai_jours INT DEFAULT 2,
    date_fin_affectation DATETIME NULL,
    affectation_precedente_id BIGINT NULL,
    last_notification DATETIME NULL,
    mail_envoye BOOLEAN DEFAULT FALSE,
    sms_envoye BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (id),
    INDEX ix_reporting_hist_aff_date (date_affectation),
    INDEX ix_reporting_hist_aff_prev (affectation_precedente_id),
    CONSTRAINT fk_reporting_hist_aff_rec FOREIGN KEY (reclamation_id) 
        REFERENCES reporting_claim(id) ON DELETE CASCADE,
    CONSTRAINT fk_reporting_hist_aff_sug FOREIGN KEY (suggestion_id) 
        REFERENCES reporting_suggestion(id) ON DELETE CASCADE,
    CONSTRAINT fk_reporting_hist_aff_affecteur FOREIGN KEY (affecteur_id) 
        REFERENCES reporting_user(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 12. Table des Solutions Proposées (reporting_solution)
-- =============================================================================
CREATE TABLE IF NOT EXISTS reporting_solution (
    id BIGINT NOT NULL AUTO_INCREMENT,
    claim_id BIGINT NOT NULL,
    author_id BIGINT NULL,
    status VARCHAR(40) NOT NULL,
    commentaire TEXT,
    motif_desaprobation TEXT,
    approver_id BIGINT NULL,
    approved_at DATETIME NULL,
    unapproved_at DATETIME NULL,
    is_ai_proposed BOOLEAN DEFAULT FALSE,
    ai_selected_solution TEXT,
    PRIMARY KEY (id),
    INDEX ix_reporting_solution_status (status),
    CONSTRAINT fk_reporting_solution_claim FOREIGN KEY (claim_id) 
        REFERENCES reporting_claim(id) ON DELETE CASCADE,
    CONSTRAINT fk_reporting_solution_author FOREIGN KEY (author_id) 
        REFERENCES reporting_user(id) ON DELETE SET NULL,
    CONSTRAINT fk_reporting_solution_approver FOREIGN KEY (approver_id) 
        REFERENCES reporting_user(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 13. Table des Mesures de Satisfaction (reporting_satisfaction_measure)
-- =============================================================================
CREATE TABLE IF NOT EXISTS reporting_satisfaction_measure (
    id BIGINT NOT NULL AUTO_INCREMENT,
    solution_id BIGINT NOT NULL,
    measurer_id BIGINT NULL,
    status VARCHAR(40) NOT NULL,
    commentaire TEXT,
    measure_date_time DATETIME NOT NULL,
    PRIMARY KEY (id),
    INDEX ix_reporting_sat_status (status),
    INDEX ix_reporting_sat_date (measure_date_time),
    CONSTRAINT fk_reporting_sat_solution FOREIGN KEY (solution_id) 
        REFERENCES reporting_solution(id) ON DELETE CASCADE,
    CONSTRAINT fk_reporting_sat_measurer FOREIGN KEY (measurer_id) 
        REFERENCES reporting_user(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 14. Rapprochement Automatique des Données Existantes (Backfill Idempotent)
-- =============================================================================

-- Alimentation des agences existantes dans reporting_service_point
INSERT IGNORE INTO reporting_service_point (libelle, type, is_principal_agence)
SELECT DISTINCT agency, 'AGENCE', FALSE 
FROM reporting_claim 
WHERE agency IS NOT NULL AND agency != '';

-- Rapprochement de service_point_id sur reporting_claim
UPDATE reporting_claim c
JOIN reporting_service_point sp ON c.agency = sp.libelle
SET c.service_point_id = sp.id
WHERE c.service_point_id IS NULL;

-- Alimentation des canaux existants dans reporting_collection_channel
INSERT IGNORE INTO reporting_collection_channel (libelle)
SELECT DISTINCT channel 
FROM reporting_claim 
WHERE channel IS NOT NULL AND channel != '';

-- Rapprochement de collection_channel_id sur reporting_claim
UPDATE reporting_claim c
JOIN reporting_collection_channel cc ON c.channel = cc.libelle
SET c.collection_channel_id = cc.id
WHERE c.collection_channel_id IS NULL;

-- Alimentation des produits existants dans reporting_product
INSERT IGNORE INTO reporting_product (libelle)
SELECT DISTINCT product 
FROM reporting_claim 
WHERE product IS NOT NULL AND product != '';

-- Rapprochement de product_id sur reporting_claim
UPDATE reporting_claim c
JOIN reporting_product p ON c.product = p.libelle
SET c.product_id = p.id
WHERE c.product_id IS NULL;

-- Alimentation des catégories existantes dans reporting_categorie_objet
INSERT IGNORE INTO reporting_categorie_objet (libelle)
SELECT DISTINCT category 
FROM reporting_claim 
WHERE category IS NOT NULL AND category != '';

-- Alimentation des motifs existants dans reporting_objet
INSERT IGNORE INTO reporting_objet (libelle, categorie_id, risque_level)
SELECT DISTINCT c.motif, cat.id, c.risk_level
FROM reporting_claim c
LEFT JOIN reporting_categorie_objet cat ON c.category = cat.libelle
WHERE c.motif IS NOT NULL AND c.motif != '';

-- Rapprochement de objet_id sur reporting_claim
UPDATE reporting_claim c
JOIN reporting_objet o ON c.motif = o.libelle
SET c.objet_id = o.id
WHERE c.objet_id IS NULL;
