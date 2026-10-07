import json

# ==========================================
# 1. DÉFINITION DES VARIABLES (Initialisées vides)
# ==========================================
KEY_TYPE = None
KEY_STATUT = None
KEY_CATEGORIE = None
KEY_AGENCE = None
KEY_DATE = None
KEY_PRODUIT = None
KEY_MOTIF = None

# ==========================================
# 2. STRUCTURE SÉMANTIQUE (Le Contrat Métier vide au départ)
# ==========================================
DATA_DICTIONARY = {}

_schema_initialized = False

def populate_allowed_values_from_db(vector_db_instance):
    """
    1. Récupère dynamiquement les clés (noms de colonnes) depuis ChromaDB.
    2. Construit le dictionnaire avec ces clés dynamiques.
    3. Parcourt la base pour extraire toutes les valeurs uniques et les injecter.
    """
    global _schema_initialized, KEY_TYPE, KEY_STATUT, KEY_CATEGORIE, KEY_AGENCE, KEY_DATE, KEY_PRODUIT, KEY_MOTIF, DATA_DICTIONARY
    if _schema_initialized:
        return
        
    print("Initialisation 100% dynamique du dictionnaire (clés + valeurs) depuis ChromaDB...")
    
    # ÉTAPE 1 : Récupérer un échantillon pour extraire les clés dynamiquement
    all_metas = vector_db_instance.get_filtered_claims_metadata()
    if not all_metas:
        return

    db_keys = list(all_metas[0].keys())
    
    # Mapping basique pour lier les clés trouvées dans la BD aux variables Python
    for k in db_keys:
        k_lower = k.lower()
        if "type" in k_lower: KEY_TYPE = k
        elif "statut" in k_lower: KEY_STATUT = k
        elif "categorie" in k_lower: KEY_CATEGORIE = k
        elif "point" in k_lower or "agence" in k_lower: KEY_AGENCE = k
        elif "date" in k_lower: KEY_DATE = k
        elif "produit" in k_lower: KEY_PRODUIT = k
        elif "motif" in k_lower: KEY_MOTIF = k

    # Fallback de sécurité au cas où la base est corrompue ou incomplète
    KEY_TYPE = KEY_TYPE or "claim_type"
    KEY_STATUT = KEY_STATUT or "statut"
    KEY_CATEGORIE = KEY_CATEGORIE or "categorie"
    KEY_AGENCE = KEY_AGENCE or "point_service_indexe"
    KEY_DATE = KEY_DATE or "date_creation"
    KEY_PRODUIT = KEY_PRODUIT or "produit_service"
    KEY_MOTIF = KEY_MOTIF or "motif_reclamation"

    # ÉTAPE 2 : Construire le dictionnaire dynamiquement avec les clés trouvées
    DATA_DICTIONARY.clear()
    DATA_DICTIONARY[KEY_TYPE] = {"aliases": ["type", "type_requete", "type_plainte", "genre", "nature"], "allowed_values": []}
    DATA_DICTIONARY[KEY_STATUT] = {"aliases": ["etat", "avancement", "status"], "allowed_values": []}
    DATA_DICTIONARY[KEY_CATEGORIE] = {"aliases": ["catégorie", "classification", "domaine"], "allowed_values": []}
    DATA_DICTIONARY[KEY_AGENCE] = {"aliases": ["agence", "région", "ville", "bureau", "succursale", "departement"], "allowed_values": []}
    DATA_DICTIONARY[KEY_DATE] = {"aliases": ["date", "cree_le", "jour", "periode"], "allowed_values": []}
    DATA_DICTIONARY[KEY_PRODUIT] = {"aliases": ["produit", "service", "offre"], "allowed_values": []}
    DATA_DICTIONARY[KEY_MOTIF] = {"aliases": ["motif", "raison", "cause"], "allowed_values": []}

    # ÉTAPE 3 : Remplissage dynamique des valeurs
    unique_values = {key: set() for key in DATA_DICTIONARY.keys()}

    for meta in all_metas:
        for key in DATA_DICTIONARY.keys():
            val = meta.get(key)
            if val:
                unique_values[key].add(str(val).lower())

    for key in DATA_DICTIONARY.keys():
        # A la demande expresse : Seuls "claim_type" et "statut" ont des listes de valeurs fermées (strictes).
        # Les autres champs (agence, categorie...) restent ouverts pour ne pas brider l'IA.
        if key in [KEY_TYPE, KEY_STATUT]:
            DATA_DICTIONARY[key]["allowed_values"] = list(unique_values[key])

    _schema_initialized = True
    print("Dictionnaire de données 100% mis à jour dynamiquement.")

def get_schema_for_prompt() -> str:
    """Retourne une version textuelle du dictionnaire pour le LLM."""
    schema = {}
    for key, data in DATA_DICTIONARY.items():
        schema[key] = {
            "aliases_connus_a_mapper_vers_ce_champ": data["aliases"],
        }
        if data["allowed_values"]:
            schema[key]["valeurs_autorisees_strictes"] = data["allowed_values"]
    return json.dumps(schema, ensure_ascii=False, indent=2)

def validate_and_correct_llm_output(intent_data: dict) -> dict:
    """
    Valide et corrige les champs proposés par le LLM (intent_data) 
    par rapport au DATA_DICTIONARY.
    """
    filters = intent_data.get("filters", {})
    group_by = intent_data.get("group_by", "")
    
    corrected_filters = {}
    
    # 1. Validation du group_by
    valid_group_by = KEY_CATEGORIE # fallback par défaut
    if group_by:
        group_by_lower = str(group_by).lower()
        for field, meta in DATA_DICTIONARY.items():
            if group_by_lower == field or group_by_lower in meta["aliases"]:
                valid_group_by = field
                break
            
    # 2. Validation des filtres
    if isinstance(filters, dict):
        for k, v in filters.items():
            k_lower = str(k).lower()
            matched_field = None
            
            for field, meta in DATA_DICTIONARY.items():
                if k_lower == field or k_lower in meta["aliases"]:
                    matched_field = field
                    break
            
            if matched_field:
                meta = DATA_DICTIONARY[matched_field]
                val = str(v).lower()
                
                if meta["allowed_values"]:
                    if val in meta["allowed_values"]:
                        corrected_filters[matched_field] = val
                    else:
                        # Fallback: on accepte quand même la valeur
                        corrected_filters[matched_field] = val
                else:
                    corrected_filters[matched_field] = val
                
    return {
        "filters": corrected_filters,
        "group_by": valid_group_by
    }
