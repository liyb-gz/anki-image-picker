import pytest
from unittest.mock import patch, MagicMock
from src.scraper import fetch_image_urls

@patch('requests.get')
def test_fetch_image_urls_returns_list_of_urls(mock_get):
    mock_html = """
    <html>
        <body>
            <a class="iusc" m='{"murl":"https://example.com/image1.jpg"}'></a>
            <a class="iusc" m='{"murl":"https://example.com/image2.jpg"}'></a>
            <a class="iusc" m='{"murl":"https://example.com/image3.png"}'></a>
            <a class="iusc" m='{"murl":"https://example.com/image4.jpeg"}'></a>
            <a class="iusc" m='{"murl":"https://example.com/image5.gif"}'></a>
            <a class="iusc" m='{"murl":"https://example.com/image6.webp"}'></a>
            <a class="iusc" m='{"murl":"https://example.com/image7.bmp"}'></a>
            <a class="iusc" m='{"murl":"https://example.com/image8.jpg"}'></a>
            <a class="iusc" m='{"murl":"https://example.com/image9.png"}'></a>
        </body>
    </html>
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    mock_get.return_value = mock_response

    urls = fetch_image_urls("test query")
    
    assert isinstance(urls, list)
    assert len(urls) == 8
    assert all(isinstance(url, str) for url in urls)
    assert "example.com" in urls[0]

@patch('requests.get')
def test_fetch_image_urls_handles_error(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_get.return_value = mock_response
    
    urls = fetch_image_urls("test query")
    assert urls == []

@patch('requests.get')
def test_google_provider_falls_back_to_bing(mock_get):
    mock_html = """
    <html>
        <body>
            <a class="iusc" m='{"murl":"https://example.com/bing_fallback.jpg"}'></a>
        </body>
    </html>
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    mock_get.return_value = mock_response

    urls = fetch_image_urls("test query", provider="google")
    
    assert "https://example.com/bing_fallback.jpg" in urls
    assert "bing" in mock_get.call_args[0][0]

def test_fetch_image_urls_empty_query():
    assert fetch_image_urls("") == []
    assert fetch_image_urls("   ") == []
    assert fetch_image_urls(None) == []

@patch('requests.get')
def test_fetch_image_urls_bing(mock_get):
    # Mock HTML response from Bing
    mock_html = """
    <html>
        <body>
            <a class="iusc" m='{"murl":"https://example.com/bing1.jpg"}'></a>
            <a class="iusc" m='{"murl":"https://example.com/bing2.jpg"}'></a>
        </body>
    </html>
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = mock_html
    mock_get.return_value = mock_response

    urls = fetch_image_urls("test query", provider="bing")
    
    assert "https://example.com/bing1.jpg" in urls
    assert "https://example.com/bing2.jpg" in urls
    assert "bing" in mock_get.call_args[0][0]

@patch('urllib.request.build_opener')
def test_fetch_image_urls_duckduckgo(mock_build_opener):
    # Mock response for DuckDuckGo using urllib
    mock_main_html = b'<html><script>vqd="12345-67890";</script></html>'
    mock_json_response = b'{"results": [{"image": "https://example.com/ddg1.jpg"}, {"image": "https://example.com/ddg2.jpg"}]}'
    
    # Create mock responses
    mock_response_main = MagicMock()
    mock_response_main.read.return_value = mock_main_html
    mock_response_main.status = 200
    mock_response_main.__enter__ = MagicMock(return_value=mock_response_main)
    mock_response_main.__exit__ = MagicMock(return_value=False)
    
    mock_response_json = MagicMock()
    mock_response_json.read.return_value = mock_json_response
    mock_response_json.status = 200
    mock_response_json.__enter__ = MagicMock(return_value=mock_response_json)
    mock_response_json.__exit__ = MagicMock(return_value=False)
    
    # Create mock opener
    mock_opener = MagicMock()
    mock_opener.open.side_effect = [mock_response_main, mock_response_json]
    mock_build_opener.return_value = mock_opener

    urls = fetch_image_urls("test query", provider="duckduckgo")
    
    assert "https://example.com/ddg1.jpg" in urls
    assert "https://example.com/ddg2.jpg" in urls

@patch('requests.get')
def test_fetch_serpapi(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "images_results": [
            {"original": "https://example.com/serpapi1.jpg"},
            {"original": "https://example.com/serpapi2.png"},
        ]
    }
    mock_get.return_value = mock_response

    urls = fetch_image_urls("test query", provider="serpapi", api_key="fake-key")

    assert "https://example.com/serpapi1.jpg" in urls
    assert "https://example.com/serpapi2.png" in urls
    assert "serpapi.com" in mock_get.call_args[0][0]

def test_fetch_serpapi_no_key():
    urls = fetch_image_urls("test query", provider="serpapi", api_key="")
    assert urls == []

@patch('requests.post')
def test_fetch_serper(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "images": [
            {"imageUrl": "https://example.com/serper1.jpg"},
            {"imageUrl": "https://example.com/serper2.png"},
        ]
    }
    mock_post.return_value = mock_response

    urls = fetch_image_urls("test query", provider="serper", api_key="fake-key")

    assert "https://example.com/serper1.jpg" in urls
    assert "https://example.com/serper2.png" in urls
    assert "serper.dev" in mock_post.call_args[0][0]

def test_fetch_serper_no_key():
    urls = fetch_image_urls("test query", provider="serper", api_key="")
    assert urls == []

@patch('urllib.request.build_opener')
def test_fetch_image_urls_duckduckgo_pagination(mock_build_opener):
    # Mock response for DuckDuckGo with pagination
    mock_main_html = b'<html><script>vqd="pagination-token";</script></html>'
    mock_json_response = b'{"results": [{"image": "https://example.com/paged.jpg"}]}'
    
    mock_response_main = MagicMock()
    mock_response_main.read.return_value = mock_main_html
    mock_response_main.status = 200
    mock_response_main.__enter__ = MagicMock(return_value=mock_response_main)
    mock_response_main.__exit__ = MagicMock(return_value=False)
    
    mock_response_json = MagicMock()
    mock_response_json.read.return_value = mock_json_response
    mock_response_json.status = 200
    mock_response_json.__enter__ = MagicMock(return_value=mock_response_json)
    mock_response_json.__exit__ = MagicMock(return_value=False)
    
    mock_opener = MagicMock()
    mock_opener.open.side_effect = [mock_response_main, mock_response_json]
    mock_build_opener.return_value = mock_opener

    start_offset = 20
    urls = fetch_image_urls("test query", provider="duckduckgo", start=start_offset)
    
    # Check that the second call URL contains the offset parameter
    second_call_url = mock_opener.open.call_args_list[1][0][0].full_url
    assert f"s={start_offset}" in second_call_url
    assert "https://example.com/paged.jpg" in urls
