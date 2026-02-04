import time
import hmac
import hashlib
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=".env.local")

SECRET_KEY = os.getenv("HMAC_KEY").encode()

NGROK_API_URL = "http://127.0.0.1:4040/api/tunnels"

def get_ngrok_url(retry=10, delay=1):
    """Get the public HTTPS ngrok URL from local API."""
    for _ in range(retry):
        try:
            tunnels = requests.get(NGROK_API_URL).json()
            for t in tunnels.get("tunnels", []):
                if t.get("proto") == "https":
                    return t.get("public_url")
        except Exception:
            time.sleep(delay)
    return None


def generate_download_url(model, filename):
    """Generate a signed download URL with 5 min expiry."""
    ngrok_url = get_ngrok_url()
    if not ngrok_url:
        raise RuntimeError("Ngrok tunnel not running. QR codes will not work.")

    expires = int(time.time() + 300)  # 5 minutes
    message = f"{model}|{filename}|{expires}".encode()
    signature = hmac.new(SECRET_KEY, message, hashlib.sha256).hexdigest()

    return (
        f"{ngrok_url}/download"
        f"?model={model}"
        f"&file={filename}"
        f"&expires={expires}"
        f"&sig={signature}"
    )

