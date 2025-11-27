# src/network_analysis.py (Versão Adaptada para Gemini)

import pandas as pd
import networkx as nx
import community.community_louvain as community_louvain
from pyvis.network import Network
import os

def run_network_analysis_from_gemini_data(network_data: dict, book_name: str, output_dir: str, murderer_name: str):
    """
    Constrói o grafo e calcula as métricas usando dados fornecidos pelo Gemini.
    """
    
    # 1. Preparação dos Dados (Relacionamentos)
    relacionamentos = network_data['relationships']
    relacionamentos_df = pd.DataFrame(relacionamentos)
    
    if relacionamentos_df.empty:
        print(f"Nenhuma relação de rede fornecida pelo Gemini para {book_name}.")
        return None

    # Normalização dos pesos para NetworkX (coluna 'weight' deve ser 'valor')
    relacionamentos_df = relacionamentos_df.rename(
        columns={'person1': 'origem', 'person2': 'alvo', 'weight': 'valor'}
    )
    
    # 2. Construção do Grafo e Métricas
    G = nx.from_pandas_edgelist(
        relacionamentos_df, 
        source="origem", 
        target='alvo', 
        edge_attr='valor', 
        create_using=nx.Graph()
    )

    # Centralidades
    degree_dict = nx.degree_centrality(G)
    betweenness_dict = nx.betweenness_centrality(G, weight='valor') 
    closeness_dict = nx.closeness_centrality(G, distance='valor') 
    partition = community_louvain.best_partition(G, weight='valor')

    # 3. Criação do DataFrame de Métricas
    metrics_data = []
    for node in G.nodes():
        data = {
            'book_filename': book_name,
            'character_name': node,
            'degree_centrality': degree_dict.get(node, 0),
            'betweenness_centrality': betweenness_dict.get(node, 0),
            'closeness_centrality': closeness_dict.get(node, 0),
            'community_id': partition.get(node, -1),
            'murderer_name': murderer_name,
            'is_murderer': 1 if node == murderer_name else 0 # Define o gabarito
        }
        metrics_data.append(data)

    metrics_df = pd.DataFrame(metrics_data)
    
    assassino_metricas = metrics_df[metrics_df['character_name'] == murderer_name]
    top_degree_char = metrics_df.sort_values(by='degree_centrality', ascending=False).iloc[0]
    
    print("\n--- 3. RESULTADOS ARS CHAVE ---")
    print(f"  > Total de Personagens (Nós): {G.number_of_nodes()}")
    
    if not assassino_metricas.empty:
        print(f"  > CENTRALIDADE DO ASSASSINO ({murderer_name}):")
        print(f"    - Grau: {assassino_metricas['degree_centrality'].iloc[0]:.4f}")
        print(f"    - Intermediação: {assassino_metricas['betweenness_centrality'].iloc[0]:.4f}")
    
    print(f"  > Personagem MAIS CONECTADO (Grau): {top_degree_char['character_name']} ({top_degree_char['degree_centrality']:.4f})")
    
    # Geração da Visualização (Opcional, mas recomendado para o teste)
    try:
        nx.set_node_attributes(G, dict(G.degree), 'size')
        nx.set_node_attributes(G, partition, 'group') 
        net = Network(notebook=True, width="1000px", height="700px", bgcolor='#222222', font_color='white')
        net.from_nx(G)
        
        output_file = os.path.join(output_dir, f"{book_name.split('.')[0]}_network.html")
        net.write_html(output_file)
        print(f"  > Visualização interativa salva em: {output_file}")
        
    except Exception as e:
        print(f"Falha ao gerar visualização Pyvis: {e}")
            
    return metrics_df