import requests
from bs4 import BeautifulSoup

def fetch_image_urls(query):
    url = f"https://www.google.com/search?q={query}&tbm=isch"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        # Google Images HTML structure for thumbnails
        # In the simple version, it's often <img> tags with a specific class or within <td>
        # For our mock, we used class "t-image"
        images = soup.find_all("img")
        
        urls = []
        for img in images:
            src = img.get("src")
            if src and (src.startswith("http") or src.startswith("data:image")):
                urls.append(src)
            if len(urls) >= 8:
                break
        return urls
    except Exception:
        return []
