from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy


async def ml_scrap(query):
    browser_conf = BrowserConfig(headless=True)  # or False to see the browser

    schema = {
        "name": "Available cars",
        "baseSelector": "ol.ui-search-layout > li.ui-search-layout__item",
        "fields": [
            {
                "name": "model",
                "selector": "a.poly-component__title",
                "type": "text",
            },
            {
                "name": "price",
                "selector": "span.andes-money-amount__fraction",
                "type": "text",
            },
            {
                "name": "year",
                "selector": "ul.poly-attributes_list > li:first-child",
                "type": "text",
            },
            {
                "name": "km",
                "selector": "ul.poly-attributes_list > li:last-child",
                "type": "text",
            },
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    async with AsyncWebCrawler(config=browser_conf) as crawler:

        # Paso 1: escribir query
        config = CrawlerRunConfig(
            js_code=[f"""
            const input = document.querySelector('input.nav-search-input');
            if (input) {{
                input.value = '{query}';
                return {{ queryValue: input.value }};
            }}
            """,
            "document.querySelector('form.nav-search').submit();"],
            extraction_strategy=extraction_strategy,
            # wait_for="networkidle",
            cache_mode=CacheMode.BYPASS,
        )
        result = await crawler.arun(url="https://www.mercadolibre.cl/", config=config)

        # cars_info = json.loads(result.extracted_content)
        # print(result.extracted_content)
        # print(f"Successfully extracted {len(courses)} courses")
        # print(result.markdown)
        # print(result.url)
        return result.extracted_content

def ml_scrap_sync(query):
    import asyncio
    import sys
    
    if sys.platform == 'win32':
        # En Windows, configurar el event loop policy antes de crear el loop
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Crear un nuevo event loop para este thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(ml_scrap(query))
    finally:
        loop.close()

if __name__ == "__main__":
    import json
    import asyncio
    query="honda civic"
    cars_info = asyncio.run(ml_scrap(query))
    print(json.loads(cars_info))
