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
# ... (continuação do código em main.py)

    # 1.3. Preencher a lista de assassinos (Gabarito)
    # Exemplo de Gabarito (VOCÊ DEVE CRIAR E PREENCHER ESTE ARQUIVO)
    # Por enquanto, criaremos um DataFrame mock para que o código rode.
    # Exemplo:
    # livro,assassino,is_murderer
    # A Caribbean Mystery_ A Miss Mar - Agatha Christie.txt,Tim Kendal,1
    # 4_50 From Paddington - Agatha Christie.txt,Emma Crackenthorpe,1

    # DataFrame de Exemplo (Mock) para não quebrar a lógica futura
    murderers_data = {
        'book_filename': [f.name for f in book_files],
        'murderer_name': ['Unknown'] * len(book_files), # Substitua por nomes reais
        'is_murderer': [0] * len(book_files) # 0 = Não, 1 = Sim (Se o personagem for o assassino)
    }
    murderers_df = pd.DataFrame(murderers_data)


    print("\n--- 2. Execução da Análise de Rede para Todos os Livros ---")

    all_metrics = []
    
    # Itera sobre todos os arquivos .txt no diretório
    for book_file in book_files:
        book_path = book_file.path
        book_filename = book_file.name
        
        print(f"\n[Processando] {book_filename}...")
        
        # A função run_network_analysis agora retorna as métricas em um DataFrame
        metrics_df = run_network_analysis(book_path, characters_df, OUTPUT_DIR)
        
        if metrics_df is not None:
            # Adiciona metadados do livro
            metrics_df['book_filename'] = book_filename
            
            # Tenta unir com a lista de assassinos (Etapa de Modelagem)
            # Como a lista de assassinos é um MOCK, o campo 'is_murderer' será preenchido depois
            
            all_metrics.append(metrics_df)

    # Cria o DataFrame Mestre
    if all_metrics:
        master_df = pd.concat(all_metrics, ignore_index=True)
        master_df = master_df.merge(
            murderers_df[['book_filename', 'murderer_name']],
            on='book_filename',
            how='left'
        )
        
        # Cria a coluna 'is_murderer' (0 ou 1)
        master_df['is_murderer'] = np.where(
            master_df['character_name'] == master_df['murderer_name'], 
            1, 
            0
        )
        
        output_csv = os.path.join(OUTPUT_DIR, "master_network_metrics.csv")
        master_df.to_csv(output_csv, index=False)
        print(f"\n--- Análise Final Concluída ---")
        print(f"DataFrame mestre com {len(master_df)} linhas salvo em: {output_csv}")

    else:
        print("\nNenhuma métrica de rede foi gerada com sucesso.")