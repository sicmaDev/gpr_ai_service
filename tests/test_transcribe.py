import os
import asyncio
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.routers.transcribe import (
    build_vocabulary_prompt,
    load_transcription_vocabulary,
    _parse_cloud_response,
    _preprocess_audio,
    _audio_suffix,
    clean_transcription,
    transcribe_audio,
    transcribe_with_cloud,
)
from app.services.transcription_correction import _needs_review, correct_transcription
from app.services.transcription_diarization import apply_diarization
from app.services.transcription_structure import structure_transcription
from app.services.transcription_storage import build_transcription_storage_payload


class TranscriptionTests(unittest.TestCase):
    def test_audio_mime_parameters_are_accepted(self):
        upload = SimpleNamespace(
            filename="claim_record.ogg",
            content_type="audio/ogg; codecs=opus",
        )

        self.assertEqual(_audio_suffix(upload), ".ogg")

    def test_storage_payload_preserves_transcription_data_as_json(self):
        payload = build_transcription_storage_payload(
            {
                "source": "appel.wav",
                "transcription_raw": "Bonjour",
                "transcription_corrected": "Bonjour.",
                "segments": [{"start": 0.0, "end": 1.0, "text": "Bonjour"}],
                "speakers": ["SPEAKER_00"],
                "language": "fr",
                "duration": 1.0,
                "transcription_status": "COMPLETED",
                "model": "whisper-large-v3-turbo",
            }
        )

        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["audio_original"], "appel.wav")
        self.assertEqual(payload["transcription_status"], "COMPLETED")
        self.assertEqual(payload["segments_json"], '[{"start": 0.0, "end": 1.0, "text": "Bonjour"}]')
        self.assertEqual(payload["speakers_json"], '["SPEAKER_00"]')
        self.assertIsNotNone(payload["created_at"])
        self.assertEqual(payload["created_at"], payload["updated_at"])

    def test_diarization_normalizes_provider_speakers(self):
        with patch.dict(os.environ, {"TRANSCRIPTION_DIARIZATION": "true"}):
            result = apply_diarization(
                [
                    {"id": 0, "start": 0.0, "end": 1.0, "text": "Bonjour", "speaker": "agent"},
                    {"id": 1, "start": 1.0, "end": 2.0, "text": "Bonjour", "speaker": "client"},
                ]
            )

        self.assertEqual(result["status"], "APPLIED")
        self.assertEqual(result["speakers"], ["SPEAKER_00", "SPEAKER_01"])
        self.assertEqual(result["segments"][0]["speaker"], "SPEAKER_00")

    def test_diarization_reports_unavailable_without_provider_speakers(self):
        with patch.dict(os.environ, {"TRANSCRIPTION_DIARIZATION": "true"}):
            result = apply_diarization(
                [{"id": 0, "start": 0.0, "end": 1.0, "text": "Bonjour"}]
            )

        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertEqual(result["speakers"], [])

    def test_structure_groups_segments_without_changing_their_content(self):
        result = structure_transcription(
            "Bonjour à tous. Nous commençons.",
            [
                {"id": 0, "start": 0.0, "end": 1.0, "text": "Bonjour à tous."},
                {"id": 1, "start": 1.0, "end": 2.0, "text": "Nous commençons."},
            ],
        )

        self.assertEqual(result["paragraph_count"], 1)
        self.assertEqual(result["paragraphs"][0]["text"], "Bonjour à tous. Nous commençons.")
        self.assertEqual(result["paragraphs"][0]["segment_ids"], [0, 1])
        self.assertEqual(result["paragraphs"][0]["start"], 0.0)
        self.assertEqual(result["paragraphs"][0]["end"], 2.0)
        self.assertEqual(result["sentence_count"], 2)

    def test_structure_splits_long_text_into_paragraphs(self):
        result = structure_transcription("Première phrase. Deuxième phrase.", max_paragraph_chars=18)

        self.assertEqual(
            [paragraph["text"] for paragraph in result["paragraphs"]],
            ["Première phrase.", "Deuxième phrase."],
        )
        self.assertEqual(result["word_count"], 4)

    def test_ai_correction_can_be_disabled_without_changing_text(self):
        with patch.dict(os.environ, {"TRANSCRIPTION_AI_CORRECTION": "false"}):
            result = correct_transcription("Bonjour [bruit]")

        self.assertEqual(result["text"], "Bonjour [bruit]")
        self.assertEqual(result["status"], "DISABLED")
        self.assertFalse(result["applied"])

    def test_ai_correction_falls_back_to_raw_when_llm_is_unavailable(self):
        with patch.dict(
            os.environ,
            {"TRANSCRIPTION_AI_CORRECTION": "true", "LLM_BASE_URL": "", "LLM_MODEL_NAME": ""},
            clear=False,
        ):
            result = correct_transcription("Bonjour")

        self.assertEqual(result["text"], "Bonjour")
        self.assertEqual(result["status"], "FALLBACK_RAW")

    def test_ai_correction_requires_review_when_protected_information_is_removed(self):
        reason = _needs_review(
            "Le client attend 10 000 FCFA depuis deux mois.",
            "Le client attend depuis.",
        )

        self.assertIsNotNone(reason)

    def test_ai_correction_preserves_raw_text_when_review_is_required(self):
        with patch.dict(
            os.environ,
            {
                "TRANSCRIPTION_AI_CORRECTION": "true",
                "LLM_BASE_URL": "http://ollama.test",
                "LLM_MODEL_NAME": "test-model",
            },
            clear=False,
        ):
            with patch("app.services.llm_service.DEFAULT_MODEL", "test-model"):
                with patch("app.services.llm_service.ollama_client.chat") as chat:
                    chat.return_value = {
                        "message": {
                            "content": "Le client attend depuis.",
                        }
                    }
                    result = correct_transcription(
                        "Le client attend 10 000 FCFA depuis deux mois."
                    )

        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertFalse(result["applied"])
        self.assertEqual(
            result["text"],
            "Le client attend 10 000 FCFA depuis deux mois.",
        )
        self.assertIn("proposed_text", result)
    def test_banking_vocabulary_is_loaded_without_invalid_internal_terms(self):
        vocabulary = load_transcription_vocabulary()
        prompt = build_vocabulary_prompt(vocabulary)

        self.assertIn("réclamation bancaire", prompt)
        self.assertIn("BCEAO", prompt)
        self.assertNotIn("SICMA", prompt)
        self.assertNotIn("FinGovTool", prompt)
        self.assertNotIn("KRI", prompt)
        self.assertNotIn("DMR", prompt)
    def test_clean_transcription_removes_noise_markers(self):
        text = "  Bonjour [bruit] à tous <pause>  "

        self.assertEqual(clean_transcription(text), "Bonjour à tous")

    def test_preprocess_audio_returns_original_when_ffmpeg_is_unavailable(self):
        with patch("app.routers.transcribe.shutil.which", return_value=None):
            result_path, processed = _preprocess_audio("audio.webm")

        self.assertEqual(result_path, "audio.webm")
        self.assertFalse(processed)

    def test_preprocess_audio_uses_normalized_output_when_ffmpeg_succeeds(self):
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as source:
            source_path = source.name
        processed_path = f"{source_path}.normalized.wav"

        def fake_run(command, **kwargs):
            with open(processed_path, "wb") as output:
                output.write(b"wav")
            return type("Completed", (), {"returncode": 0, "stderr": ""})()

        try:
            with patch("app.routers.transcribe.shutil.which", return_value="ffmpeg.exe"):
                with patch("app.routers.transcribe.subprocess.run", side_effect=fake_run):
                    result_path, processed = _preprocess_audio(source_path)
            self.assertEqual(result_path, processed_path)
            self.assertTrue(processed)
        finally:
            for path in (source_path, processed_path):
                if os.path.exists(path):
                    os.remove(path)

    def test_parse_cloud_response_preserves_segments(self):
        result = _parse_cloud_response(
            {
                "text": "Bonjour à tous",
                "duration": 4.2,
                "segments": [
                    {
                        "id": 0,
                        "start": 0.0,
                        "end": 4.2,
                        "text": "Bonjour à tous",
                        "avg_logprob": -0.2,
                        "words": [
                            {"word": "Bonjour", "start": 0.0, "end": 0.8, "probability": 0.91}
                        ],
                    }
                ],
            }
        )

        self.assertEqual(result["text"], "Bonjour à tous")
        self.assertEqual(result["duration"], 4.2)
        self.assertEqual(result["segments"][0]["start"], 0.0)
        self.assertEqual(result["segments"][0]["end"], 4.2)
        self.assertEqual(result["segments"][0]["avg_logprob"], -0.2)
        self.assertEqual(result["segments"][0]["words"][0]["text"], "Bonjour")
        self.assertEqual(result["segments"][0]["words"][0]["confidence"], 0.91)
        self.assertEqual(result["words"][0]["start"], 0.0)

    def test_parse_cloud_response_rejects_invalid_timestamps(self):
        result = _parse_cloud_response(
            {
                "text": "Bonjour",
                "segments": [
                    {"id": 0, "start": 4.2, "end": 2.0, "text": "invalide"},
                    {"id": 1, "start": 0.0, "end": 1.5, "text": "valide"},
                ],
            }
        )

        self.assertEqual(len(result["segments"]), 1)
        self.assertEqual(result["segments"][0]["text"], "valide")

    def test_cloud_request_uses_configured_bearer_token(self):
        response = type(
            "Response",
            (),
            {"status_code": 200, "text": "", "json": lambda self: {"text": "Bonjour"}},
        )()
        file_descriptor, file_path = tempfile.mkstemp(suffix=".webm")
        os.close(file_descriptor)

        try:
            with patch.dict(
                os.environ,
                {
                    "CLOUD_TRANSCRIPTION_API_KEY": "test-key",
                    "CLOUD_TRANSCRIPTION_RESPONSE_FORMAT": "json",
                },
                clear=False,
            ):
                with patch("app.routers.transcribe.load_dotenv"):
                    with patch("app.routers.transcribe.requests.post", return_value=response) as post:
                        result = transcribe_with_cloud(file_path)
        finally:
            os.remove(file_path)

        self.assertEqual(result["text"], "Bonjour")
        self.assertEqual(
            post.call_args.kwargs["headers"]["Authorization"],
            "B" + "earer " + "test-key",
        )
        self.assertEqual(post.call_args.kwargs["data"]["response_format"], "json")

    def test_endpoint_separates_raw_text_from_cleaned_text(self):
        transcription_result = {
            "text": "Bonjour [bruit]",
            "segments": [],
            "duration": 3.5,
            "source": "meeting.webm",
        }

        with patch(
            "app.routers.transcribe._transcribe_upload",
            new=AsyncMock(return_value=transcription_result),
        ):
            result = asyncio.run(
                transcribe_audio(
                    texte=None,
                    audio_upload=object(),
                    audio_recording=None,
                )
            )

        self.assertEqual(result["transcription_raw"], "Bonjour [bruit]")
        self.assertEqual(result["transcription_raw_parts"], ["Bonjour [bruit]"])
        self.assertEqual(result["transcription_corrected"], "Bonjour")
        self.assertTrue(result["correction_appliquee"])
        self.assertEqual(result["correction_status"], "CLEANED")
        self.assertEqual(result["transcription_status"], "COMPLETED")
        self.assertFalse(result["timestamps_available"])
        self.assertEqual(result["duration"], 3.5)
        self.assertEqual(result["diarization_status"], "DISABLED")
        self.assertIsNone(result["speakers"])


if __name__ == "__main__":
    unittest.main()
