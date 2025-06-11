# strix.py

import sys
from lexer import Lexer
from parser_strix import Parser
from interpreter import Interpreter, StrixError

def main():
    """
    Ponto de entrada principal para o interpretador Strix.
    Executa o processo: Leitura -> Lexer -> Parser -> Interpreter.
    """
    if len(sys.argv) != 2:
        print("Uso: strix <nome_do_arquivo.tx>")
        sys.exit(1)

    caminho_arquivo = sys.argv[1]
    if not caminho_arquivo.endswith('.tx'):
        print("Erro: O arquivo de código fonte deve ter a extensão '.tx'")
        sys.exit(1)

    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            codigo = f.read()
    except FileNotFoundError:
        print(f"Erro: Arquivo '{caminho_arquivo}' não encontrado.")
        sys.exit(1)

    if not codigo.strip():
        # Arquivo vazio, não faz nada
        return

    # Adiciona uma nova linha no final para garantir que o último token seja processado
    codigo += '\n'
    
    try:
        # 1. Lexer: Transforma o código em uma lista de tokens
        lexer = Lexer(codigo, caminho_arquivo)
        tokens = lexer.tokenize()

        # 2. Parser: Constrói uma Árvore de Sintaxe Abstrata (AST) a partir dos tokens
        parser = Parser(tokens)
        arvore = parser.parse()
        
        # Se a árvore for nula (código com apenas comentários/espaços), não executa
        if arvore is None:
            return

        # 3. Interpreter: Executa as instruções da AST
        interpretador = Interpreter()
        interpretador.interpret(arvore)

    except StrixError as e:
        # Captura erros personalizados da linguagem e os exibe
        print(e, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Captura outros erros inesperados do Python
        print(f"Erro inesperado no interpretador: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
