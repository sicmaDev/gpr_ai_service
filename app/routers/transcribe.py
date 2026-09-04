from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import tempfile
import os
import re
import requests
from typing import Optional
from dotenv import load_dotenv

def clean_transcription(text: str) -> str:
    if not text:
        return ""
    # 1. Supprimer les balises HTML/XML (ex: <tag>...</tag>)
    text = re.sub(r'<[^>]*>', '', text)
    # 2. Supprimer les indicateurs Whisper/bruitages entre crochets ou parenthèses
    text = re.sub(r'\[[^\]]*\]', '', text)
    text = re.sub(r'\([^)]*\)', '', text)
    # 3. Remplacer les slashes par un espace
    text = re.sub(r'[\/\\]', ' ', text)
    # 4. Supprimer les caractères spéciaux inhabituels
    text = re.sub(r'[*_~`#@^|+==<>{}|[\]]', '', text)
    # 5. Normaliser les espaces blancs
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def transcribe_with_cloud(file_path: str) -> str:
    """Envoie le fichier audio à l'API Cloud pour transcription."""
    load_dotenv(override=True)
    CLOUD_API_KEY = os.getenv("CLOUD_TRANSCRIPTION_API_KEY", "")
    CLOUD_API_URL = os.getenv("CLOUD_TRANSCRIPTION_URL", "https://api.groq.com/openai/v1/audio/transcriptions")
    CLOUD_MODEL_NAME = os.getenv("CLOUD_TRANSCRIPTION_MODEL", "whisper-large-v3-turbo")

    if not CLOUD_API_KEY or CLOUD_API_KEY == "votre_cle_api_ici":
        return "Erreur: La clé API Cloud n'est pas configurée dans le fichier .env."
        
    headers = {
        "Authorization": f"Bearer {CLOUD_API_KEY}"
    }
    
    # On spécifie 'fr' pour être sûr de la langue
    data = {
        "model": CLOUD_MODEL_NAME,
        "language": "fr",
        "response_format": "json"
    }
    
    with open(file_path, "rb") as audio_file:
        files = {
            "file": ("audio.webm", audio_file, "audio/webm")
        }
        
        # Désactivation des proxys locaux si nécessaires, comme pour le backend Java
        proxies = {"http": "", "https": ""}
        
        try:
            response = requests.post(
                CLOUD_API_URL, 
                headers=headers, 
                data=data, 
                files=files, 
                proxies=proxies,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("text", "")
            else:
                print(f"Erreur API Cloud ({response.status_code}): {response.text}")
                return f"Erreur Cloud: {response.status_code}"
                
        except Exception as e:
            print(f"Exception lors de l'appel Cloud: {str(e)}")
            return f"Erreur de connexion: {str(e)}"

router = APIRouter(prefix="/transcribe", tags=["Audio Transcription"])

@router.post("/")
async def transcribe_audio(
    texte: Optional[str] = Form(None),
    audio_upload: Optional[UploadFile] = File(None),
    audio_recording: Optional[UploadFile] = File(None)
):
    """
    Transcribe audio files using Cloud API (Groq/OpenAI).
    Accepts either audio_upload or audio_recording or both.
    Returns the combined transcription.
    """
    transcriptions = []
    
    # Traiter l'audio uploadé
    if audio_upload:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                content = await audio_upload.read()
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                # Appel au Cloud au lieu du modèle local Whisper
                text_result = transcribe_with_cloud(tmp_path)
                transcriptions.append(text_result.strip())
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception as e:
            print(f"Erreur transcription audio_upload: {e}")
            transcriptions.append(f"Erreur: {str(e)}")
    
    # Traiter l'audio enregistré
    if audio_recording:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                content = await audio_recording.read()
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                # Appel au Cloud au lieu du modèle local Whisper
                text_result = transcribe_with_cloud(tmp_path)
                transcriptions.append(text_result.strip())
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception as e:
            print(f"Erreur transcription audio_recording: {e}")
            transcriptions.append(f"Erreur: {str(e)}")
    
    # Combiner les transcriptions
    combined_text = " ".join(transcriptions)
    
    # Ajouter le texte saisi s'il existe
    if texte:
        combined_text = texte + " " + combined_text if combined_text else texte
    
    cleaned_text = clean_transcription(combined_text)
    
    return {
        "texte_transcrit": cleaned_text,
        "transcription": cleaned_text,
        "success": True
    }
