from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import tempfile
import os
from typing import Optional

router = APIRouter(prefix="/transcribe", tags=["Audio Transcription"])

# Charger le modèle Whisper une seule fois au démarrage
whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        try:
            import whisper
            print("Chargement du modèle Whisper...")
            whisper_model = whisper.load_model("base")
        except ImportError:
            raise ImportError("openai-whisper n'est pas installé. Veuillez exécuter: pip install openai-whisper")
    return whisper_model

@router.post("/")
async def transcribe_audio(
    texte: Optional[str] = Form(None),
    audio_upload: Optional[UploadFile] = File(None),
    audio_recording: Optional[UploadFile] = File(None)
):
    """
    Transcribe audio files using Whisper.
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
                model = get_whisper_model()
                result = model.transcribe(tmp_path, language="fr", task="transcribe")
                transcriptions.append(result["text"].strip())
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
                model = get_whisper_model()
                result = model.transcribe(tmp_path, language="fr", task="transcribe")
                transcriptions.append(result["text"].strip())
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
    
    return {
        "texte_transcrit": combined_text.strip(),
        "transcription": combined_text.strip(),
        "success": True
    }
