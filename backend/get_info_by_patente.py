from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time


def get_info_by_patente(patente):

    # Configurar Selenium (modo headless para que no abra ventana)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Abrir la página

    driver.get("https://www.patentechile.com/")
    time.sleep(2)

    # Buscar el campo de patente
    campo_patente = driver.find_element(By.ID, "txtTerm")  # puede ser 'patente' o similar
    campo_patente.clear()
    campo_patente.send_keys(patente)

    # Enviar con Enter
    campo_patente.send_keys(Keys.RETURN)
    time.sleep(3)  # esperar que cargue resultado

    # Obtener el HTML de los resultados
    html = driver.page_source
    driver.quit()

    # Parsear con BeautifulSoup
    soup = BeautifulSoup(html, "lxml")

    # Buscar todas las filas de la tabla
    datos = {}
    for fila in soup.select("tbody tr"):
        celdas = fila.find_all("td")
        if len(celdas) == 2:
            # Primer td = nombre del campo, segundo td = valor
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
