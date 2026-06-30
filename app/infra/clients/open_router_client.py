from app.infra.clients.http_client import HttpClient


class OpenRouterClient:
    def __init__(self, api_key: str, base_url: str, http: HttpClient):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/embeddings"
        self.http = http

    async def embeddings(self, model: str, input: list[str]):
        endpoint = f"{self.base_url}/embeddings"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": model, "input": input}
        response = await self.http.post(endpoint, json=payload, headers=headers)
        return response

