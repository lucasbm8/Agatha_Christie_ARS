# main.py

import os
import pandas as pd
from src.data_processing import scrape_and_prepare_data
from src.network_analysis import run_network_analysis

# --- Configurações do Projeto ---
# O diretório 'livros' está na raiz do projeto (Agatha_Christie_ARS/livros)
BOOKS_DIR = os.path.join(os.path.dirname(__file__), "livros")
CHARACTERS_FILE = os.path.join(os.path.dirname(__file__), "personagens.csv")
MISSING_CHARS_FILE = os.path.join(os.path.dirname(__file__), "faltando.txt")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def main():
    """
    Função principal para orquestrar a extração de dados e a análise de rede.
    """
    print("--- 1. Extração e Preparação de Dados ---")
    
    # 1.1. Raspagem (Scraping) e Criação de 'personagens.csv'
    # Esta etapa só precisa ser executada se o 'personagens.csv' não existir ou precisar ser atualizado.
    if not os.path.exists(CHARACTERS_FILE):
        print("Executando raspagem de personagens...")
        scraped_df = scrape_and_prepare_data()
        scraped_df.to_csv(CHARACTERS_FILE, index=False, header=False)
        print(f"Lista de personagens salva em: {CHARACTERS_FILE}")
    else:
        print("Arquivo 'personagens.csv' encontrado. Pulando raspagem.")

    # 1.2. Carregar lista final de personagens
    try:
        characters_df = pd.read_csv(CHARACTERS_FILE, header=None, names=['nome_completo'])
        characters_df['sobrenome'] = characters_df['nome_completo'].apply(
            lambda x: x.split(' ', 1)[-1] if ' ' in x else x
        )
        print(f"Total de personagens carregados: {len(characters_df)}")
    except Exception as e:
        print(f"Erro ao carregar o arquivo de personagens: {e}")
        return

    # 1.3. Preencher a lista de assassinos (Gabarito)
    # ATENÇÃO: Este é um gabarito de exemplo. Você deve criar e preencher
    # o arquivo 'data/murderers.csv' (ou 'murderers.xlsx') com a verdade.
    # Exemplo: {'A Caribbean Mystery...txt': 'Tim Kendal', ...}
    
    # Por enquanto, rodaremos a análise de rede para o primeiro livro.
    
    print("\n--- 2. Execução da Análise de Rede para o primeiro livro ---")
    
    # Lista de todos os livros no diretório
    book_files = [b for b in os.scandir(BOOKS_DIR) if b.name.endswith('.txt')]
    
    if not book_files:
        print(f"Nenhum arquivo .txt encontrado em: {BOOKS_DIR}")
        return
        
    # Exemplo: analise o segundo livro ('A Caribbean Mystery')
    # O arquivo 'relacoes.ipynb' usou livros[1], que é o segundo arquivo da lista.
    # Para consistência com o notebook, vou usar o primeiro encontrado no dir 'livros'.
    
    book_path = book_files[1].path # Altere o índice se quiser testar outro livro
    
    run_network_analysis(book_path, characters_df, OUTPUT_DIR)
    
    # O passo final de PREDICAO (Etapa 3) será implementado após a
    # automação da Etapa 2 para todos os livros.
    
if __name__ == "__main__":
    main()