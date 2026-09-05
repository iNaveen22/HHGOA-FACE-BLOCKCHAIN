import os
import requests

def download_test_images():
    os.makedirs("test_images", exist_ok=True)
    images = {
        "person1_a.jpg": "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg",
        "person2_a.jpg": "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/cv/face/david1.jpg"
    }
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for filename, url in images.items():
        filepath = os.path.join("test_images", filename)
        print(f"Downloading test image: {filename}...")
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(resp.content)
            print(f"Saved to {filepath}")
        else:
            print(f"Failed to download {filename}: Status {resp.status_code}")

if __name__ == "__main__":
    download_test_images()
