from app.infra.clients.http_client import HttpClient


class OpenRouterClient:
    def __init__(self, api_key: str, open_router_base_url: str, http: HttpClient):
        self.api_key = api_key
        self.base_url = open_router_base_url
        self.http = http

    async def embeddings(self, model: str, input: list[str]):
        endpoint = f"{self.base_url}/embeddings"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": model, "input": input}
        response = await self.http.post(endpoint, json=payload, headers=headers)
        return response
    
    async def completions(self, model: str, prompt: str):
        endpoint = f"{self.base_url}/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": model, "prompt": prompt}
        response = await self.http.post(endpoint, json=payload, headers=headers)
        return response
    
    
