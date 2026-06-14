from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import analyze, search, transcribe

app = FastAPI(
    title="GPR Web IA Service",
    description="Micro-service d'Intelligence Artificielle pour la Gestion des Plaintes et Réclamations.",
    version="1.0.0"
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
app.include_router(transcribe.router)

@app.get("/")
def read_root():
    return {"status": "online", "service": "GPR Web IA API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
