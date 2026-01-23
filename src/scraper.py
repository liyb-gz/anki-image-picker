import requests
import re
from bs4 import BeautifulSoup

def fetch_image_urls(query, limit=8):
    """
    Fetches image URLs from Google Images based on a search query.

    Args:
        query (str): The search term to find images for.
        limit (int): The maximum number of URLs to return. Defaults to 8.

    Returns:
        list: A list of image URLs (strings).
    """
    if not query or not query.strip():
        return []

    url = f"https://www.google.com/search?q={query}&tbm=isch"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        urls = []
        
        # 1. Try to find images in the standard HTML structure
        for img in soup.find_all("img"):
            src = img.get("src")
            if not src:
                continue
            
            # Skip obvious UI elements
            if any(x in src for x in ["googlelogo", "cleardot", "nav_logo"]):
                continue
                
            if src.startswith("http") or src.startswith("data:image"):
                if src not in urls:
                    urls.append(src)
            
            if len(urls) >= 20:
                break
                
        # 2. Use regex to find additional URLs (especially high-res or those in scripts)
        # We look for the pattern ["https://...", height, width] which is common in Google's JSON metadata
        patterns = [
            r'\["(https?://[^"]+)",\s*\d+,\s*\d+\]',
            r'["\'](https?://[^"\'\s]+\.(?:jpg|jpeg|png|gif|bmp))["\']',
            r'["\'](https?://encrypted-tbn[0-9]\.gstatic\.com/images\?q=tbn:[^"\'\s]+)["\']'
        ]
        
        for pattern in patterns:
            found_urls = re.findall(pattern, response.text)
            for found_url in found_urls:
                # Prioritize original URLs over thumbnails
                if "gstatic.com" in found_url and len(urls) > 0:
                    continue
                if found_url not in urls:
                    urls.append(found_url)
                if len(urls) >= 30:
                    break
                    
        return urls[:limit]
    except requests.RequestException as e:
        print(f"Error fetching images for '{query}': {e}")
        return []
