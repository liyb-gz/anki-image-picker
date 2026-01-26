import requests
import re
import json
import codecs
import time
import logging
from bs4 import BeautifulSoup

# Configure logging
logger = logging.getLogger(__name__)

def _get_headers():
    """Returns common headers for requests."""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

def _make_request(url, params=None, cookies=None, max_retries=3, timeout=15):
    """
    Makes an HTTP GET request with retries and 429 handling.
    """
    headers = _get_headers()
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, cookies=cookies, timeout=timeout)
            
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    logger.warning(f"Rate limited (429). Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Rate limited (429) after {max_retries} attempts.")
                    response.raise_for_status()
            
            response.raise_for_status()
            return response

        except requests.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            logger.error(f"Request failed for {url}: {e}")
            return None
    return None

def _is_image_url(url):
    """Checks if a URL likely points to an image based on its extension."""
    if not url or not isinstance(url, str):
        return False
    # Skip data URLs
    if url.startswith("data:image"):
        return True
    
    image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
    url_lower = url.lower().split("?")[0] # Check before query params
    return any(url_lower.endswith(ext) for ext in image_extensions) or any(ext in url_lower for ext in image_extensions)

def fetch_image_urls(query, limit=8, start=0, provider="google"):
    """
    Fetches image URLs from specified provider based on a search query.
    """
    if not query or not query.strip():
        return []

    if provider == "google":
        return _fetch_google(query, limit, start)
    elif provider == "bing":
        return _fetch_bing(query, limit, start)
    elif provider == "duckduckgo":
        return _fetch_duckduckgo(query, limit, start)
    else:
        return []

def _fetch_google(query, limit=8, start=0):
    """
    Fetches image URLs from Google Images.
    """
    params = {
        "q": query,
        "tbm": "isch",
        "start": start,
        "ie": "utf8",
        "oe": "utf8",
        "ucbcb": "1",
        "safe": "active",
        "tbs": "itp:photo,ic:color"
    }
    
    cookies = {"CONSENT": "YES+"}
    
    response = _make_request("https://www.google.com/search", params=params, cookies=cookies)
    if not response:
        return []
    
    html = response.text
    results = []
    
    # 1. Primary Strategy: Extract from AF_initDataCallback
    json_patterns = [
        r"AF_initDataCallback\({[^<]*?data:[^<]*?(\[.+?\])\s*\}\);",
        r"var m=(\{\"?[^\"}]+?\"?:\[.+?\]\});"
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, html)
        for match in matches:
            try:
                data = json.loads(match)
                extracted_any = False
                
                # Path 1: data[31][0][12][2]
                try:
                    for d in data[31][0][12][2]:
                        try:
                            url = d[1][3][0]
                            if url.startswith("http") and _is_image_url(url):
                                results.append(url)
                                extracted_any = True
                        except: pass
                except: pass
                
                # Path 2: data[56][1][0][0][1][0]
                try:
                    for d in data[56][1][0][0][1][0]:
                        try:
                            url = d[0][0]["444383007"][1][3][0]
                            if url.startswith("http") and _is_image_url(url):
                                results.append(url)
                                extracted_any = True
                        except: pass
                except: pass

                # Fallback to recursive extraction
                def extract_urls(obj):
                    if isinstance(obj, str):
                        if obj.startswith("http") and _is_image_url(obj):
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

    # 2. Secondary Strategy: Regex for metadata
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
            if "gstatic.com" not in img_url and _is_image_url(img_url):
                if img_url not in results:
                    results.append(img_url)

    # 3. Fallback: Direct image links
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
                # Regex already filters for extensions
                results.append(found_url)

    # 4. Last Resort: Thumbnails
    soup = BeautifulSoup(html, 'html.parser')
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src or "googlelogo" in src or "cleardot" in src:
            continue
        if src.startswith("http") or src.startswith("data:image"):
            if src not in results:
                if src.startswith("data:image") or _is_image_url(src):
                    results.append(src)
                
    # Remove duplicates
    unique_results = []
    for url in results:
        if url not in unique_results:
            unique_results.append(url)
            
    return unique_results[:limit]

def _fetch_bing(query, limit=8, start=0):
    """
    Fetches image URLs from Bing Images.
    Extracts 'murl' from the 'm' attribute of '<a>' tags with class 'iusc'.
    """
    url = "https://www.bing.com/images/search"
    params = {
        "q": query,
        "first": start,
        "count": limit,
        "adlt": "strict"
    }
    
    response = _make_request(url, params=params)
    if not response:
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    results = []
    
    for a in soup.find_all("a", class_="iusc"):
        m_attr = a.get("m")
        if m_attr:
            try:
                m_data = json.loads(m_attr)
                img_url = m_data.get("murl")
                if img_url and _is_image_url(img_url):
                    results.append(img_url)
            except json.JSONDecodeError:
                continue
    
    return results[:limit]

def _fetch_duckduckgo(query, limit=8, start=0):
    """
    Fetches image URLs from DuckDuckGo.
    Uses vqd token and i.js endpoint.
    Supports pagination via 's' parameter.
    """
    # Step 1: Get vqd token
    search_url = "https://duckduckgo.com/"
    search_params = {"q": query, "iax": "images", "ia": "images"}
    
    response = _make_request(search_url, params=search_params)
    if not response:
        return []
    
    vqd_match = re.search(r"vqd=['\"]?([a-zA-Z0-9-]+)['\"]?", response.text)
    if not vqd_match:
        logger.error(f"Could not find vqd token for DuckDuckGo search: {query}")
        return []
    
    vqd = vqd_match.group(1)
    
    # Step 2: Fetch images JSON
    json_url = "https://duckduckgo.com/i.js"
    json_params = {
        "l": "us-en",
        "o": "json",
        "q": query,
        "vqd": vqd,
        "f": ",,,",
        "s": start  # Offset for pagination
    }
    
    response = _make_request(json_url, params=json_params)
    if not response:
        return []
    
    try:
        data = response.json()
        results = []
        for item in data.get("results", []):
            img_url = item.get("image")
            if img_url and _is_image_url(img_url):
                results.append(img_url)
                
        return results[:limit]
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error(f"Error parsing DuckDuckGo JSON response: {e}")
        return []
