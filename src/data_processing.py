# src/data_processing.py

import pandas as pd
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os
import logging
import time

def setup_driver():
    """Configura e retorna o driver do Selenium em modo headless."""
    try:
        chrome_options = Options()
        # Adicionando argumentos de cabeçalho para evitar detecção
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # Supressão de logs
        logging.getLogger('WDM').setLevel(logging.NOTSET)
        os.environ['WDM_LOG'] = 'False'
        
        # O ChromeDriverManager fará o download do driver automaticamente
        webdriver_service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
        return driver
    except Exception as e:
        # Se você estiver rodando em um ambiente sem GUI (como Colab), isso falhará.
        print(f"Erro ao configurar o WebDriver. Certifique-se de ter o Chrome instalado: {e}")
        return None

def scrape_characters(driver, path):
    """Extrai personagens de uma categoria de livros na wiki da Agatha Christie."""
    if not driver:
        return pd.DataFrame()
        
    driver.get(path)
    time.sleep(2) # Pausa para carregar o conteúdo
    
    # Encontra os links para as categorias dos livros
    categories = driver.find_elements(by=By.CLASS_NAME, value='category-page__member-link')

    books = []
    for category in categories:
        book_url = category.get_attribute('href')
        book_name = category.text
        books.append({'book_name': book_name, "url": book_url})
    
    character_list = []
    for book in books:
        print(f"  > Scraping: {book['book_name']}")
        driver.get(book['url'])
        time.sleep(1) # Pausa para evitar ser bloqueado
        
        # Encontra os links dos personagens dentro da página da categoria
        character_elems = driver.find_elements(by=By.CLASS_NAME, value='category-page__member-link')

        for elem in character_elems:
            character_list.append({'book': book['book_name'], 'character': elem.text})
            
    return pd.DataFrame(character_list)

def scrape_and_prepare_data():
    """Orquestra a raspagem de todas as fontes e junta em um único DataFrame."""
    driver = setup_driver()
    if not driver:
        return pd.DataFrame()
        
    try:
        NOVEM_PATH = "https://agathachristie.fandom.com/wiki/Category:Characters_by_novel"
        SHORT_PATH = "https://agathachristie.fandom.com/wiki/Category:Characters_by_short_story"
        PLAY_PATH = "https://agathachristie.fandom.com/wiki/Category:Characters_by_stage_play"

        # 1. Romances
        print("Raspando personagens de Romances...")
        novels_df = scrape_characters(driver, NOVEM_PATH)
        
        # 2. Novelas (Short Stories)
        print("Raspando personagens de Novelas...")
        short_stories_df = scrape_characters(driver, SHORT_PATH)

        # 3. Peças (Stage Plays)
        print("Raspando personagens de Peças...")
        plays_df = scrape_characters(driver, PLAY_PATH)
        
        # 4. Juntando e limpando
        personagens_df = pd.concat([novels_df, short_stories_df, plays_df], ignore_index=True)
        
        # Removendo a coluna 'book' e mantendo apenas 'character' (único)
        personagens_df = personagens_df[['character']].drop_duplicates()
        
        # 5. Adicionando manualmente personagens chave (de 'faltando.txt')
        missing_chars_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "faltando.txt")
        if os.path.exists(missing_chars_path):
             with open(missing_chars_path, 'r', encoding='utf-8') as f:
                linhas_faltando = f.read().splitlines()
             
             df_faltando = pd.DataFrame(linhas_faltando, columns=['character'])
             personagens_df = pd.concat([personagens_df, df_faltando], ignore_index=True)
             personagens_df = personagens_df.drop_duplicates(subset=['character'])
        
        return personagens_df[['character']]
        
    finally:
        if driver:
            driver.quit()