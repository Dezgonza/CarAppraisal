import re
import json
import asyncio
import urllib.parse
import pandas as pd

from get_google_info import google_scrap
from get_ml_info import ml_scrap, ml_scrap_sync

def custom_split(text, symbol):
    splitted_text = text.split(symbol)
    custom_result = []
    current_text_index = 0
    for i in range(1, len(splitted_text)):
        if len(splitted_text[i]) < 20: continue
        custom_result.append(" ".join(splitted_text[current_text_index:i+1]))
        current_text_index = i+1
    custom_result.append(" ".join(splitted_text[current_text_index:]))
    return custom_result

def extract_custom_info(brand, model, text):
    
    def match_to_num(match):

        if match:
            value_str = match.group(0)
            return int(re.sub(r'[^\d]', '', value_str))
        return None

    # 1️⃣ Extraer año
    year_match = re.search(r'\b(19|20)\d{2}\b', text)
    year = match_to_num(year_match)

    # 2️⃣ Extraer precio
    price_match = re.search(r'\$[\d\.]+', text)
    price_num = match_to_num(price_match)

    # 3️⃣ Extraer kilometraje
    km_match = re.search(r'[\d\.]+\s*km', text, flags=re.IGNORECASE)
    km = match_to_num(km_match)

    # 4️⃣ Capturar versión específica del modelo si existe en el texto
    model_detail = None
    pattern = re.compile(rf'{brand}\s+{model}\s*(.*?)\s*(?:·|\$|$)', flags=re.IGNORECASE)
    m = pattern.search(text)
    if m:
        model_detail = m.group(1).strip() if m.group(1).strip() else None

    # Combinar resultados
    return {
        "year": year,
        "price": price_num,
        "km": km,
        "brand": brand,
        "model": model,
        "model_detail": model_detail
    }

def scrap_chileautos(query, max_pages=5):

    search_query = f"{query} site:chileautos.cl"
    print(f"Buscando: {search_query}")
    
    encoded_query = urllib.parse.quote_plus(search_query)
        
    results = []
    for i in range(max_pages):

        URL_TO_SCRAPE = f"https://www.google.com/search?q={encoded_query}&start={i}"

        cars_info = json.loads(asyncio.run(google_scrap(URL_TO_SCRAPE)))
        results.extend(cars_info)

    return results

async def scrap_chileautos_async(query, max_pages=5):
    search_query = f"{query} site:chileautos.cl"
    print(f"Buscando: {search_query}")
    
    encoded_query = urllib.parse.quote_plus(search_query)

    tasks = []
    for i in range(max_pages):
        url_to_scrape = f"https://www.google.com/search?q={encoded_query}&start={i}"
        tasks.append(google_scrap(url_to_scrape))

    # Ejecutar todas en paralelo
    all_results = await asyncio.gather(*tasks)

    # Flatten + parse
    results = []
    for cars_info in all_results:
        results.extend(json.loads(cars_info))

    return results

def scrap_chileautos_sync(query, max_pages=5):
    import sys
    if sys.platform == 'win32':
        # En Windows, configurar el event loop policy antes de crear el loop
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Crear un nuevo event loop para este thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(scrap_chileautos_async(query, max_pages))
    finally:
        loop.close()

def scrap_pipeline(brand, model, year):

    # ChileAutos Scrap
    query_ca = " ".join([brand,model,str(year)])
    # cars_info = scrap_chileautos(query_ca, 5)
    cars_info = asyncio.run(scrap_chileautos_async(query_ca, 5))
    results = []
    for car_info in cars_info:
        for sub_text in custom_split(car_info['description'], ";"):
            results.append(extract_custom_info(brand, model, sub_text))

    # MercadoLibre Scrap
    query_ml = " ".join([brand,model])
    cars_info = asyncio.run(ml_scrap(query_ml))

    for car_info in json.loads(cars_info):
        for key in ['price','year','km']:
            car_info[key] = int(re.sub(r'[^\d]', '', car_info[key]))
        results.append(car_info)

    return pd.DataFrame(results)

async def scrap_pipeline_async(brand, model, year):
    query_ca = " ".join([brand, model, str(year)])
    query_ml = " ".join([brand, model])

    # Ejecutar ambos scrapes en paralelo usando threads para evitar problemas con subprocess
    cars_ca_task = asyncio.to_thread(scrap_chileautos_sync, query_ca, 5)
    cars_ml_task = asyncio.to_thread(ml_scrap_sync, query_ml)

    cars_ca, cars_ml = await asyncio.gather(cars_ca_task, cars_ml_task)

    results = []

    # Procesar ChileAutos
    for car_info in cars_ca:
        for sub_text in custom_split(car_info['description'], ";"):
            results.append(extract_custom_info(brand, model, sub_text))

    # Procesar MercadoLibre  
    cars_ml_parsed = json.loads(cars_ml) if isinstance(cars_ml, str) else cars_ml
    for car_info in cars_ml_parsed:
        for key in ['price','year','km']:
            try:
                car_info[key] = int(re.sub(r'[^\d]', '', car_info[key]))
            except KeyError:
                continue
        results.append(car_info)

    return pd.DataFrame(results)

if __name__ == "__main__":
    # brand = "honda"
    # model = "civic"
    # year = 2016
    brand = "honda"
    model = "ridgeline rtl 4x4 3.5 aut"
    year = 2023
    
    # df = scrap_pipeline(brand, model, year)
    df = asyncio.run(scrap_pipeline_async(brand, model, year))
    df = df.drop_duplicates()
    # df = scrap_pipeline(brand, model, year)
    print(df[(df.price.notna()) & (df.year==year)])
    print(len(df[(df.price.notna()) & (df.year==year)]))
