import time
import httpx

def check_ollama_health(base_url: str) -> bool:
    try:
        r = httpx.get(f"{base_url}/api/tags", timeout=10.0)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[health] Ollama health check failed: {e}")
        return False

def model_in_tags(base_url: str, model: str) -> bool:
    try:
        r = httpx.get(f"{base_url}/api/tags", timeout=10.0)
        r.raise_for_status()
        tags = r.json().get("models", [])
        names = {m.get("name") for m in tags if "name" in m}
        return model in names
    except Exception as e:
        print(f"[tags] Could not fetch tags: {e}")
        return False

def warmup_ollama(base_url: str, model: str, keep_alive: str,
                  timeout: float = 90.0, retries: int = 2, backoff_sec: float = 5.0):
    payload = {"model": model, "prompt": "ping", "stream": False, "keep_alive": keep_alive}
    for attempt in range(1, retries + 1):
        try:
            r = httpx.post(f"{base_url}/api/generate", json=payload, timeout=timeout)
            r.raise_for_status()
            print(f"[warmup] {model} warmed successfully.")
            return
        except Exception as e:
            print(f"[warmup] Warning: {model} attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(backoff_sec * (2 ** (attempt - 1)))
    print(f"[warmup] Giving up warming {model}. Proceeding anyway.")
