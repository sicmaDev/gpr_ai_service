"""
Catalogue officiel du schéma analytique (Schema Catalog) pour le moteur Text-to-SQL Gouverné.

Ce module matérialise l'inventaire exhaustif de la base gpr_ai_reporting :
- Les 13 tables analytiques et de gestion (tables de faits, workflows, dimensions et administration).
- Le typage SQL strict, les contraintes de clés primaires et étrangères.
- Le marquage impératif de protection des données sensibles (is_sensitive=True).
- Le graphe officiel des relations autorisées pour les jointures sécurisées.
- L'extracteur de sous-schéma minimal garanti sans fuite de données confidentielles.
"""

from typing import Dict, List, Optional

from app.reporting.text_to_sql_contracts import (
    ColumnMetadata,
    RelationshipMetadata,
    SchemaCatalog,
    TableMetadata,
)

# -----------------------------------------------------------------------------
# DÉFINITION DES TABLES DU SCHEMA CATALOG
# -----------------------------------------------------------------------------

_TABLES: Dict[str, TableMetadata] = {
    # 1. Table Pivot Centrale : reporting_claim (Réclamations & Dénonciations)
    "reporting_claim": TableMetadata(
        name="reporting_claim",
        table_type="fact",
        primary_key="id",
        description="Table pivot centrale regroupant les réclamations et dénonciations opérationnelles (hors brouillons).",
        columns={
            "id": ColumnMetadata(
                name="id",
                data_type="BIGINT",
                is_primary_key=True,
                is_nullable=False,
                is_indexed=True,
                description="Identifiant technique unique interne au reporting.",
            ),
            "source_claim_id": ColumnMetadata(
                name="source_claim_id",
                data_type="BIGINT",
                is_nullable=False,
                is_indexed=True,
                description="Identifiant unique d'origine dans la base opérationnelle.",
            ),
            "source_code": ColumnMetadata(
                name="source_code",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Référence métier lisible du dossier (ex: REC-2026-001, DEN-2026-001).",
            ),
            "client_code": ColumnMetadata(
                name="client_code",
                data_type="VARCHAR",
                is_nullable=True,
                is_sensitive=True,
                description="Code client bancaire nominatif (DONNÉE SENSIBLE - EXCLUSION ABSOLUE).",
            ),
            "claim_type": ColumnMetadata(
                name="claim_type",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Type de dossier : 'CLAIM' (Réclamation) ou 'DENUNCIATION' (Dénonciation).",
            ),
            "status": ColumnMetadata(
                name="status",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Statut opérationnel du cycle de vie (ex: SAVED, AFFECTED, TREAT, SATISFIED).",
            ),
            "objet_id": ColumnMetadata(
                name="objet_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_objet",
                references_column="id",
                is_nullable=True,
                is_indexed=True,
                description="Clé étrangère vers le motif / objet précis du dossier.",
            ),
            "product_id": ColumnMetadata(
                name="product_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_product",
                references_column="id",
                is_nullable=True,
                is_indexed=True,
                description="Clé étrangère vers le produit bancaire concerné.",
            ),
            "service_point_id": ColumnMetadata(
                name="service_point_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_service_point",
                references_column="id",
                is_nullable=True,
                is_indexed=True,
                description="Clé étrangère vers l'agence ou point de service rattaché.",
            ),
            "collection_channel_id": ColumnMetadata(
                name="collection_channel_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_collection_channel",
                references_column="id",
                is_nullable=True,
                is_indexed=True,
                description="Clé étrangère vers le canal d'entrée / collecte.",
            ),
            "collector_id": ColumnMetadata(
                name="collector_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_user",
                references_column="id",
                is_nullable=True,
                is_indexed=True,
                description="Clé étrangère vers l'agent ayant enregistré le dossier.",
            ),
            "content": ColumnMetadata(
                name="content",
                data_type="TEXT",
                is_nullable=True,
                is_sensitive=True,
                description="Contenu brut saisi ou transcrit (DONNÉE SENSIBLE - EXCLUSION ABSOLUE).",
            ),
            "solution": ColumnMetadata(
                name="solution",
                data_type="TEXT",
                is_nullable=True,
                is_sensitive=True,
                description="Texte de la solution finale retenue (DONNÉE SENSIBLE - EXCLUSION ABSOLUE).",
            ),
            "ai_urgency": ColumnMetadata(
                name="ai_urgency",
                data_type="VARCHAR",
                is_nullable=True,
                is_indexed=True,
                description="Gravité ou urgence détectée par l'IA : 'MINEUR', 'MOYEN', 'GRAVE'.",
            ),
            "ai_sentiment": ColumnMetadata(
                name="ai_sentiment",
                data_type="VARCHAR",
                is_nullable=True,
                description="Tonalité émotionnelle détectée : 'neutre', 'negatif', 'tres_negatif'.",
            ),
            "risk_level": ColumnMetadata(
                name="risk_level",
                data_type="VARCHAR",
                is_nullable=True,
                is_indexed=True,
                description="Niveau de risque réglementaire / conformité.",
            ),
            "ai_risk_score": ColumnMetadata(
                name="ai_risk_score",
                data_type="DOUBLE",
                is_nullable=True,
                description="Score numérique de risque calculé de 0.0 à 100.0.",
            ),
            "receipt_at": ColumnMetadata(
                name="receipt_at",
                data_type="DATETIME",
                is_nullable=False,
                is_indexed=True,
                description="Date pivot officielle de réception de la réclamation ou dénonciation.",
            ),
            "created_at": ColumnMetadata(
                name="created_at",
                data_type="DATETIME",
                is_nullable=False,
                is_indexed=True,
                description="Horodatage de création technique dans le système opérationnel.",
            ),
            "source_updated_at": ColumnMetadata(
                name="source_updated_at",
                data_type="DATETIME",
                is_nullable=True,
                is_indexed=True,
                description="Horodatage de dernière mise à jour dans le système opérationnel.",
            ),
            "affected_at": ColumnMetadata(
                name="affected_at",
                data_type="DATETIME",
                is_nullable=True,
                description="Horodatage de la première affectation à un agent traitant.",
            ),
            "resolved_at": ColumnMetadata(
                name="resolved_at",
                data_type="DATETIME",
                is_nullable=True,
                is_indexed=True,
                description="Horodatage de clôture ou résolution effective du dossier.",
            ),
            "sla_due_at": ColumnMetadata(
                name="sla_due_at",
                data_type="DATETIME",
                is_nullable=True,
                is_indexed=True,
                description="Date limite réglementaire SLA calculée pour le traitement.",
            ),
            "satisfaction_status": ColumnMetadata(
                name="satisfaction_status",
                data_type="VARCHAR",
                is_nullable=True,
                is_indexed=True,
                description="Statut final d'évaluation client : 'SATISFIED', 'UNSATISFIED', 'PARTIAL_SATISFIED'.",
            ),
            "synced_at": ColumnMetadata(
                name="synced_at",
                data_type="DATETIME",
                is_nullable=False,
                description="Horodatage de réplication dans la base de reporting analytique.",
            ),
        },
    ),

    # 2. Table des Suggestions : reporting_suggestion
    "reporting_suggestion": TableMetadata(
        name="reporting_suggestion",
        table_type="fact",
        primary_key="id",
        description="Table dédiée aux propositions d'amélioration, idées et retours constructifs.",
        columns={
            "id": ColumnMetadata(
                name="id",
                data_type="BIGINT",
                is_primary_key=True,
                is_nullable=False,
                is_indexed=True,
                description="Identifiant technique unique interne au reporting.",
            ),
            "source_suggestion_id": ColumnMetadata(
                name="source_suggestion_id",
                data_type="BIGINT",
                is_nullable=False,
                is_indexed=True,
                description="Identifiant unique d'origine dans la base opérationnelle.",
            ),
            "reference": ColumnMetadata(
                name="reference",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Numéro de référence officiel de la suggestion (ex: SUG-2026-001).",
            ),
            "title": ColumnMetadata(
                name="title",
                data_type="VARCHAR",
                is_nullable=False,
                description="Titre concis ou intitulé de la suggestion.",
            ),
            "description": ColumnMetadata(
                name="description",
                data_type="TEXT",
                is_nullable=True,
                is_sensitive=True,
                description="Texte narratif détaillé de la proposition (DONNÉE SENSIBLE - EXCLUSION ABSOLUE).",
            ),
            "client_code": ColumnMetadata(
                name="client_code",
                data_type="VARCHAR",
                is_nullable=True,
                is_sensitive=True,
                description="Identifiant client bancaire éventuel (DONNÉE SENSIBLE - EXCLUSION ABSOLUE).",
            ),
            "client_name": ColumnMetadata(
                name="client_name",
                data_type="VARCHAR",
                is_nullable=True,
                is_sensitive=True,
                description="Nom complet du suggérant (DONNÉE SENSIBLE - EXCLUSION ABSOLUE).",
            ),
            "phone": ColumnMetadata(
                name="phone",
                data_type="VARCHAR",
                is_nullable=True,
                is_sensitive=True,
                description="Numéro de téléphone du suggérant (DONNÉE SENSIBLE - EXCLUSION ABSOLUE).",
            ),
            "email": ColumnMetadata(
                name="email",
                data_type="VARCHAR",
                is_nullable=True,
                is_sensitive=True,
                description="Adresse email du suggérant (DONNÉE SENSIBLE - EXCLUSION ABSOLUE).",
            ),
            "channel": ColumnMetadata(
                name="channel",
                data_type="VARCHAR",
                is_nullable=True,
                description="Canal de soumission brut de la suggestion.",
            ),
            "status": ColumnMetadata(
                name="status",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Statut du cycle de vie ('ENREGISTREE', 'EN_COURS_ETUDE', 'ADOPTEE', 'REJETEE', 'CLOTUREE').",
            ),
            "impact_level": ColumnMetadata(
                name="impact_level",
                data_type="VARCHAR",
                is_nullable=True,
                is_indexed=True,
                description="Niveau d'impact attendu : 'FAIBLE', 'MOYEN', 'FORT', 'STRATEGIQUE'.",
            ),
            "origine": ColumnMetadata(
                name="origine",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Origine de la suggestion : 'INTERNE' (agent) ou 'EXTERNE' (public/client).",
            ),
            "objet_id": ColumnMetadata(
                name="objet_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_objet",
                references_column="id",
                is_nullable=True,
                is_indexed=True,
                description="Clé étrangère vers l'objet ou thème ciblé.",
            ),
            "product_id": ColumnMetadata(
                name="product_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_product",
                references_column="id",
                is_nullable=True,
                is_indexed=True,
                description="Clé étrangère vers le produit bancaire concerné.",
            ),
            "service_point_id": ColumnMetadata(
                name="service_point_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_service_point",
                references_column="id",
                is_nullable=True,
                is_indexed=True,
                description="Clé étrangère vers l'agence ou point de service ciblé.",
            ),
            "collection_channel_id": ColumnMetadata(
                name="collection_channel_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_collection_channel",
                references_column="id",
                is_nullable=True,
                is_indexed=True,
                description="Clé étrangère vers le canal normalisé de collecte.",
            ),
            "enregistre_par_id": ColumnMetadata(
                name="enregistre_par_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_user",
                references_column="id",
                is_nullable=True,
                is_indexed=True,
                description="Clé étrangère vers l'utilisateur ayant pris en note la suggestion.",
            ),
            "evaluator_notes": ColumnMetadata(
                name="evaluator_notes",
                data_type="TEXT",
                is_nullable=True,
                is_sensitive=True,
                description="Notes et délibérations internes de l'évaluateur (DONNÉE SENSIBLE - EXCLUSION ABSOLUE).",
            ),
            "motif_rejet_soumission": ColumnMetadata(
                name="motif_rejet_soumission",
                data_type="TEXT",
                is_nullable=True,
                description="Motif technique de rejet issu du filtrage de conformité.",
            ),
            "recorded_at": ColumnMetadata(
                name="recorded_at",
                data_type="DATE",
                is_nullable=False,
                is_indexed=True,
                description="Date pivot officielle d'enregistrement de la suggestion.",
            ),
            "created_at": ColumnMetadata(
                name="created_at",
                data_type="DATETIME",
                is_nullable=False,
                is_indexed=True,
                description="Horodatage de création technique dans le système opérationnel.",
            ),
            "updated_at": ColumnMetadata(
                name="updated_at",
                data_type="DATETIME",
                is_nullable=True,
                is_indexed=True,
                description="Horodatage de dernière mise à jour dans le système opérationnel.",
            ),
            "synced_at": ColumnMetadata(
                name="synced_at",
                data_type="DATETIME",
                is_nullable=False,
                description="Horodatage de réplication dans la base de reporting analytique.",
            ),
        },
    ),

    # 3. Table du Processus d'Affectation : reporting_historique_affectations
    "reporting_historique_affectations": TableMetadata(
        name="reporting_historique_affectations",
        table_type="workflow",
        primary_key="id",
        description="Traçabilité détaillée des affectations et réaffectations successives des dossiers (réclamations et suggestions).",
        columns={
            "id": ColumnMetadata(
                name="id",
                data_type="BIGINT",
                is_primary_key=True,
                is_nullable=False,
                is_indexed=True,
                description="Identifiant unique de la ligne d'affectation.",
            ),
            "reclamation_id": ColumnMetadata(
                name="reclamation_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_claim",
                references_column="source_claim_id",
                is_nullable=True,
                is_indexed=True,
                description="Référence source du dossier réclamation (clé d'affectation XOR).",
            ),
            "suggestion_id": ColumnMetadata(
                name="suggestion_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_suggestion",
                references_column="source_suggestion_id",
                is_nullable=True,
                is_indexed=True,
                description="Référence source de la suggestion (clé d'affectation XOR).",
            ),
            "code_plainte": ColumnMetadata(
                name="code_plainte",
                data_type="VARCHAR",
                is_nullable=True,
                description="Numéro de dossier lisible affecté.",
            ),
            "type_plainte": ColumnMetadata(
                name="type_plainte",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Type du dossier affecté : 'CLAIM', 'DENUNCIATION' ou 'SUGGESTION'.",
            ),
            "nom_agent": ColumnMetadata(
                name="nom_agent",
                data_type="VARCHAR",
                is_nullable=True,
                description="Nom complet de l'agent traitant désigné.",
            ),
            "email_agent": ColumnMetadata(
                name="email_agent",
                data_type="VARCHAR",
                is_nullable=True,
                description="Adresse email professionnelle de l'agent traitant.",
            ),
            "affecteur_id": ColumnMetadata(
                name="affecteur_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_user",
                references_column="id",
                is_nullable=True,
                is_indexed=True,
                description="Clé étrangère vers l'utilisateur ayant procédé à l'affectation.",
            ),
            "nom_affecteur": ColumnMetadata(
                name="nom_affecteur",
                data_type="VARCHAR",
                is_nullable=True,
                description="Nom du gestionnaire ayant ordonné l'affectation.",
            ),
            "email_affecteur": ColumnMetadata(
                name="email_affecteur",
                data_type="VARCHAR",
                is_nullable=True,
                description="Email du gestionnaire ayant ordonné l'affectation.",
            ),
            "date_affectation": ColumnMetadata(
                name="date_affectation",
                data_type="DATETIME",
                is_nullable=False,
                is_indexed=True,
                description="Horodatage auquel l'affectation a été validée.",
            ),
            "delai_jours": ColumnMetadata(
                name="delai_jours",
                data_type="INT",
                is_nullable=True,
                description="Délai contractuel de traitement imparti à l'agent en jours.",
            ),
            "date_fin_affectation": ColumnMetadata(
                name="date_fin_affectation",
                data_type="DATETIME",
                is_nullable=True,
                description="Date limite impartie pour finaliser le traitement.",
            ),
            "affectation_precedente_id": ColumnMetadata(
                name="affectation_precedente_id",
                data_type="BIGINT",
                is_nullable=True,
                is_indexed=True,
                description="Identifiant de l'affectation antérieure en cas de réaffectation (transfert).",
            ),
            "last_notification": ColumnMetadata(
                name="last_notification",
                data_type="DATETIME",
                is_nullable=True,
                description="Date de la dernière notification de rappel adressée à l'agent.",
            ),
            "mail_envoye": ColumnMetadata(
                name="mail_envoye",
                data_type="BOOLEAN",
                is_nullable=False,
                description="Indicateur d'acheminement de la notification email.",
            ),
            "sms_envoye": ColumnMetadata(
                name="sms_envoye",
                data_type="BOOLEAN",
                is_nullable=False,
                description="Indicateur d'acheminement de la notification SMS.",
            ),
        },
    ),

    # 4. Table des Solutions Proposées : reporting_solution
    "reporting_solution": TableMetadata(
        name="reporting_solution",
        table_type="workflow",
        primary_key="id",
        description="Cycle de proposition, validation et approbation managériale des résolutions de réclamations.",
        columns={
            "id": ColumnMetadata(
                name="id",
                data_type="BIGINT",
                is_primary_key=True,
                is_nullable=False,
                is_indexed=True,
                description="Identifiant unique de la solution proposée.",
            ),
            "claim_id": ColumnMetadata(
                name="claim_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_claim",
                references_column="id",
                is_nullable=False,
                is_indexed=True,
                description="Clé étrangère vers la réclamation concernée.",
            ),
            "author_id": ColumnMetadata(
                name="author_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_user",
                references_column="id",
                is_nullable=False,
                is_indexed=True,
                description="Clé étrangère vers l'agent ayant rédigé la solution.",
            ),
            "status": ColumnMetadata(
                name="status",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Statut du cycle de validation ('PENDING', 'VALIDATED', 'REJECTED').",
            ),
            "commentaire": ColumnMetadata(
                name="commentaire",
                data_type="TEXT",
                is_nullable=True,
                is_sensitive=True,
                description="Commentaire interne rédigé par l'agent (DONNÉE SENSIBLE - EXCLUSION ABSOLUE).",
            ),
            "motif_desaprobation": ColumnMetadata(
                name="motif_desaprobation",
                data_type="TEXT",
                is_nullable=True,
                is_sensitive=True,
                description="Motif de refus du superviseur (DONNÉE SENSIBLE - EXCLUSION ABSOLUE).",
            ),
            "approver_id": ColumnMetadata(
                name="approver_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_user",
                references_column="id",
                is_nullable=True,
                is_indexed=True,
                description="Clé étrangère vers le superviseur ayant validé la proposition.",
            ),
            "approved_at": ColumnMetadata(
                name="approved_at",
                data_type="DATETIME",
                is_nullable=True,
                is_indexed=True,
                description="Horodatage d'approbation effective de la solution.",
            ),
            "unapproved_at": ColumnMetadata(
                name="unapproved_at",
                data_type="DATETIME",
                is_nullable=True,
                description="Horodatage de désapprobation ou de rejet de la solution.",
            ),
            "is_ai_proposed": ColumnMetadata(
                name="is_ai_proposed",
                data_type="BOOLEAN",
                is_nullable=False,
                description="Indique si la solution proposée est issue de l'assistance IA.",
            ),
            "ai_selected_solution": ColumnMetadata(
                name="ai_selected_solution",
                data_type="TEXT",
                is_nullable=True,
                is_sensitive=True,
                description="Texte suggéré par l'IA retenu par l'agent (DONNÉE SENSIBLE - EXCLUSION ABSOLUE).",
            ),
        },
    ),

    # 5. Table de Base de Connaissances : reporting_existing_solution
    "reporting_existing_solution": TableMetadata(
        name="reporting_existing_solution",
        table_type="dimension",
        primary_key="id",
        description="Base de connaissances de solutions types et réutilisables indexées par motif.",
        columns={
            "id": ColumnMetadata(
                name="id",
                data_type="BIGINT",
                is_primary_key=True,
                is_nullable=False,
                is_indexed=True,
                description="Identifiant unique de la solution type.",
            ),
            "objet_id": ColumnMetadata(
                name="objet_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_objet",
                references_column="id",
                is_nullable=False,
                is_indexed=True,
                description="Clé étrangère vers le motif associé.",
            ),
            "content": ColumnMetadata(
                name="content",
                data_type="TEXT",
                is_nullable=False,
                description="Contenu modèle de la solution type.",
            ),
            "compteur": ColumnMetadata(
                name="compteur",
                data_type="BIGINT",
                is_nullable=False,
                description="Nombre de réutilisations réelles de ce modèle pour la résolution de dossiers.",
            ),
        },
    ),

    # 6. Table des Mesures de Satisfaction : reporting_satisfaction_measure
    "reporting_satisfaction_measure": TableMetadata(
        name="reporting_satisfaction_measure",
        table_type="workflow",
        primary_key="id",
        description="Enquêtes et mesures de satisfaction client réalisées post-clôture.",
        columns={
            "id": ColumnMetadata(
                name="id",
                data_type="BIGINT",
                is_primary_key=True,
                is_nullable=False,
                is_indexed=True,
                description="Identifiant unique de la mesure de satisfaction.",
            ),
            "solution_id": ColumnMetadata(
                name="solution_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_solution",
                references_column="id",
                is_nullable=False,
                is_indexed=True,
                description="Clé étrangère vers la solution évaluée.",
            ),
            "measurer_id": ColumnMetadata(
                name="measurer_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_user",
                references_column="id",
                is_nullable=False,
                is_indexed=True,
                description="Clé étrangère vers l'agent ayant conduit l'enquête de satisfaction.",
            ),
            "status": ColumnMetadata(
                name="status",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Avis client recueilli : 'SATISFIED', 'UNSATISFIED', 'PARTIAL_SATISFIED'.",
            ),
            "commentaire": ColumnMetadata(
                name="commentaire",
                data_type="TEXT",
                is_nullable=True,
                is_sensitive=True,
                description="Commentaire ou retour textuel libre du client (DONNÉE SENSIBLE - EXCLUSION ABSOLUE).",
            ),
            "measure_date_time": ColumnMetadata(
                name="measure_date_time",
                data_type="DATETIME",
                is_nullable=False,
                is_indexed=True,
                description="Horodatage auquel la mesure de satisfaction a été enregistrée.",
            ),
        },
    ),

    # 7. Table des Produits : reporting_product
    "reporting_product": TableMetadata(
        name="reporting_product",
        table_type="dimension",
        primary_key="id",
        description="Référentiel des produits et services bancaires proposés par l'institution.",
        columns={
            "id": ColumnMetadata(
                name="id",
                data_type="BIGINT",
                is_primary_key=True,
                is_nullable=False,
                is_indexed=True,
                description="Identifiant unique du produit bancaire.",
            ),
            "libelle": ColumnMetadata(
                name="libelle",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Nom commercial officiel du produit bancaire.",
            ),
            "description": ColumnMetadata(
                name="description",
                data_type="TEXT",
                is_nullable=True,
                description="Description détaillée des caractéristiques du produit.",
            ),
            "is_deleted": ColumnMetadata(
                name="is_deleted",
                data_type="BOOLEAN",
                is_nullable=False,
                description="Indicateur d'archivage ou de suppression logique du produit.",
            ),
        },
    ),

    # 8. Table des Agences : reporting_service_point
    "reporting_service_point": TableMetadata(
        name="reporting_service_point",
        table_type="dimension",
        primary_key="id",
        description="Réseau physique et organisationnel des agences, guichets et directions.",
        columns={
            "id": ColumnMetadata(
                name="id",
                data_type="BIGINT",
                is_primary_key=True,
                is_nullable=False,
                is_indexed=True,
                description="Identifiant unique du point de service.",
            ),
            "libelle": ColumnMetadata(
                name="libelle",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Nom officiel de l'agence ou du point de service.",
            ),
            "description": ColumnMetadata(
                name="description",
                data_type="TEXT",
                is_nullable=True,
                description="Informations de localisation ou précisions sur l'agence.",
            ),
            "type": ColumnMetadata(
                name="type",
                data_type="VARCHAR",
                is_nullable=False,
                description="Type d'entité : 'AGENCE', 'GUICHET', 'SIEGE', 'DIRECTION'.",
            ),
            "is_principal_agence": ColumnMetadata(
                name="is_principal_agence",
                data_type="BOOLEAN",
                is_nullable=False,
                description="Indicateur si l'agence est un centre principal.",
            ),
            "direction_id": ColumnMetadata(
                name="direction_id",
                data_type="BIGINT",
                is_nullable=True,
                description="Identifiant technique de la direction régionale de rattachement.",
            ),
        },
    ),

    # 9. Table des Catégories de Motif : reporting_categorie_objet
    "reporting_categorie_objet": TableMetadata(
        name="reporting_categorie_objet",
        table_type="dimension",
        primary_key="id",
        description="Grandes familles ou typologies catégorielles regroupant les motifs de doléances.",
        columns={
            "id": ColumnMetadata(
                name="id",
                data_type="BIGINT",
                is_primary_key=True,
                is_nullable=False,
                is_indexed=True,
                description="Identifiant unique de la catégorie d'objet.",
            ),
            "libelle": ColumnMetadata(
                name="libelle",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Intitulé de la catégorie (ex: Carte bancaire, Crédit, Virement, Qualité d'accueil).",
            ),
            "description": ColumnMetadata(
                name="description",
                data_type="TEXT",
                is_nullable=True,
                description="Description du périmètre couvert par la catégorie.",
            ),
        },
    ),

    # 10. Table des Objets / Motifs : reporting_objet
    "reporting_objet": TableMetadata(
        name="reporting_objet",
        table_type="dimension",
        primary_key="id",
        description="Motifs précis de dossiers, portant les niveaux de risque et délais SLA réglementaires.",
        columns={
            "id": ColumnMetadata(
                name="id",
                data_type="BIGINT",
                is_primary_key=True,
                is_nullable=False,
                is_indexed=True,
                description="Identifiant unique du motif.",
            ),
            "categorie_id": ColumnMetadata(
                name="categorie_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_categorie_objet",
                references_column="id",
                is_nullable=False,
                is_indexed=True,
                description="Clé étrangère vers la catégorie chapeau parente.",
            ),
            "libelle": ColumnMetadata(
                name="libelle",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Libellé précis du motif (ex: Capture de carte DAB, Erreur de débit compte).",
            ),
            "risque_level": ColumnMetadata(
                name="risque_level",
                data_type="VARCHAR",
                is_nullable=False,
                description="Niveau de risque intrinsèque du motif : 'MINEUR', 'MOYEN', 'GRAVE'.",
            ),
            "processing_time": ColumnMetadata(
                name="processing_time",
                data_type="INT",
                is_nullable=False,
                description="Délai contractuel de traitement réglementaire (SLA) en jours ouvrés.",
            ),
        },
    ),

    # 11. Table des Canaux de Collecte : reporting_collection_channel
    "reporting_collection_channel": TableMetadata(
        name="reporting_collection_channel",
        table_type="dimension",
        primary_key="id",
        description="Canaux de collecte et voies d'entrée des dossiers (ex: Web, Agence, WhatsApp, Téléphone).",
        columns={
            "id": ColumnMetadata(
                name="id",
                data_type="BIGINT",
                is_primary_key=True,
                is_nullable=False,
                is_indexed=True,
                description="Identifiant unique du canal de collecte.",
            ),
            "libelle": ColumnMetadata(
                name="libelle",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Nom du canal : 'WEB', 'AGENCE', 'WHATSAPP', 'COURRIER', 'TELEPHONE'.",
            ),
            "description": ColumnMetadata(
                name="description",
                data_type="TEXT",
                is_nullable=True,
                description="Description opérationnelle du canal de réception.",
            ),
        },
    ),

    # 12. Table des Utilisateurs : reporting_user
    "reporting_user": TableMetadata(
        name="reporting_user",
        table_type="dimension",
        primary_key="id",
        description="Référentiel des agents, superviseurs et gestionnaires (sans données sensibles d'authentification).",
        columns={
            "id": ColumnMetadata(
                name="id",
                data_type="BIGINT",
                is_primary_key=True,
                is_nullable=False,
                is_indexed=True,
                description="Identifiant unique de l'utilisateur.",
            ),
            "code": ColumnMetadata(
                name="code",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Matricule professionnel ou code agent.",
            ),
            "firstandlastname": ColumnMetadata(
                name="firstandlastname",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Nom et prénom complets de l'agent.",
            ),
            "email": ColumnMetadata(
                name="email",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Adresse email professionnelle.",
            ),
            "additionalrole": ColumnMetadata(
                name="additionalrole",
                data_type="VARCHAR",
                is_nullable=True,
                description="Rôle additionnel ou privilège attribué.",
            ),
            "service_point_id": ColumnMetadata(
                name="service_point_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_service_point",
                references_column="id",
                is_nullable=True,
                is_indexed=True,
                description="Clé étrangère vers l'agence d'affectation de l'agent.",
            ),
            "poste_id": ColumnMetadata(
                name="poste_id",
                data_type="BIGINT",
                is_foreign_key=True,
                references_table="reporting_poste",
                references_column="id",
                is_nullable=True,
                is_indexed=True,
                description="Clé étrangère vers le poste occupé par l'agent.",
            ),
        },
    ),

    # 13. Table des Postes : reporting_poste
    "reporting_poste": TableMetadata(
        name="reporting_poste",
        table_type="dimension",
        primary_key="id",
        description="Référentiel des fonctions et postes organisationnels occupés par les agents.",
        columns={
            "id": ColumnMetadata(
                name="id",
                data_type="BIGINT",
                is_primary_key=True,
                is_nullable=False,
                is_indexed=True,
                description="Identifiant unique du poste.",
            ),
            "libelle": ColumnMetadata(
                name="libelle",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Intitulé du poste (ex: Chargé de clientèle, Chef d'agence, Auditeur).",
            ),
            "description": ColumnMetadata(
                name="description",
                data_type="TEXT",
                is_nullable=True,
                description="Description synthétique des responsabilités du poste.",
            ),
        },
    ),

    # Tables d'administration (types admin, exclues des requêtes métiers directes)
    "reporting_sync_state": TableMetadata(
        name="reporting_sync_state",
        table_type="admin",
        primary_key="id",
        description="Suivi technique des synchronisations incrémentales entre bases opérationnelle et reporting.",
        columns={
            "id": ColumnMetadata(
                name="id",
                data_type="BIGINT",
                is_primary_key=True,
                is_nullable=False,
                is_indexed=True,
                description="Identifiant technique du curseur de synchronisation.",
            ),
            "sync_name": ColumnMetadata(
                name="sync_name",
                data_type="VARCHAR",
                is_nullable=False,
                is_indexed=True,
                description="Nom du flux de synchronisation (ex: sync_claims, sync_suggestions).",
            ),
            "last_successful_sync_at": ColumnMetadata(
                name="last_successful_sync_at",
                data_type="DATETIME",
                is_nullable=True,
                description="Horodatage de la dernière réplication complétée avec succès.",
            ),
            "records_synced": ColumnMetadata(
                name="records_synced",
                data_type="INT",
                is_nullable=False,
                description="Nombre de lignes traitées lors de la dernière exécution.",
            ),
        },
    ),

    "reporting_alert": TableMetadata(
        name="reporting_alert",
        table_type="admin",
        primary_key="id",
        description="Alertes et anomalies de cohérence détectées lors des synchronisations de données.",
        columns={
            "id": ColumnMetadata(
                name="id",
                data_type="BIGINT",
                is_primary_key=True,
                is_nullable=False,
                is_indexed=True,
                description="Identifiant unique de l'anomalie détectée.",
            ),
            "source_key": ColumnMetadata(
                name="source_key",
                data_type="VARCHAR",
                is_nullable=False,
                description="Référence de l'enregistrement source ayant généré l'anomalie.",
            ),
            "alert_type": ColumnMetadata(
                name="alert_type",
                data_type="VARCHAR",
                is_nullable=False,
                description="Type d'alerte : SLA_BREACH, INTEGRITY_ERROR, UNKNOWN_STATUS.",
            ),
            "severity": ColumnMetadata(
                name="severity",
                data_type="VARCHAR",
                is_nullable=False,
                description="Gravité technique : INFO, WARNING, CRITICAL.",
            ),
            "status": ColumnMetadata(
                name="status",
                data_type="VARCHAR",
                is_nullable=False,
                description="Statut de prise en charge : OPEN, RESOLVED, DISMISSED.",
            ),
            "detected_at": ColumnMetadata(
                name="detected_at",
                data_type="DATETIME",
                is_nullable=False,
                description="Horodatage de détection de l'alerte.",
            ),
        },
    ),
}

# -----------------------------------------------------------------------------
# GRAPHES DES RELATIONS OFFICIELLES (JOINTURES AUTORISÉES)
# -----------------------------------------------------------------------------

_RELATIONSHIPS: List[RelationshipMetadata] = [
    # Jointures réclamations vers référentiels
    RelationshipMetadata(
        name="claim_to_agency",
        source_table="reporting_claim",
        source_column="service_point_id",
        target_table="reporting_service_point",
        target_column="id",
        join_type="LEFT JOIN",
        description="Liaison de la réclamation/dénonciation vers son agence bancaire de rattachement.",
    ),
    RelationshipMetadata(
        name="claim_to_channel",
        source_table="reporting_claim",
        source_column="collection_channel_id",
        target_table="reporting_collection_channel",
        target_column="id",
        join_type="LEFT JOIN",
        description="Liaison de la réclamation/dénonciation vers son canal d'entrée de collecte.",
    ),
    RelationshipMetadata(
        name="claim_to_product",
        source_table="reporting_claim",
        source_column="product_id",
        target_table="reporting_product",
        target_column="id",
        join_type="LEFT JOIN",
        description="Liaison de la réclamation vers le produit bancaire concerné.",
    ),
    RelationshipMetadata(
        name="claim_to_object",
        source_table="reporting_claim",
        source_column="objet_id",
        target_table="reporting_objet",
        target_column="id",
        join_type="LEFT JOIN",
        description="Liaison de la réclamation vers le motif d'objet précis et son délai SLA.",
    ),
    RelationshipMetadata(
        name="object_to_category",
        source_table="reporting_objet",
        source_column="categorie_id",
        target_table="reporting_categorie_objet",
        target_column="id",
        join_type="LEFT JOIN",
        description="Liaison du motif vers sa catégorie ou famille fonctionnelle.",
    ),

    # Jointures suggestions vers référentiels
    RelationshipMetadata(
        name="suggestion_to_agency",
        source_table="reporting_suggestion",
        source_column="service_point_id",
        target_table="reporting_service_point",
        target_column="id",
        join_type="LEFT JOIN",
        description="Liaison de la suggestion vers l'agence ciblée par la proposition.",
    ),
    RelationshipMetadata(
        name="suggestion_to_channel",
        source_table="reporting_suggestion",
        source_column="collection_channel_id",
        target_table="reporting_collection_channel",
        target_column="id",
        join_type="LEFT JOIN",
        description="Liaison de la suggestion vers son canal de réception.",
    ),
    RelationshipMetadata(
        name="suggestion_to_product",
        source_table="reporting_suggestion",
        source_column="product_id",
        target_table="reporting_product",
        target_column="id",
        join_type="LEFT JOIN",
        description="Liaison de la suggestion vers le produit ou service bancaire suggéré.",
    ),
    RelationshipMetadata(
        name="suggestion_to_object",
        source_table="reporting_suggestion",
        source_column="objet_id",
        target_table="reporting_objet",
        target_column="id",
        join_type="LEFT JOIN",
        description="Liaison de la suggestion vers la thématique ou motif associé.",
    ),

    # Traçabilité et historique d'affectation
    RelationshipMetadata(
        name="claim_to_affectations",
        source_table="reporting_claim",
        source_column="source_claim_id",
        target_table="reporting_historique_affectations",
        target_column="reclamation_id",
        join_type="LEFT JOIN",
        description="Liaison de la réclamation vers l'historique de ses affectations et réaffectations.",
    ),
    RelationshipMetadata(
        name="suggestion_to_affectations",
        source_table="reporting_suggestion",
        source_column="source_suggestion_id",
        target_table="reporting_historique_affectations",
        target_column="suggestion_id",
        join_type="LEFT JOIN",
        description="Liaison de la suggestion vers l'historique de ses affectations de traitement.",
    ),

    # Processus de résolution et satisfaction
    RelationshipMetadata(
        name="claim_to_solutions",
        source_table="reporting_claim",
        source_column="id",
        target_table="reporting_solution",
        target_column="claim_id",
        join_type="LEFT JOIN",
        description="Liaison de la réclamation vers les propositions de solution soumises.",
    ),
    RelationshipMetadata(
        name="solution_to_satisfaction",
        source_table="reporting_solution",
        source_column="id",
        target_table="reporting_satisfaction_measure",
        target_column="solution_id",
        join_type="LEFT JOIN",
        description="Liaison de la solution validée vers son évaluation de satisfaction client.",
    ),

    # Organisation des utilisateurs et postes
    RelationshipMetadata(
        name="user_to_service_point",
        source_table="reporting_user",
        source_column="service_point_id",
        target_table="reporting_service_point",
        target_column="id",
        join_type="LEFT JOIN",
        description="Liaison de l'agent vers son agence bancaire de rattachement.",
    ),
    RelationshipMetadata(
        name="user_to_poste",
        source_table="reporting_user",
        source_column="poste_id",
        target_table="reporting_poste",
        target_column="id",
        join_type="LEFT JOIN",
        description="Liaison de l'agent vers le poste ou la fonction organisationnelle occupée.",
    ),
]

# -----------------------------------------------------------------------------
# INSTANCE GLOBALE DU CATALOGUE
# -----------------------------------------------------------------------------

SCHEMA_CATALOG: SchemaCatalog = SchemaCatalog(
    schema_version="1.0.0",
    database_name="gpr_ai_reporting",
    tables=_TABLES,
    relationships=_RELATIONSHIPS,
)


def get_schema_catalog() -> SchemaCatalog:
    """Retourne l'instance officielle et validée du SchemaCatalog."""
    return SCHEMA_CATALOG


def get_minimal_subschema(tables: Optional[List[str]] = None) -> str:
    """
    Génère une projection textuelle compacte du schéma pour l'injection dans le prompt LLM.

    RÈGLE DE SÉCURITÉ ABSOLUE :
    Toute colonne marquée `is_sensitive=True` est systématiquement et irrémédiablement
    exclue du sous-schéma afin d'empêcher toute fuite de données nominatives ou confidentielles
    vers les modèles de langage ou les requêtes SQL candidates.
    """
    catalog = get_schema_catalog()

    if tables is None or len(tables) == 0:
        # Par défaut, toutes les tables hors administration
        target_table_names = [
            t_name for t_name, t_meta in catalog.tables.items()
            if t_meta.table_type != "admin"
        ]
    else:
        target_table_names = [t for t in tables if t in catalog.tables]

    lines: List[str] = [
        f"# SCHEMA ANALYTIQUE DE RÉFÉRENCE ({catalog.database_name} v{catalog.schema_version})",
        "",
    ]

    for tbl_name in target_table_names:
        tbl = catalog.tables[tbl_name]
        lines.append(f"TABLE `{tbl.name}` ({tbl.table_type}) - PK: `{tbl.primary_key}`")
        lines.append(f"  Description: {tbl.description}")
        lines.append("  Colonnes autorisées :")

        for col_name, col in tbl.columns.items():
            # FILTRE DE SÉCURITÉ ABSOLUE : pas de colonnes sensibles dans le prompt
            if col.is_sensitive:
                continue

            pk_mark = " [PK]" if col.is_primary_key else ""
            fk_mark = f" [FK -> {col.references_table}.{col.references_column}]" if col.is_foreign_key else ""
            idx_mark = " [IDX]" if col.is_indexed and not col.is_primary_key else ""
            nullable_mark = "" if col.is_nullable else " NOT NULL"

            lines.append(
                f"    - `{col.name}` ({col.data_type}{nullable_mark}{pk_mark}{fk_mark}{idx_mark}): {col.description}"
            )
        lines.append("")

    # Inclusion des jointures autorisées entre les tables sélectionnées
    selected_set = set(target_table_names)
    relevant_relationships = [
        rel for rel in catalog.relationships
        if rel.source_table in selected_set and rel.target_table in selected_set
    ]

    if relevant_relationships:
        lines.append("RELATIONS & JOINTURES AUTORISÉES :")
        for rel in relevant_relationships:
            lines.append(
                f"  - `{rel.name}` : `{rel.source_table}.{rel.source_column}` = `{rel.target_table}.{rel.target_column}` ({rel.join_type})"
            )
        lines.append("")

    return "\n".join(lines).strip()
