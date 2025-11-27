# main.py

import os
import pandas as pd
from src.gemini_extractor import setup_gemini_client, extract_network_data
from src.network_analysis import run_network_analysis_from_gemini_data

# --- Configurações Globais ---
BASE_DIR = os.path.dirname(__file__)
BOOKS_DIR = os.path.join(BASE_DIR, "livros")
OUTPUT_DIR = os.path.join(BASE_DIR, "output_single_test")

# Dados do Livro de Teste
TARGET_BOOK_FILENAME = 'Hallowe\'en Party_ A Hercule Poi - Agatha Christie.txt'
TARGET_BOOK_PATH = os.path.join(BOOKS_DIR, TARGET_BOOK_FILENAME)

# ATENÇÃO: COLOQUE SUA CHAVE AQUI
GEMINI_API_KEY = "AIzaSyA44oDX5f3e33UFU3C9bUUe7cXeesPBu4w" # <-- ESPAÇO EM BRANCO PARA SUA CHAVE

def main():
    if not GEMINI_API_KEY:
        print("ERRO: Por favor, insira sua chave da API do Gemini no arquivo 'main.py'.")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 1. CONFIGURAÇÃO DA IA
    try:
        gemini_client = setup_gemini_client(GEMINI_API_KEY)
    except Exception as e:
        print(f"ERRO DE CONFIGURAÇÃO: {e}")
        return

    # 2. CARREGAR O LIVRO ALVO
    try:
        with open(TARGET_BOOK_PATH, "r", encoding="utf-8", errors="replace") as f:
            book_text = f.read()
    except FileNotFoundError:
        print(f"ERRO: Arquivo do livro '{TARGET_BOOK_FILENAME}' não encontrado na pasta 'livros'.")
        return
        
    print(f"--- 1. INICIANDO ANÁLISE DE REDE COM GEMINI ---")
    print(f"Livro Alvo: {TARGET_BOOK_FILENAME}")
    
    # 3. EXTRAÇÃO DE DADOS E GABARITO (GEMINI)
    network_data_json = extract_network_data(gemini_client, book_text, TARGET_BOOK_FILENAME)
    
    if not network_data_json:
        print("Falha na extração de dados da rede pelo Gemini. Verifique as mensagens de erro da API.")
        return

    murderer_name = network_data_json.get("murderer_name")
    
    if not murderer_name:
        print("Gemini não conseguiu identificar o assassino ('murderer_name' está vazio).")
        return

    print(f"  > Assassino (Gabarito da IA): {murderer_name}")

    # 4. CONSTRUÇÃO DO GRAFO E CÁLCULO DE MÉTRICAS (NETWORKX)
    metrics_df = run_network_analysis_from_gemini_data(
        network_data_json, 
        TARGET_BOOK_FILENAME, 
        OUTPUT_DIR, 
        murderer_name
    )

    # 5. SALVAMENTO DOS RESULTADOS
    if metrics_df is not None:
        output_csv = os.path.join(OUTPUT_DIR, "hallowe'en_party_metrics_gemini.csv")
        metrics_df.to_csv(output_csv, index=False)
        print(f"\n--- 4. SUCESSO ---")
        print(f"Análise de rede completa e métricas salvas em: {output_csv}")

if __name__ == "__main__":
    main()