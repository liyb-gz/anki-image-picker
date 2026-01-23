import requests
import re
from bs4 import BeautifulSoup

def fetch_image_urls(query, limit=8):
    """
    Fetches image URLs from Google Images based on a search query.
    Prioritizes high-resolution images found in metadata.
    """
    if not query or not query.strip():
        return []

    url = f"https://www.google.com/search?q={query}&tbm=isch"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
            
        high_res_urls = []
        fallback_urls = []
        
        # 1. Primary Strategy: Extract high-res URLs from Google's JSON-like metadata
        # Pattern for [original_url, height, width]
        meta_patterns = [
            r'\["(https?://[^"]+)",\s*([1-9][0-9]{2,}),\s*([1-9][0-9]{2,})\]'
        ]
        
        for pattern in meta_patterns:
            matches = re.findall(pattern, response.text)
            for img_url, height, width in matches:
                if "gstatic.com" in img_url:
                    continue
                # Simple heuristic: prioritize images larger than 300px
                if int(height) >= 300 and int(width) >= 300:
                    if img_url not in high_res_urls:
                        high_res_urls.append(img_url)
                if len(high_res_urls) >= 20:
                    break

        # 2. Secondary Strategy: Extract direct image links from other patterns
        patterns = [
            r'["\'](https?://[^"\'\s]+\.(?:jpg|jpeg|png|gif|bmp))["\']',
        ]
        
        for pattern in patterns:
            found_urls = re.findall(pattern, response.text)
            for found_url in found_urls:
                if "gstatic.com" in found_url:
                    continue
                if found_url not in high_res_urls and found_url not in fallback_urls:
                    fallback_urls.append(found_url)
                if len(fallback_urls) >= 20:
                    break

        # 3. Last Resort: Extract thumbnails from <img> tags
        soup = BeautifulSoup(response.text, 'html.parser')
        for img in soup.find_all("img"):
            src = img.get("src")
            if not src or "googlelogo" in src or "cleardot" in src:
                continue
            if src.startswith("http") or src.startswith("data:image"):
                if src not in high_res_urls and src not in fallback_urls:
                    fallback_urls.append(src)
            if len(high_res_urls) + len(fallback_urls) >= 40:
                break
                    
        # Combine: High-res first, then others
        all_urls = high_res_urls + fallback_urls
        return all_urls[:limit]

    except requests.RequestException as e:
        print(f"Error fetching images for '{query}': {e}")
        return []
