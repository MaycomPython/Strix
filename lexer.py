# lexer.py

import re

class StrixError(Exception):
    """Classe base para todos os erros da linguagem Strix."""
    def __init__(self, mensagem, linha=None, coluna=None, nome_arquivo=None):
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna
        self.nome_arquivo = nome_arquivo
        super().__init__(self.formatar_mensagem())

    def formatar_mensagem(self):
        msg = f"ErroStrix: {self.mensagem}"
        if self.nome_arquivo and self.linha is not None:
            msg += f"\n  Arquivo \"{self.nome_arquivo}\", linha {self.linha}"
        elif self.linha is not None:
            msg += f" na linha {self.linha}, coluna {self.coluna}"
        return msg

class StrixSintaxeError(StrixError):
    """Erro para problemas de sintaxe."""
    def __init__(self, mensagem, linha, coluna, nome_arquivo):
        super().__init__(f"Sintaxe inválida: {mensagem}", linha, coluna, nome_arquivo)


class Token:
    """Representa um token, a menor unidade da linguagem."""
    def __init__(self, tipo, valor, linha, coluna):
        self.tipo = tipo
        self.valor = valor
        self.linha = linha
        self.coluna = coluna

    def __repr__(self):
        return f"Token({self.tipo}, {repr(self.valor)}, L{self.linha}:C{self.coluna})"


class Lexer:
    """
    O Lexer (ou Tokenizer) quebra o código fonte em uma lista de Tokens.
    """
    def __init__(self, codigo, nome_arquivo):
        self.codigo = codigo
        self.nome_arquivo = nome_arquivo
        self.pos = 0
        self.linha = 1
        self.coluna = 1

    def _avancar(self):
        if self.pos < len(self.codigo):
            if self.codigo[self.pos] == '\n':
                self.linha += 1
                self.coluna = 1
            else:
                self.coluna += 1
            self.pos += 1

    def _char_atual(self):
        return self.codigo[self.pos] if self.pos < len(self.codigo) else None

    def _proximo_char(self):
        return self.codigo[self.pos + 1] if self.pos + 1 < len(self.codigo) else None

    def _erro(self, mensagem):
        raise StrixSintaxeError(mensagem, self.linha, self.coluna, self.nome_arquivo)

    def tokenize(self):
        tokens = []
        palavras_chave = {
            'exibir': 'EXIBIR',
            'se': 'SE',
            'senao': 'SENAO',
            'senaose': 'SENAOSE',
            'func': 'FUNC',
            'retornar': 'RETORNAR',
            'digitar': 'DIGITAR',
        }

        while self.pos < len(self.codigo):
            char = self._char_atual()

            if char.isspace():
                self._avancar()
                continue

            if char == '#':
                while self._char_atual() and self._char_atual() != '\n':
                    self._avancar()
                continue
            
            linha_inicio, col_inicio = self.linha, self.coluna

            # Números (inteiros e float)
            if char.isdigit():
                num_str = ''
                while self._char_atual() and self._char_atual().isdigit():
                    num_str += self._char_atual()
                    self._avancar()
                if self._char_atual() == '.':
                    num_str += '.'
                    self._avancar()
                    while self._char_atual() and self._char_atual().isdigit():
                        num_str += self._char_atual()
                        self._avancar()
                    tokens.append(Token('NUMERO_FLOAT', float(num_str), linha_inicio, col_inicio))
                else:
                    tokens.append(Token('NUMERO_INT', int(num_str), linha_inicio, col_inicio))
                continue

            # Identificadores e Palavras-chave
            if char.isalpha() or char == '_':
                id_str = ''
                is_fstring = False
                if char == 'f' and self._proximo_char() in ('"', "'"):
                    is_fstring = True
                    self._avancar() # Pula o 'f'
                    char = self._char_atual() # Agora é a aspa
                
                if not is_fstring:
                    while self._char_atual() and (self._char_atual().isalnum() or self._char_atual() == '_'):
                        id_str += self._char_atual()
                        self._avancar()
                    
                    tipo_token = palavras_chave.get(id_str, 'ID')
                    tokens.append(Token(tipo_token, id_str, linha_inicio, col_inicio))
                    continue

            # Strings e F-Strings
            if char == '"' or char == "'":
                tipo_token = 'FSTRING' if 'f' == self.codigo[self.pos-1] and self.pos > 0 else 'STRING'
                quote = char
                self._avancar()
                str_val = ''
                while self._char_atual() != quote:
                    if self._char_atual() is None:
                        self._erro("String não terminada. Esperando por uma aspa '\"'.")
                    str_val += self._char_atual()
                    self._avancar()
                self._avancar() # Pula a aspa final
                tokens.append(Token(tipo_token, str_val, linha_inicio, col_inicio))
                continue
            
            # Operadores e Símbolos
            if char == '+': tokens.append(Token('MAIS', '+', self.linha, self.coluna)); self._avancar(); continue
            if char == '-': tokens.append(Token('MENOS', '-', self.linha, self.coluna)); self._avancar(); continue
            if char == '*': tokens.append(Token('MULT', '*', self.linha, self.coluna)); self._avancar(); continue
            if char == '/': tokens.append(Token('DIV', '/', self.linha, self.coluna)); self._avancar(); continue
            if char == '(': tokens.append(Token('LPAREN', '(', self.linha, self.coluna)); self._avancar(); continue
            if char == ')': tokens.append(Token('RPAREN', ')', self.linha, self.coluna)); self._avancar(); continue
            if char == '{': tokens.append(Token('LCHAVE', '{', self.linha, self.coluna)); self._avancar(); continue
            if char == '}': tokens.append(Token('RCHAVE', '}', self.linha, self.coluna)); self._avancar(); continue
            if char == ':': tokens.append(Token('DOISPONTOS', ':', self.linha, self.coluna)); self._avancar(); continue
            if char == ',': tokens.append(Token('VIRGULA', ',', self.linha, self.coluna)); self._avancar(); continue

            if char == '=':
                if self._proximo_char() == '=':
                    self._avancar()
                    tokens.append(Token('IGUAL_IGUAL', '==', linha_inicio, col_inicio))
                else:
                    tokens.append(Token('IGUAL', '=', linha_inicio, col_inicio))
                self._avancar()
                continue
            
            if char == '!':
                if self._proximo_char() == '=':
                    self._avancar()
                    tokens.append(Token('DIFERENTE', '!=', linha_inicio, col_inicio))
                    self._avancar()
                    continue
            
            if char == '<':
                if self._proximo_char() == '=':
                    self._avancar()
                    tokens.append(Token('MENOR_IGUAL', '<=', linha_inicio, col_inicio))
                else:
                    tokens.append(Token('MENOR', '<', linha_inicio, col_inicio))
                self._avancar()
                continue

            if char == '>':
                if self._proximo_char() == '=':
                    self._avancar()
                    tokens.append(Token('MAIOR_IGUAL', '>=', linha_inicio, col_inicio))
                else:
                    tokens.append(Token('MAIOR', '>', linha_inicio, col_inicio))
                self._avancar()
                continue

            self._erro(f"Caractere inesperado '{char}'")

        tokens.append(Token('EOF', None, self.linha, self.coluna))
        return tokens