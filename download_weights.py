import os
import requests

def download_arcface_weights():
    weights_dir = os.path.expanduser("~/.deepface/weights")
    os.makedirs(weights_dir, exist_ok=True)
    target_path = os.path.join(weights_dir, "arcface_weights.h5")
    
    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        print(f"ArcFace weights already present at {target_path}")
        return

    url = "https://github.com/serengil/deepface_models/releases/download/v1.0/arcface_weights.h5"
    print(f"Downloading ArcFace weights from {url}...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    response = requests.get(url, headers=headers, stream=True)
    if response.status_code == 200:
        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"[+] Download complete! Saved to {target_path} (Size: {os.path.getsize(target_path)} bytes)")
    else:
        print(f"[-] Failed to download weights. Status code: {response.status_code}")

if __name__ == "__main__":
    download_arcface_weights()
