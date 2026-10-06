"""Próbagenerálás a helyi llama.cpp szerverrel (Qwen3.8-27B)."""
import json
import time
import urllib.request

payload = {
    "model": "models\\Qwen3.8-27B-UD-Q4_K_M.gguf",
    "messages": [
        {"role": "system", "content": (
            "You write realistic IT support tickets for a 500-person company, "
            "in ENGLISH ONLY. Answer with a JSON array of objects, each "
            '{"text": "..."}, no commentary.')},
        {"role": "user", "content": (
            "Write 3 different IT support tickets from the Finance department "
            'about: printer offline / stuck print queue. They must clearly '
            'belong to the "Printers & Devices" support team.')},
    ],
    "max_tokens": 1200,
    "temperature": 0.9,
}
req = urllib.request.Request(
    "http://127.0.0.1:8080/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
t0 = time.monotonic()
r = json.load(urllib.request.urlopen(req, timeout=180))
dt = time.monotonic() - t0
print(r["choices"][0]["message"]["content"][:900])
print("---", r["usage"], f"| {dt:.1f}s")
