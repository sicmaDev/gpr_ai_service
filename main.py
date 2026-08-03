from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import analyze, search, reporting

from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.sync_service import perform_sync

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrer le planificateur de tâches (Cron)
    scheduler = BackgroundScheduler()
    # Configuration pour tourner toutes les nuits à 02:00
    scheduler.add_job(perform_sync, 'cron', hour=2, minute=0)
    scheduler.start()
    print("Planificateur Cron démarré. Synchronisation MySQL prévue tous les jours à 02:00.")
    yield
    scheduler.shutdown()

app = FastAPI(
    title="GPR Web IA Service",
    description="Micro-service d'Intelligence Artificielle pour la Gestion des Plaintes et Réclamations.",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS pour autoriser le backend Java (Spring Boot)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # À restreindre en Production (ex: http://localhost:8080)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(search.router)
app.include_router(reporting.router)

@app.get("/")
def read_root():
    return {"status": "online", "service": "GPR Web IA API", "version": "1.0.0"}

@app.get("/sync")
def trigger_sync():
    try:
        perform_sync()
        return {"status": "success", "message": "Synchronisation terminée avec succès."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True, reload_excludes=["app/data/*", "*.sqlite3", "*.bin", "*.sqlite3-journal"])
