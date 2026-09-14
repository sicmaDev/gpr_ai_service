import os
import sys

APP_ENV = os.getenv("APP_ENV", "development").lower()
IS_DEPLOYMENT = APP_ENV in {"production", "deploy", "deployment"}

if IS_DEPLOYMENT:
    try:
        import pysqlite3
        sys.modules["sqlite3"] = pysqlite3
    except ImportError:
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import analyze, search, transcribe
from app.reporting import router as reporting_router

from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.sync_service import perform_sync

@asynccontextmanager
async def lifespan(app: FastAPI):
    if IS_DEPLOYMENT:
        scheduler = BackgroundScheduler()
        scheduler.add_job(perform_sync, 'cron', hour=2, minute=0)
        scheduler.start()
        print("Planificateur Cron démarré. Synchronisation MySQL prévue tous les jours à 02:00.")
        try:
            yield
        finally:
            scheduler.shutdown()
    else:
        yield
app = FastAPI(
    title="GPR Web IA Service",
    description="Micro-service d'Intelligence Artificielle pour la Gestion des Plaintes et Réclamations.",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS pour autoriser le backend Java (Spring Boot)
allowed_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3020,https://gpr-formation.gprserver.com",
).split(",")
allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(search.router)
app.include_router(reporting_router)
app.include_router(transcribe.router)

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
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8001")),
        reload=not IS_DEPLOYMENT,
        reload_excludes=["app/data/*", "*.sqlite3", "*.bin", "*.sqlite3-journal"],
    )
