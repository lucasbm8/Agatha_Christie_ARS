# src/network_analysis.py

import pandas as pd
import numpy as np
import spacy
import networkx as nx
import community.community_louvain as community_louvain
import matplotlib.pyplot as plt
import os
import io

# Carregar o modelo spaCy apenas uma vez
try:
    NER = spacy.load("en_core_web_sm")
    print("Modelo spaCy 'en_core_web_sm' carregado com sucesso.")
except OSError:
    print("O modelo 'en_core_web_sm' não está instalado. Execute: python -m spacy download en_core_web_sm")
    NER = None

def filter_entity(lista_entidades, personagens_df):
    """Filtra as entidades para incluir apenas nomes completos ou sobrenomes de personagens conhecidos."""
    full_names = personagens_df['nome_completo'].tolist()
    last_names = personagens_df['sobrenome'].tolist()
    
    # A verificação é mais complexa do que apenas o primeiro token, mas vamos manter a lógica base
    # do seu notebook, garantindo que o nome completo OU o sobrenome estejam na lista.
    
    known_entities = []
    for ent in lista_entidades:
        # Limpeza básica da entidade
        cleaned_ent = ent.replace('\n', ' ').strip()
        
        # Verificar se é um nome conhecido (completo ou sobrenome)
        if cleaned_ent in full_names:
            known_entities.append(cleaned_ent)
        elif cleaned_ent in last_names:
            # Precisa garantir que a entidade seja apenas o sobrenome (ex: 'Poirot', 'Marple')
            known_entities.append(cleaned_ent)
        
    return known_entities

def run_network_analysis(book_path, characters_df, output_dir):
    """
    Executa a análise de rede (NER, criação de grafo, métricas) para um único livro.
    """
    if NER is None:
        return

    book_name = os.path.basename(book_path)
    
    # 1. Leitura e Processamento do Livro
    try:
        with open(book_path, "r", encoding="utf-8", errors="replace") as f:
            book_text = f.read()
    except FileNotFoundError:
        print(f"Erro: Arquivo do livro não encontrado em {book_path}")
        return

    # Processamento com NER
    book_doc = NER(book_text)
    
    # 2. Extração de Personagens por Sentença
    sent_entidades_list = []
    for sent in book_doc.sents:
        # NER do spaCy
        all_entities = [ent.text for ent in sent.ents if ent.label_ in ['PERSON', 'ORG', 'NORP']]
        
        # Filtro com a lista de personagens
        known_characters = filter_entity(all_entities, characters_df)
        
        if known_characters:
            # Remove duplicatas consecutivas no nível da sentença
            unique_chars = []
            for char in known_characters:
                if not unique_chars or char != unique_chars[-1]:
                    unique_chars.append(char)
            sent_entidades_list.append({'sentence': sent.text, 'personagens': unique_chars})

    sent_df = pd.DataFrame(sent_entidades_list)
    
    if sent_df.empty:
        print(f"Nenhuma relação de personagem encontrada em {book_name}.")
        return
    
    # 3. Criação de Relacionamentos (Co-ocorrência em Janelas)
    WINDOW_SIZE = 5
    relacionamentos = []

    # Cria relações entre personagens que aparecem em janelas de 5 sentenças.
    for i in range(len(sent_df)):
        # Define o fim da janela (até o final do DF)
        end_index = min(i + WINDOW_SIZE, len(sent_df))
        
        # Combina as listas de personagens em todas as sentenças da janela
        chars_in_window = sum(sent_df['personagens'].iloc[i:end_index].tolist(), [])
        
        # Remove duplicatas consecutivas na janela
        unique_chars = []
        for char in chars_in_window:
            if not unique_chars or char != unique_chars[-1]:
                unique_chars.append(char)
        
        # Cria arestas (relações) entre todos os pares únicos na janela
        if len(unique_chars) > 1:
            for idx, char1 in enumerate(unique_chars):
                for char2 in unique_chars[idx + 1:]:
                    # Garante que a tupla (origem, alvo) esteja ordenada
                    # para contagem correta do peso da aresta.
                    ordered_pair = tuple(sorted((char1, char2)))
                    relacionamentos.append({"origem": ordered_pair[0], "alvo": ordered_pair[1]})

    relacionamentos_df = pd.DataFrame(relacionamentos)
    
    # Agrupa e soma os pesos (número de co-ocorrências)
    relacionamentos_df['valor'] = 1
    relacionamentos_df = relacionamentos_df.groupby(['origem', 'alvo'], as_index=False).sum()

    # 4. Construção do Grafo e Métricas
    G = nx.from_pandas_edgelist(relacionamentos_df, source="origem", target='alvo', edge_attr='valor', create_using=nx.Graph())

    # Centralidades
    degree_dict = nx.degree_centrality(G)
    betweenness_dict = nx.betweenness_centrality(G)
    closeness_dict = nx.closeness_centrality(G)

    # Comunidades (Louvain)
    # Requer o atributo 'valor' (peso) para a partição
    partition = community_louvain.best_partition(G, weight='valor')

    # Adicionando atributos ao grafo
    nx.set_node_attributes(G, degree_dict, 'degree_centrality')
    nx.set_node_attributes(G, betweenness_dict, 'betweenness_centrality')
    nx.set_node_attributes(G, closeness_dict, 'closeness_centrality')
    nx.set_node_attributes(G, partition, 'group')
    
    print(f"Análise de rede concluída para: {book_name}")
    print(f"Nós (Personagens): {G.number_of_nodes()}")
    print(f"Arestas (Relações): {G.number_of_edges()}")

    # 5. Visualização (Salva o HTML para PyVis)
    # Usaremos um arquivo HTML interativo.
    
    try:
        from pyvis.network import Network
        
        # Recria o PyVis Network
        net = Network(notebook=True, width="1000px", height="700px", bgcolor='#222222', font_color='white')
        
        # Define o tamanho do nó baseado no grau
        node_degree = dict(G.degree)
        nx.set_node_attributes(G, node_degree, 'size')
        
        net.from_nx(G)
        
        # Salva o arquivo HTML na pasta 'output'
        output_file = os.path.join(output_dir, f"{book_name.split('.')[0]}_network.html")
        net.write_html(output_file, notebook=True)
        print(f"Visualização de rede salva em: {output_file}")
        
    except ImportError:
        print("Pyvis não está instalado. Pule a geração de HTML. Execute: pip install pyvis")
        
    # 6. Retorna métricas para o DataFrame Mestre (Etapa 3 futura)
    # Por enquanto, apenas imprime o resultado do personagem mais conectado
    
    # Converte métricas para DataFrame para fácil inspeção
    metrics_df = pd.DataFrame(G.nodes(data=True))
    metrics_df = metrics_df.apply(lambda x: x[1] if isinstance(x[1], dict) else x, axis=1, result_type='expand')
    metrics_df = metrics_df.rename(columns={0: 'character_name'})
    
    top_degree_char = metrics_df.sort_values(by='degree_centrality', ascending=False).iloc[0]
    print(f"\nPersonagem com maior Centralidade de Grau:")
    print(f"  > {top_degree_char['character_name']}: {top_degree_char['degree_centrality']:.4f}")