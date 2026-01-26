import pytest
from unittest.mock import patch, MagicMock
from src.scraper import fetch_image_urls

@patch('requests.get')
def test_fetch_image_urls_returns_list_of_urls(mock_get):
    # Mock HTML response from Google Images with valid image URLs
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
                        <a href="/url?q=https://example.com/2"><img src="https://example.com/image2.jpg"></a>
                    </td>
                    <td>
                        <a href="/url?q=https://example.com/3"><img src="https://example.com/image3.png"></a>
                    </td>
                    <td>
                        <a href="/url?q=https://example.com/4"><img src="https://example.com/image4.jpeg"></a>
                    </td>
                </tr>
                <tr>
                    <td>
                        <a href="/url?q=https://example.com/5"><img src="https://example.com/image5.gif"></a>
                    </td>
                    <td>
                        <a href="/url?q=https://example.com/6"><img src="https://example.com/image6.webp"></a>
                    </td>
                    <td>
                        <a href="/url?q=https://example.com/7"><img src="https://example.com/image7.bmp"></a>
                    </td>
                    <td>
                        <a href="/url?q=https://example.com/8"><img src="https://example.com/image8.jpg"></a>
                    </td>
                    <td>
                        <a href="/url?q=https://example.com/9"><img src="https://example.com/image9.png"></a>
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
    # First URL should be the data URI or one of the example.com images
    assert urls[0].startswith("data:image/jpeg;base64") or "example.com" in urls[0]

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

@patch('requests.Session')
def test_fetch_image_urls_duckduckgo(mock_session_class):
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
    mock_response_main.raise_for_status = MagicMock()
    
    mock_response_json = MagicMock()
    mock_response_json.status_code = 200
    mock_response_json.json.return_value = mock_json_response
    mock_response_json.raise_for_status = MagicMock()
    
    # Create mock session instance
    mock_session = MagicMock()
    mock_session.get.side_effect = [mock_response_main, mock_response_json]
    mock_session_class.return_value = mock_session

    urls = fetch_image_urls("test query", provider="duckduckgo")
    
    assert "https://example.com/ddg1.jpg" in urls
    assert "https://example.com/ddg2.jpg" in urls
    # Check first call was to duckduckgo.com
    assert "duckduckgo.com" in mock_session.get.call_args_list[0][0][0]
    # Check second call has correct vqd
    assert mock_session.get.call_args_list[1][1]['params']['vqd'] == "12345-67890"

@patch('requests.Session')
def test_fetch_image_urls_duckduckgo_pagination(mock_session_class):
    # Mock response for DuckDuckGo with pagination
    mock_main_html = '<html><script>vqd="pagination-token";</script></html>'
    mock_json_response = {"results": [{"image": "https://example.com/paged.jpg"}]}
    
    mock_response_main = MagicMock()
    mock_response_main.status_code = 200
    mock_response_main.text = mock_main_html
    mock_response_main.raise_for_status = MagicMock()
    
    mock_response_json = MagicMock()
    mock_response_json.status_code = 200
    mock_response_json.json.return_value = mock_json_response
    mock_response_json.raise_for_status = MagicMock()
    
    # Create mock session instance
    mock_session = MagicMock()
    mock_session.get.side_effect = [mock_response_main, mock_response_json]
    mock_session_class.return_value = mock_session

    start_offset = 20
    urls = fetch_image_urls("test query", provider="duckduckgo", start=start_offset)
    
    # Check if the 's' parameter (offset) was passed correctly in the second call
    assert mock_session.get.call_args_list[1][1]['params']['s'] == start_offset
    assert "https://example.com/paged.jpg" in urls
