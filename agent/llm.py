import requests
import json
from typing import Optional

# ─── Config ────────────────────────────────────────────────────────────────────
OLLAMA_URL   = "http://localhost:11434"
DEFAULT_MODEL = "llama3.1:8b"


class OllamaClient:

    def __init__(self, model: str = DEFAULT_MODEL, base_url: str = OLLAMA_URL):
        self.model    = model
        self.base_url = base_url.rstrip("/")

    def is_available(self) -> bool:
        
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code != 200:
                return False
            models = [m["name"] for m in resp.json().get("models", [])]
            return any(self.model in m for m in models)
        except Exception:
            return False

    def chat(
        self,
        messages: list,
        system:   Optional[str] = None,
        temperature: float = 0.2,
        stream:   bool = False,
    ) -> str:
       
        payload = {
            "model":   self.model,
            "messages": messages,
            "stream":  stream,
            "options": {
                "temperature": temperature,
                "num_predict": 2048,   # max tokens per response
                "stop": ["Human:", "User:"],
            }
        }

        if system:
            payload["system"] = system

        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=300,
                stream=stream,
            )

            if resp.status_code != 200:
                raise RuntimeError(f"Ollama returned HTTP {resp.status_code}: {resp.text[:200]}")

            if stream:
                return self._stream(resp)
            else:
                data = resp.json()
                return data["message"]["content"].strip()

        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Cannot connect to Ollama. Make sure it's running:\n"
                "  ollama serve"
            )
        except requests.exceptions.Timeout:
            raise RuntimeError("Ollama request timed out after 300 seconds. Model may be slow or unresponsive.")

    def _stream(self, resp) -> str:
        
        full_text = ""
        for line in resp.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    full_text += token
                    print(token, end="", flush=True)
                    if chunk.get("done"):
                        break
                except json.JSONDecodeError:
                    continue
        print()  # newline after streaming
        return full_text.strip()

    def complete(self, prompt: str, system: Optional[str] = None) -> str:
        return self.chat(
            messages=[{"role": "user", "content": prompt}],
            system=system,
        )

    def list_models(self) -> list:
        
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            return []
