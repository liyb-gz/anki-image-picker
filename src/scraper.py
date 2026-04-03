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

def _is_blocked_domain(url):
    """Returns True if URL is from a domain known to block direct image access."""
    if not url:
        return False
    url_lower = url.lower()
    
    # Only block domains that consistently return 403/HTML for ALL image requests.
    # Note: Stock photo sites like shutterstock.com/dreamstime.com are NOT blocked
    # because Google provides links to their thumbnail/preview images which work fine.
    blocked_patterns = [
        # Pinterest aggressively blocks all hotlinking with 403
        "pinterest.com",
        "pinterest.",
        "pinimg.com",
        # Social media that blocks hotlinking
        "facebook.com",
        "fbcdn.net",
        "instagram.com",
        "cdninstagram.com",
        # Sites that consistently return 403 for direct image access
        "creativefabrica.com",
        "freevector.com",
        "cleanpng.com",
    ]
    return any(pattern in url_lower for pattern in blocked_patterns)

def _is_image_url(url):
    """Checks if a URL likely points to an image based on its extension or path patterns."""
    if not url or not isinstance(url, str):
        return False
    
    # Skip blocked domains
    if _is_blocked_domain(url):
        return False
    
    # Data URLs are always valid images
    if url.startswith("data:image"):
        return True
    
    # Normalize URL for checking
    url_lower = url.lower()
    
    # Remove query params and fragments for extension check
    path_part = url_lower.split("?")[0].split("#")[0]
    
    image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".avif", ".svg"]
    
    # Check if path ENDS with image extension (most reliable)
    if any(path_part.endswith(ext) for ext in image_extensions):
        return True
    
    # Check for extensions followed by / (CDN resizing patterns like /image.jpg/resize)
    for ext in image_extensions:
        if ext + "/" in path_part:
            return True
    
    # Check query params for image extensions with proper boundary
    # Match extension at end of a param value (before & or end of string)
    if "?" in url_lower:
        query_part = url_lower.split("?")[1]
        for ext in image_extensions:
            # Look for extension followed by & or at end of query string
            if re.search(rf'{re.escape(ext)}(?:&|$)', query_part):
                return True
    
    # Known image CDN domains that serve images without extensions
    image_cdn_domains = [
        "images.unsplash.com",
        "i.imgur.com",
        "pbs.twimg.com",
        "cdn.pixabay.com",
    ]
    if any(cdn in url_lower for cdn in image_cdn_domains):
        return True
    
    return False

def fetch_image_urls(query, limit=8, start=0, provider="bing"):
    """
    Fetches image URLs from specified provider based on a search query.
    """
    if not query or not query.strip():
        return []

    if provider == "google":
        logger.warning(
            "Google Image Search is no longer available. "
            "Google now renders image results entirely via client-side JavaScript, "
            "making HTTP-based scraping impossible. Falling back to Bing."
        )
        results = _fetch_bing(query, limit, start)
    elif provider == "bing":
        results = _fetch_bing(query, limit, start)
    elif provider == "duckduckgo":
        results = _fetch_duckduckgo(query, limit, start)
    else:
        results = []
    return results

def _fetch_google(query, limit=8, start=0):
    """
    Fetches image URLs from Google Images.
    """
    # Dynamically build tbs based on query
    # If query contains illustration-related terms, don't force itp:photo
    non_photo_terms = [
        "illustration", "drawing", "clipart", "vector", "sketch", "painting",
        "anime", "cartoon", "icon", "logo", "diagram", "infographic", "art",
        "comic", "manga", "pixel", "3d render", "cgi"
    ]
    is_non_photo = any(term in query.lower() for term in non_photo_terms)
    
    tbs = "ic:color"
    if not is_non_photo:
        tbs += ",itp:photo"
    
    params = {
        "q": query,
        "tbm": "isch",
        "start": start,
        "ie": "utf8",
        "oe": "utf8",
        "ucbcb": "1",
        "safe": "active",
        "tbs": tbs
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
    Uses urllib for more consistent behavior across Python versions.
    """
    import urllib.request
    import urllib.parse
    import urllib.error
    import http.cookiejar
    
    # Create a cookie jar and opener to maintain session
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Step 1: Get initial page to obtain vqd token
    search_params = urllib.parse.urlencode({"q": query, "iax": "images", "ia": "images"})
    search_url = f"https://duckduckgo.com/?{search_params}"
    
    try:
        req = urllib.request.Request(search_url, headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
        with opener.open(req, timeout=15) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        logger.error(f"DuckDuckGo initial request failed: {e}")
        return []
    
    vqd_match = re.search(r"vqd=['\"]?([a-zA-Z0-9-]+)['\"]?", html)
    if not vqd_match:
        logger.error(f"Could not find vqd token for DuckDuckGo search: {query}")
        return []
    
    vqd = vqd_match.group(1)
    
    # Step 2: Fetch images JSON
    json_params = urllib.parse.urlencode({
        "l": "us-en",
        "o": "json",
        "q": query,
        "vqd": vqd,
        "f": ",,,",
        "p": "1",
        "s": start
    })
    json_url = f"https://duckduckgo.com/i.js?{json_params}"
    
    try:
        req = urllib.request.Request(json_url, headers={
            "User-Agent": user_agent,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://duckduckgo.com/",
            "X-Requested-With": "XMLHttpRequest",
        })
        with opener.open(req, timeout=15) as response:
            json_text = response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        logger.error(f"DuckDuckGo API request failed: {e}")
        return []
    except Exception as e:
        logger.error(f"DuckDuckGo API request failed: {e}")
        return []
    
    try:
        data = json.loads(json_text)
        results = []
        for item in data.get("results", []):
            img_url = item.get("image")
            if img_url and _is_image_url(img_url):
                results.append(img_url)
        return results[:limit]
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error(f"Error parsing DuckDuckGo JSON response: {e}")
        return []
