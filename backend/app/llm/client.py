import httpx

from app.core.config import Settings, get_settings
from app.llm.schemas import ChapterGeneration, parse_chapter_generation


class LLMClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def generate_chapter(self, messages: list[dict[str, str]]) -> ChapterGeneration:
        base_url = str(self.settings.llm_base_url).rstrip('/')
        try:
            response = httpx.post(
                f'{base_url}/chat/completions',
                headers={'Authorization': f'Bearer {self.settings.llm_api_key}'},
                json={
                    'model': self.settings.llm_model,
                    'messages': messages,
                    'temperature': 0.7,
                    'response_format': {'type': 'json_object'},
                },
                timeout=self.settings.llm_timeout_seconds,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise TimeoutError('MODEL_TIMEOUT') from exc
        except httpx.HTTPError as exc:
            raise RuntimeError('MODEL_REQUEST_FAILED') from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError('MODEL_RESPONSE_INVALID') from exc
        if not isinstance(payload, dict):
            raise ValueError('MODEL_RESPONSE_INVALID')
        choices = payload.get('choices', [])
        if not choices or not isinstance(choices[0], dict):
            raise ValueError('MODEL_RESPONSE_INVALID')
        content = choices[0].get('message', {}).get('content')
        if not isinstance(content, str):
            raise ValueError('MODEL_RESPONSE_INVALID')
        return parse_chapter_generation(content)
