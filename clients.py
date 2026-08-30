class FakeClient:
    """Returns pre-scripted responses, one per call, in order.
    Records every prompt sent, so tests can assert the error text got through."""

    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls: list[str] = []

    def complete(self, prompt: str) -> str:
        self.calls.append(prompt)
        if not self._responses:
            raise RuntimeError(
                f"FakeClient ran out of scripted responses "
                f"(was called {len(self.calls)} times)"
            )
        return self._responses.pop(0)


class OllamaClient:
    """Local model over HTTP. Needs `ollama serve` running."""

    def __init__(self, model: str = "llama3.2", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host

    def complete(self, prompt: str) -> str:
        import requests

        r = requests.post(
            f"{self.host}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0},
            },
            timeout=180,
        )
        r.raise_for_status()
        return r.json()["response"]
