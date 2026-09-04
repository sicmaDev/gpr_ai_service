import requests
from app.services.vector_service import vector_db

JAVA_API_URL = "http://localhost:8020/api/v1/ai/export-claims"

def perform_sync():
    print(f"Début de la synchronisation avec l'API Java : {JAVA_API_URL}")
    
    # Désactivation explicite du proxy pour éviter l'erreur ProxyError
    proxies = {
        "http": "",
        "https": "",
    }
    
    response = requests.get(JAVA_API_URL, timeout=30, proxies=proxies)
    
    if response.status_code == 200:
        data = response.json()
        if not data:
            print("Aucune donnée reçue depuis l'API Java.")
            return
        
        print(f"{len(data)} réclamations récupérées avec succès depuis l'API.")
        vector_db.build_index_from_data(data)
        print("Synchronisation terminée avec succès.")
    else:
        print(f"Échec de la synchronisation. Statut HTTP : {response.status_code}")
        print(response.text)
        raise Exception("Erreur API Java")

def run_sync():
    print("Déclenchement de la synchronisation via l'API interne...")
    try:
        response = requests.get("http://localhost:8001/sync", timeout=120)
        if response.status_code == 200:
            print("Synchronisation réussie:", response.json().get("message", "OK"))
        else:
            print(f"Échec de la synchronisation. Statut HTTP : {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Erreur de connexion à l'API interne : {e}")
        print("Veuillez vous assurer que le serveur Python (FastAPI) est bien lancé sur le port 8001.")
