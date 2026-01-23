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
    assert urls[0].startswith("data:image/jpeg;base64") or urls[0] == "https://encrypted-tbn0.gstatic.com/images?q=tbn:1"

@patch('requests.get')
def test_fetch_image_urls_handles_error(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    urls = fetch_image_urls("test query")
    assert urls == []
