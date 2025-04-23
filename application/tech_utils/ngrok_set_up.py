# Set up bot
import requests
import os

NGROK_API_KEY = os.getenv("NGROK_API_KEY")
NGROK_API_BASE = "https://api.ngrok.com"
HEADERS = {
    "Authorization": f"Bearer {NGROK_API_KEY}",
    "Ngrok-Version": "2"
}

def get_url(forwards_to_port: int, timeout=10) -> str:
    for _ in range(timeout):
        resp = requests.get(f"{NGROK_API_BASE}/tunnels", headers=HEADERS)
        resp.raise_for_status()
        tunnels = resp.json().get("tunnels", [])
        for t in tunnels:
            if t.get("proto") == "https" and f"127.0.0.1:{forwards_to_port}" in t.get("forwards_to", ""):
                return t["public_url"]
        time.sleep(1)
    raise RuntimeError(f"No ngrok tunnel forwarding to port {forwards_to_port} found after {timeout} sec")



import time

def get_public_url(forwards_to_port: int, timeout=10) -> str:
    for i in range(timeout):
        try:
            url = get_url(forwards_to_port)
            return url
        except RuntimeError:
            time.sleep(1)
    raise RuntimeError(f"Tunnel '{forwards_to_port}' not available after {timeout} sec")
