import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

def get_info_by_patente(patente):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    if sys.platform == "win32":
        # Windows: usar ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
    else:
        # Linux / Docker: usar Chromium instalado
        options.binary_location = "/usr/bin/chromium"
        driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.patentechile.com/")
        time.sleep(2)

        driver.save_screenshot("patente.png")

        campo_patente = driver.find_element(By.ID, "txtTerm")
        campo_patente.clear()
        campo_patente.send_keys(patente)
        campo_patente.send_keys(Keys.RETURN)
        time.sleep(3)

        html = driver.page_source

    finally:
        driver.quit()

    # Parsear con BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    datos = {}
    for fila in soup.select("tbody tr"):
        celdas = fila.find_all("td")
        if len(celdas) == 2:
            campo = celdas[0].get_text(strip=True).replace(":", "")
            valor = celdas[1].get_text(strip=True)
            datos[campo] = valor

    return datos


if __name__ == "__main__":
    patente = 'SGXR42'
    datos = get_info_by_patente(patente)
    
    print(f"Resultado para {patente}:")
    for k, v in datos.items():
        if not k: continue
        print(f"{k}: {v}")
