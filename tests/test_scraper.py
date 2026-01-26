import pytest
from unittest.mock import patch, MagicMock
from src.scraper import fetch_image_urls

@patch('requests.get')
def test_fetch_image_urls_returns_list_of_urls(mock_get):
    # Mock HTML response from Google Images
    # Minimal HTML structure that we expect to parse
    mock_html = """
    <html>
        <body>
            <img src="/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png" alt="Google">
            <table>
                <tr>
                    <td>
                        <a href="/url?q=https://example.com/1"><img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD"></a>
                    </td>
                    <td>
                        <a href="/url?q=https://example.com/2"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:2"></a>
                    </td>
                    <td>
                        <a href="/url?q=https://example.com/3"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:3"></a>
                    </td>
                    <td>
                        <a href="/url?q=https://example.com/4"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:4"></a>
                    </td>
                </tr>
                <tr>
                    <td>
                        <a href="/url?q=https://example.com/5"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:5"></a>
                    </td>
                    <td>
                        <a href="/url?q=https://example.com/6"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:6"></a>
                    </td>
                    <td>
                        <a href="/url?q=https://example.com/7"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:7"></a>
                    </td>
                    <td>
                        <a href="/url?q=https://example.com/8"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:8"></a>
                    </td>
                    <td>
                        <a href="/url?q=https://example.com/9"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:9"></a>
                    </td>
                </tr>
            </table>
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
    assert urls[0].startswith("data:image/jpeg;base64") or urls[0] == "https://encrypted-tbn0.gstatic.com/images?q=tbn:2"

@patch('requests.get')
def test_fetch_image_urls_handles_error(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_get.return_value = mock_response
    
    # We expect an empty list if there's an error status code or exception
    urls = fetch_image_urls("test query")
    assert urls == []

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

@patch('requests.get')
def test_fetch_image_urls_duckduckgo(mock_get):
    # Mock response for DuckDuckGo
    # First call: main page with vqd
    mock_main_html = '<html><script>vqd="12345-67890";</script></html>'
    # Second call: i.js JSON results
    mock_json_response = {
        "results": [
            {"image": "https://example.com/ddg1.jpg"},
            {"image": "https://example.com/ddg2.jpg"}
        ]
    }
    
    mock_response_main = MagicMock()
    mock_response_main.status_code = 200
    mock_response_main.text = mock_main_html
    
    mock_response_json = MagicMock()
    mock_response_json.status_code = 200
    mock_response_json.json.return_value = mock_json_response
    
    mock_get.side_effect = [mock_response_main, mock_response_json]

    urls = fetch_image_urls("test query", provider="duckduckgo")
    
    assert "https://example.com/ddg1.jpg" in urls
    assert "https://example.com/ddg2.jpg" in urls
    assert "duckduckgo.com" in mock_get.call_args_list[0][0][0]
    assert mock_get.call_args_list[1].kwargs['params']['vqd'] == "12345-67890"
