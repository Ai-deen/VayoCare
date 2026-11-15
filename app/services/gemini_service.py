import os
import json
import logging
from typing import Dict, Any, Optional, List
from app.config import settings

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = None
        self.primary_model = settings.GEMINI_MODEL
        self.candidate_models: List[str] = [
            self.primary_model,
            "gemini-3.5-flash",
            "gemini-3.8-flash",
            "gemini-3.1-flash-lite"
        ]
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Google GenAI client initialized with model preference: {self.primary_model}")
            except Exception as e:
                logger.warning(f"Could not initialize GenAI client: {e}")

    def is_available(self) -> bool:
        return self.client is not None

    def generate_json_response(self, prompt: str, system_instruction: str) -> Optional[Dict[str, Any]]:
        """Invokes Gemini model to generate structured JSON output with multi-model fallback."""
        if not self.is_available():
            return None

        for model_name in self.candidate_models:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={
                        "system_instruction": system_instruction,
                        "response_mime_type": "application/json"
                    }
                )
                if response and response.text:
                    return json.loads(response.text)
            except Exception as e:
                logger.warning(f"Model {model_name} invocation failed ({e}), trying next candidate...")

        return None

    def generate_text_response(self, prompt: str, system_instruction: str = "") -> Optional[str]:
        """Invokes Gemini for general natural language generation."""
        if not self.is_available():
            return None

        for model_name in self.candidate_models:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={"system_instruction": system_instruction} if system_instruction else {}
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Model {model_name} text generation failed: {e}")

        return None

gemini_service = GeminiService()
