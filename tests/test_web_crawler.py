import pytest
from app.abilities.crawler.web_crawler import WebCrawlerAbility

@pytest.mark.asyncio
async def test_web_crawler_validate():
    crawler = WebCrawlerAbility()
    
    # Test valid parameters
    valid_context = {"url": "https://example.com"}
    assert await crawler.validate(valid_context)
    
    # Test invalid parameters
    invalid_contexts = [
        {},  # Empty dictionary
        {"url": None},  # URL is None
        {"url": 123},  # URL is not a string
    ]
    
    for context in invalid_contexts:
        assert not await crawler.validate(context)

@pytest.mark.asyncio
async def test_web_crawler_execute():
    crawler = WebCrawlerAbility()
    context = {"url": "https://example.com"}
    
    result = await crawler.execute(context)
    
    assert isinstance(result, dict)
    assert "status" in result
    assert "content" in result
    assert isinstance(result["status"], int)
    assert isinstance(result["content"], str)