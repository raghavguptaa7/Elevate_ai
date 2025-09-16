import os
import requests
import json
import time
from utils.config import get_config
from utils.logger import log_info, log_error, log_groq_api_request


class GroqClient:
    def __init__(self, api_key=None, base_url=None, model=None):
        """Initialize the Groq client."""
        self.config = get_config()
        self.api_key = api_key or self.config.GROQ_API_KEY
        if not self.api_key:
            log_error("GROQ_API_KEY not found. Set it in .env file or pass it to the constructor.")
            raise ValueError("Missing GROQ_API_KEY")

        # Ensure base_url ends at /v1 (not /chat/completions)
        self.base_url = (base_url or self.config.GROQ_API_BASE_URL).rstrip("/")
        if self.base_url.endswith("/chat/completions"):
            self.base_url = self.base_url.replace("/chat/completions", "")

        self.model = model or self.config.GROQ_API_MODEL

    def set_model(self, model_name: str):
        """Change the model used for generation."""
        self.model = model_name

    def generate_response(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """Generate a plain text response from Groq API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # Log request
        prompt_type = prompt.split('\n')[0][:50]
        log_groq_api_request(prompt_type)

        start_time = time.time()
        try:
            # Ensure we're using the correct endpoint
            endpoint = f"{self.base_url}/chat/completions"
            response = requests.post(
                endpoint,
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()

            choices = result.get("choices", [])
            if not choices:
                raise Exception(f"No choices in response: {result}")

            content = choices[0]["message"]["content"]

            # Logging
            response_time = int((time.time() - start_time) * 1000)
            tokens_used = result.get("usage", {}).get("total_tokens", 0)
            log_groq_api_request(prompt_type, tokens_used, response_time)

            return content

        except Exception as e:
            log_error(f"Groq API request failed: {str(e)}")
            raise

    def generate_structured_response(self, prompt: str, expect_json: bool = True,
                                     temperature: float = 0.7, max_tokens: int = 2048):
        """Generate a structured (JSON) response from Groq API.
        Since Groq does not support `response_format`, we enforce JSON via prompt.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Prompt trick: force JSON output if requested
        if expect_json:
            prompt = f"{prompt}\n\nReturn ONLY valid JSON as response."

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        prompt_type = prompt.split('\n')[0][:50]
        log_groq_api_request(prompt_type)

        start_time = time.time()
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()

            choices = result.get("choices", [])
            if not choices:
                raise Exception(f"No choices in response: {result}")

            content = choices[0]["message"]["content"]

            # Logging
            response_time = int((time.time() - start_time) * 1000)
            tokens_used = result.get("usage", {}).get("total_tokens", 0)
            log_groq_api_request(prompt_type, tokens_used, response_time)

            if expect_json:
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    log_error(f"Failed to parse JSON response: {str(e)}")
                    log_error(f"Raw content: {content[:500]}...")
                    raise

            return content

        except Exception as e:
            log_error(f"Groq API request failed: {str(e)}")
            raise