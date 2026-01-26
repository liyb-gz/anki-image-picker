import requests
import re
import json
import codecs
import time
from bs4 import BeautifulSoup

def fetch_image_urls(query, limit=8, start=0):
    """
    Fetches image URLs from Google Images based on a search query.
    Prioritizes high-resolution images found in metadata.
    """
    if not query or not query.strip():
        return []

    # Use parameters from the reference addon for better stability and results
    params = {
        "q": query,
        "tbm": "isch",
        "start": start,
        "ie": "utf8",
        "oe": "utf8",
        "ucbcb": "1",
        "safe": "active",
        # tbs parameters: itp:photo (images), ic:color (colored), iar:w (wide/standard)
        "tbs": "itp:photo,ic:color"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Adding CONSENT cookie to bypass common Google redirect issues
    cookies = {"CONSENT": "YES+"}
    
    max_retries = 3
    retry_delay = 5 # seconds
    
    for attempt in range(max_retries):
        try:
            response = requests.get("https://www.google.com/search", params=params, headers=headers, cookies=cookies, timeout=15)
            
            # Handle rate limiting (429) specifically as seen in reference addon
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    response.raise_for_status()
            
            response.raise_for_status()
            
            html = response.text
            results = []
            
            # 1. Primary Strategy: Extract from AF_initDataCallback (Modern Google Image structure)
            # Use a more robust regex that doesn't stop at nested brackets
            json_patterns = [
                r"AF_initDataCallback\({[^<]*?data:[^<]*?(\[.+?\])\s*\}\);",
                r"var m=(\{\"?[^\"}]+?\"?:\[.+?\]\});"
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, html)
                for match in matches:
                    try:
                        # Some versions might need the match to be slightly cleaned
                        data = json.loads(match)
                        
                        # Use specific paths from the reference addon for known Google structures
                        # These are often more reliable than generic recursive search
                        extracted_any = False
                        
                        # Path 1: data[31][0][12][2]
                        try:
                            # The structure is deeply nested
                            for d in data[31][0][12][2]:
                                try:
                                    url = d[1][3][0]
                                    if url.startswith("http"):
                                        results.append(url)
                                        extracted_any = True
                                except: pass
                        except: pass
                        
                        # Path 2: data[56][1][0][0][1][0]
                        try:
                            for d in data[56][1][0][0][1][0]:
                                try:
                                    url = d[0][0]["444383007"][1][3][0]
                                    if url.startswith("http"):
                                        results.append(url)
                                        extracted_any = True
                                except: pass
                        except: pass

                        # Fallback to recursive extraction if specific paths failed or for other structures
                        def extract_urls(obj):
                            if isinstance(obj, str):
                                if obj.startswith("http") and any(ext in obj.lower() for ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]):
                                    if "gstatic.com" not in obj:
                                        results.append(obj)
                            elif isinstance(obj, list):
                                for item in obj:
                                    extract_urls(item)
                            elif isinstance(obj, dict):
                                for value in obj.values():
                                    extract_urls(value)
                        
                        if not extracted_any:
                            extract_urls(data)
                            
                    except json.JSONDecodeError:
                        continue

            # 2. Secondary Strategy: Regex for [original_url, height, width] metadata
            meta_patterns = [
                r'\["(https?://[^"]+)",\s*([1-9][0-9]{2,}),\s*([1-9][0-9]{2,})\]'
            ]
            for pattern in meta_patterns:
                matches = re.findall(pattern, html)
                for img_url, height, width in matches:
                    try:
                        img_url = codecs.decode(img_url, 'unicode_escape')
                    except:
                        pass
                    if "gstatic.com" not in img_url:
                        if img_url not in results:
                            results.append(img_url)

            # 3. Fallback: Direct image links in the page
            fallback_patterns = [
                r'["\'](https?://[^"\'\s]+\.(?:jpg|jpeg|png|gif|bmp|webp))["\']',
            ]
            for pattern in fallback_patterns:
                found_urls = re.findall(pattern, html)
                for found_url in found_urls:
                    try:
                        found_url = codecs.decode(found_url, 'unicode_escape')
                    except:
                        pass
                    if "gstatic.com" not in found_url and found_url not in results:
                        results.append(found_url)

            # 4. Last Resort: Thumbnails from <img> tags
            soup = BeautifulSoup(html, 'html.parser')
            for img in soup.find_all("img"):
                src = img.get("src")
                if not src or "googlelogo" in src or "cleardot" in src:
                    continue
                if src.startswith("http") or src.startswith("data:image"):
                    if src not in results:
                        results.append(src)
                        
            # Remove duplicates while preserving order
            unique_results = []
            for url in results:
                if url not in unique_results:
                    unique_results.append(url)
                    
            return unique_results[:limit]

        except requests.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(1) # Short sleep before retry for non-429 errors
                continue
            print(f"Error fetching images for '{query}': {e}")
            return []
    
    return []
