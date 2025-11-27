# src/gemini_extractor.py

import json
from google import genai
from google.genai import types

# Estrutura JSON de Retorno Esperada (para o Gemini):
# {
#   "murderer_name": "Nome Completo do Assassino",
#   "relationships": [
#     {"person1": "Nome A", "person2": "Nome B", "weight": 5},
#     {"person1": "Nome X", "person2": "Nome Y", "weight": 12}
#   ]
# }

def setup_gemini_client(api_key: str):
    """Configura e retorna o cliente Gemini."""
    if not api_key:
        raise ValueError("A chave da API do Gemini não pode ser vazia.")
    try:
        # Usa a chave fornecida para inicializar o cliente
        client = genai.Client(api_key=api_key)
        return client
    except Exception as e:
        raise ConnectionError(f"Falha ao inicializar o cliente Gemini: {e}")

def extract_network_data(client: genai.Client, book_text: str, book_name: str) -> dict:
    """
    Usa o Gemini para extrair a rede de relacionamentos e o assassino (ground truth).
    """
    print("  > Enviando texto para Gemini para extração de rede e gabarito...")
    
    # 1. Definição da Estrutura JSON de Saída
    json_schema = {
        "type": "object",
        "properties": {
            "murderer_name": {"type": "string", "description": "O nome completo do assassino revelado no final do livro."},
            "relationships": {
                "type": "array",
                "description": "Uma lista de pares de personagens com o peso da interação.",
                "items": {
                    "type": "object",
                    "properties": {
                        "person1": {"type": "string"},
                        "person2": {"type": "string"},
                        "weight": {"type": "integer", "description": "A frequência ou força da relação (contagem de interações)."
                        }
                    },
                    "required": ["person1", "person2", "weight"]
                }
            }
        },
        "required": ["murderer_name", "relationships"]
    }
    
    # 2. Definição do Prompt de Engenharia
    prompt = f"""
    Analise o texto do livro '{book_name}' fornecido abaixo. Sua tarefa é extrair as relações de co-ocorrência e o gabarito do mistério.
    
    Instruções Rigorosas:
    1. RELACIONAMENTOS: Identifique todos os pares de personagens que interagem (conversam, investigam juntos) ou são frequentemente mencionados no mesmo parágrafo/contexto. O 'weight' deve ser uma estimativa da frequência de interação (uma contagem simples ou nota de 1 a 10).
    2. NOME DO ASSASSINO: Baseado EXCLUSIVAMENTE no conteúdo do livro (o 'ground truth' da história), identifique o nome COMPLETO do assassino. Se houver co-conspiradores, liste o principal ou o mais ativo.
    3. FORMATO: A saída deve ser APENAS o objeto JSON, estritamente conforme o schema fornecido.
    
    TEXTO DO LIVRO:
    ---
    {book_text[:20000]} 
    ---
    """ # Limita o texto a 20k chars para evitar custos excessivos/limites de token

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=json_schema,
                temperature=0.0
            )
        )
        
        # A resposta é uma string JSON, precisamos carregá-la.
        data = json.loads(response.text)
        print("  > Extração JSON do Gemini concluída.")
        return data

    except Exception as e:
        print(f"!!! ERRO na chamada da API Gemini: {e}")
        return None