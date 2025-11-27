# src/data_processing.py

import pandas as pd
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os
import logging

def setup_driver():
    """Configura e retorna o driver do Selenium em modo headless."""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")

        # Supressão de logs do WebDriver Manager e Selenium
        logging.getLogger('WDM').setLevel(logging.NOTSET)
        os.environ['WDM_LOG'] = 'False'
        
        webdriver_service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"Erro ao configurar o WebDriver. Certifique-se de ter o Chrome instalado: {e}")
        return None

def scrape_characters(driver, path):
    """
    Função adaptada da 'raspa' do seu raspagem.ipynb para extrair 
    personagens por categoria (romances, novelas, peças).
    """
    if not driver:
        return pd.DataFrame()
        
    driver.get(path)
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
        # Encontra os links dos personagens dentro da página da categoria
        character_elems = driver.find_elements(by=By.CLASS_NAME, value='category-page__member-link')

        for elem in character_elems:
            character_list.append({'book': book['book_name'], 'character': elem.text})
            
    return pd.DataFrame(character_list)

def scrape_and_prepare_data():
    """
    Orquestra a raspagem de todas as fontes e junta em um único DataFrame.
    """
    driver = setup_driver()
    if not driver:
        return pd.DataFrame()
        
    try:
        # Caminhos base
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
        
        # Aplicando a lógica de remoção de duplicatas do seu notebook
        personagens_df = personagens_df[['character']].drop_duplicates()
        
        # 5. Adicionando manualmente personagens chave (de 'faltando.txt')
        # CUIDADO: O 'faltando.txt' deve estar na raiz, ou você precisa ajustar o caminho.
        # Por simplicidade na modularização, esta lógica deve estar no main.py, mas a movi aqui
        # para manter a dependência do `personagens.csv` em um só lugar.
        
        missing_chars_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "faltando.txt")
        if os.path.exists(missing_chars_path):
             with open(missing_chars_path, 'r', encoding='utf-8') as f:
                linhas_faltando = f.read().splitlines()
             
             df_faltando = pd.DataFrame(linhas_faltando, columns=['character'])
             personagens_df = pd.concat([personagens_df, df_faltando], ignore_index=True)
             personagens_df = personagens_df.drop_duplicates(subset=['character'])
             print(f"Total final de personagens após adição manual: {len(personagens_df)}")
        else:
            print("Arquivo 'faltando.txt' não encontrado. Pulando adição manual.")
            
        return personagens_df[['character']]
        
    finally:
        if driver:
            driver.quit()