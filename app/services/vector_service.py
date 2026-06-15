import json
import os
import chromadb
from sentence_transformers import SentenceTransformer

# Définition du chemin absolu vers nos fausses données générées précédemment
MOCK_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "plaintes_fictives.json")
CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")

class VectorSearchService:
    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        """
        Initialise le modèle NLP pre-entrainé multilingue (efficace en français) 
        et le client persistant ChromaDB.
        """
        print(f"Chargement du modèle {model_name}... (cela peut prendre quelques secondes)")
        self.model = SentenceTransformer(model_name)
        
        # Initialiser ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.collection = self.chroma_client.get_or_create_collection(name="claims")
        
        # Si la collection est vide, charger les données fictives
        if self.collection.count() == 0:
            print("Collection ChromaDB vide. Chargement des données fictives par défaut...")
            self._load_and_index_mock_data()
        else:
            print(f"Collection ChromaDB chargée avec {self.collection.count()} vecteurs.")

    def build_index_from_data(self, data: list):
        """Met à jour (Upsert) l'index complet à partir d'une liste de dictionnaires (venant de l'API)."""
        if not data:
            print("Aucune donnée fournie pour l'indexation.")
            return

        print(f"Indexation/Mise à jour de {len(data)} réclamations dans ChromaDB...")
        
        ids = []
        embeddings = []
        metadatas = []
        documents = []

        for row in data:
            # Sécurité si un code manque, on utilise l'id
            doc_id = str(row.get('id', row.get('code')))
            if not doc_id:
                continue
                
            cat = row.get('objet_categorie', '')
            mot = row.get('motif_reclamation', '')
            txt = row.get('texte_plainte', '')
            combined = f"Catégorie: {cat}. Motif: {mot}. Plainte: {txt}"
            
            # Préparation des tableaux pour ChromaDB
            ids.append(doc_id)
            documents.append(combined)
            
            # Filtrer les métadonnées pour éviter les objets complexes non supportés par ChromaDB (ex: listes de dict)
            # On stocke l'essentiel pour le filtrage et on stringify le reste
            meta = {
                "id_historique": int(row['id']),
                "code": str(row.get('code', '')),
                "code_client": str(row.get('codeClient', '')),
                "categorie": str(cat).lower(), # On stocke en minuscule pour le filtrage
                "statut": str(row.get('statut_final', '')),
                "texte_original": str(txt),
                "solution_suggeree": str(row.get('texte_solution', '')),
                "modalite_depot": str(row.get('modalite_depot', '')),
                "motif_reclamation": str(mot).lower(), # Minuscule pour filtrage strict
                "produit_service": str(row.get('produit_service', '')),
                "point_service_indexe": str(row.get('point_service_indexe', '')),
                "date_creation": str(row.get('date_creation', ''))
            }
            # Les listes medias et audios sont converties en chaine JSON car ChromaDB ne gère que les types simples
            meta["medias"] = json.dumps(row.get('medias', []))
            meta["audios"] = json.dumps(row.get('audios', []))
            
            metadatas.append(meta)

        # Calculer tous les embeddings d'un coup
        print("Calcul des embeddings...")
        embeds = self.model.encode(documents, convert_to_numpy=True).tolist()
        
        # Upsert dans ChromaDB (Ajoute si n'existe pas, met à jour si l'ID existe)
        print("Enregistrement dans la base de données...")
        self.collection.upsert(
            ids=ids,
            embeddings=embeds,
            metadatas=metadatas,
            documents=documents
        )
        
        print(f"Mise à jour terminée. Total des vecteurs en base: {self.collection.count()}")

    def _load_and_index_mock_data(self):
        """Charge les données JSON fictives (utilisé en fallback si rien d'autre)."""
        try:
            with open(MOCK_DATA_PATH, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            if not raw_data:
                return
                
            data = [item for item in raw_data if item.get('statut_final') == 'SATISFIED']
            self.build_index_from_data(data)
            
        except Exception as e:
            print(f"Erreur lors de l'initialisation depuis le mock data: {e}")

    def search_similar(self, query: str, top_k: int = 3, category_filter: str = None, motif_filter: str = None) -> list[dict]:
        """
        Recherche les plaintes les plus sémantiquement proches de la requête.
        Utilise le filtrage natif de ChromaDB.
        """
        if self.collection.count() == 0:
            return []

        # 1. Construction de la query
        cat_str = category_filter or ""
        mot_str = motif_filter or ""
        combined_query = f"Catégorie: {cat_str}. Motif: {mot_str}. Plainte: {query}"
        
        # 2. Embedding de la recherche
        query_vector = self.model.encode([combined_query], convert_to_numpy=True).tolist()
        
        # 3. Construction du filtre (where clause de ChromaDB)
        where_filter = {}
        if category_filter and motif_filter:
            where_filter = {
                "$and": [
                    {"categorie": category_filter.lower()},
                    {"motif_reclamation": motif_filter.lower()}
                ]
            }
        elif category_filter:
            where_filter = {"categorie": category_filter.lower()}
        elif motif_filter:
            where_filter = {"motif_reclamation": motif_filter.lower()}

        # 4. Requête à ChromaDB (c'est instantané et filtré nativement !)
        # On ne passe le where que s'il n'est pas vide
        kwargs = {
            "query_embeddings": query_vector,
            "n_results": top_k
        }
        if where_filter:
            kwargs["where"] = where_filter

        results = self.collection.query(**kwargs)
        
        # 5. Formatage de la réponse pour l'API
        formatted_results = []
        
        if not results['ids'] or not results['ids'][0]:
            return []
            
        # results est un dict avec 'ids', 'distances', 'metadatas', 'documents'
        # comme on a demandé 1 query, tout est dans le premier élément (index 0)
        for i in range(len(results['ids'][0])):
            meta = results['metadatas'][0][i]
            dist = results['distances'][0][i]
            
            # Reconversion des listes JSON
            medias = []
            audios = []
            try:
                if "medias" in meta and meta["medias"]:
                    medias = json.loads(meta["medias"])
                if "audios" in meta and meta["audios"]:
                    audios = json.loads(meta["audios"])
            except:
                pass
                
            formatted_results.append({
                "score_similarite": float(dist), # Dans Chroma, c'est généralement la distance euclidienne par défaut (L2)
                "id_historique": int(meta.get('id_historique', 0)),
                "code": meta.get('code'),
                "code_client": meta.get('code_client'),
                "categorie": meta.get('categorie'), # attention, il est en minuscule
                "statut": meta.get('statut'),
                "texte_original": meta.get('texte_original'),
                "solution_suggeree": meta.get('solution_suggeree'),
                "modalite_depot": meta.get('modalite_depot'),
                "motif_reclamation": meta.get('motif_reclamation'),
                "produit_service": meta.get('produit_service'),
                "point_service_indexe": meta.get('point_service_indexe'),
                "date_creation": meta.get('date_creation'),
                "medias": medias,
                "audios": audios
            })
            
        return formatted_results

# Singleton: Chargé une seule fois
vector_db = VectorSearchService()
