from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode
)
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy


async def google_scrap(url):
    import asyncio
    import sys
    
    # Fix para Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    browser_conf = BrowserConfig(headless=True)  # or False to see the browser

    schema = {
        "name": "Available cars",
        "baseSelector": "#rso > div",
        "fields": [
            {
                "name": "description",
                "selector": "span:has(em)",# :not(em)",
                "type": "text",
                "all": False
            }
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    async with AsyncWebCrawler(config=browser_conf) as crawler:

        # Paso 1: escribir query
        config = CrawlerRunConfig(
            extraction_strategy=extraction_strategy,
            # wait_for="networkidle",
            cache_mode=CacheMode.BYPASS,
        )
        result = await crawler.arun(url=url, config=config)

        # print(result.extracted_content)
        # print(f"Successfully extracted {len(courses)} courses")
        # print(result.markdown)
        # print(result.url)
        return result.extracted_content

if __name__ == "__main__":
    import urllib.parse
    import asyncio
    import json
    query = "honda civic 2016"
    search_query = f"{query} site:chileautos.cl"
    encoded_query = urllib.parse.quote_plus(search_query)
        
    start = 0

    print(f"Buscando: {search_query}")

    URL_TO_SCRAPE = f"https://www.google.com/search?q={encoded_query}&start={start}"
    
    cars_info = asyncio.run(google_scrap(URL_TO_SCRAPE))
    print(json.loads(cars_info))
