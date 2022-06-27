from time import sleep
from math import ceil
import json
# Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
# BeautifulSoup
from bs4 import BeautifulSoup
# WebDriverManager
from webdriver_manager.chrome import ChromeDriverManager

def pageIsLoaded(driver):
    CLASE_CANT_EMPLEOS = 'sc-tVThF'
    return driver.find_element(by=By.CLASS_NAME, value=CLASE_CANT_EMPLEOS).text.strip() != ''

def launchBrowser(url):
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        driver.get(url)
        wait = WebDriverWait(driver, 10).until(
            lambda driver: pageIsLoaded(driver)
        )
        return driver
    except:
        return None

def getNormalizedSearchWord(searchWord):
    return '-'.join(searchWord.split(' '))

def getUrls(url, cantPages):
    urls = []
    for i in range(2, cantPages+1):
        urls.append(f'{url}?page={i}')
    return urls

def getInnerHTML(driver):
    return driver.find_element(by=By.XPATH, value='/html').get_attribute('innerHTML')

def getBodyContent(driver):
    return driver.find_element(by=By.ID, value='root').get_attribute('innerHTML')

def saveHTML(html, path):
    soup = BeautifulSoup(html, 'html.parser')
    with open(path, 'w') as f:
        f.write(soup.prettify())

def readHTML(path):
    with open(path, 'r') as f:
        return f.read()

def scrapAnuncio(data, anuncio):
    """Data es una lista de dics,
    anuncio es un elemento de bs4"""
    CLASE_CARAC_ANUNCIO = 'sc-gYtlsd'
    d = {}
    d['link'] = anuncio.find('a')['href']
    d['titulo'] = anuncio.find('h2').get_text().strip()
    d['descripcion'] = anuncio.find('p').get_text().strip() if anuncio.find('p') else None
    ubicacion, modalidad = [elem.get_text().strip() for elem in anuncio.find(class_=CLASE_CARAC_ANUNCIO).find_all('h3')]
    d['ubicacion'] = ubicacion
    d['modalidad'] = modalidad
    data.append(d)

def scrapPage(data, page):
    '''Data es una lista de dics,
    page es un elemento de bs4'''
    CLASE_ANUNCIO = 'sc-ghUbLI'
    anuncios = page.find_all(class_=CLASE_ANUNCIO)
    for anuncio in anuncios:
        scrapAnuncio(data, anuncio)

def initScrap(searchWord):
    URL_BASE = 'https://www.bumeran.com.ar/empleos-busqueda-'
    CLASE_CANT_ANUNCIOS = 'sc-tVThF'
    ANUNCIOS_POR_PAGINA = 20

    data = []

    url = URL_BASE + searchWord + '.html'
    driver = launchBrowser(url)
    if not driver: 
        print('Hubieron problemas al cargar la página')
        return

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    cant_anuncios = int(soup.find(class_=CLASE_CANT_ANUNCIOS).get_text().strip())
    if cant_anuncios == 0:
        print('No hay resultados para su búsqueda')
        return
    CANT_PAGINAS = ceil(cant_anuncios / ANUNCIOS_POR_PAGINA)

    ### Scrapear primera pagina
    scrapPage(data, soup)

    ### Scrapear otras paginas
    urls = getUrls(url, CANT_PAGINAS)
    for url in urls:
        sleep(5)
        driver = launchBrowser(url)
        if not driver: 
            print('Hubieron problemas al cargar la página')
            return
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        scrapPage(data, soup)
    driver.quit()
    return data

busqueda = 'python'
busqueda = getNormalizedSearchWord(busqueda)
empleos = initScrap(busqueda)
with open(f'{busqueda}.json', 'w', encoding='utf-8') as f:
    json.dump(empleos, f, ensure_ascii=False, indent=4)
