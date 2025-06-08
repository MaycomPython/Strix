# parser_strix.py

from lexer import StrixSintaxeError

# --- Nós da Árvore de Sintaxe Abstrata (AST) ---

class AST:
    """Classe base para todos os nós da AST."""
    pass

class Bloco(AST):
    def __init__(self, declaracoes):
        self.declaracoes = declaracoes

class AtribuicaoVar(AST):
    def __init__(self, var, valor):
        self.var = var
        self.valor = valor

class AcessoVar(AST):
    def __init__(self, var):
        self.var = var

class OperacaoBinaria(AST):
    def __init__(self, esq, op, dir):
        self.esq = esq
        self.op = op
        self.dir = dir

class Numero(AST):
    def __init__(self, token):
        self.token = token
        self.valor = token.valor

class String(AST):
    def __init__(self, token):
        self.token = token
        self.valor = token.valor

class FString(AST):
    def __init__(self, token, expressoes):
        self.token = token
        self.valor = token.valor
        self.expressoes = expressoes

class ChamadaExibir(AST):
    def __init__(self, no):
        self.no = no

class ChamadaDigitar(AST):
    def __init__(self, no_prompt):
        self.no_prompt = no_prompt

class DeclaracaoSe(AST):
    def __init__(self, condicao, bloco_se, blocos_senaose, bloco_senao):
        self.condicao = condicao
        self.bloco_se = bloco_se
        self.blocos_senaose = blocos_senaose # lista de (condicao, bloco)
        self.bloco_senao = bloco_senao

class DeclaracaoFunc(AST):
    def __init__(self, nome_func, parametros, corpo):
        self.nome_func = nome_func
        self.parametros = parametros
        self.corpo = corpo

class ChamadaFunc(AST):
    def __init__(self, nome_func, args):
        self.nome_func = nome_func
        self.args = args

class DeclaracaoRetornar(AST):
    def __init__(self, valor):
        self.valor = valor

class NoVazio(AST):
    pass

# --- Parser ---

class Parser:
    """
    O Parser constrói a AST a partir da lista de tokens.
    Implementa um parser de descida recursiva.
    """
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.token_atual = self.tokens[self.pos]

    def _erro(self, mensagem):
        tk = self.token_atual
        raise StrixSintaxeError(mensagem, tk.linha, tk.coluna, None)

    def _avancar(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.token_atual = self.tokens[self.pos]

    def _consumir(self, tipo_token):
        if self.token_atual.tipo == tipo_token:
            token = self.token_atual
            self._avancar()
            return token
        else:
            self._erro(f"Esperava token do tipo '{tipo_token}', mas encontrou '{self.token_atual.tipo}' com valor '{self.token_atual.valor}'")

    def parse(self):
        if self.token_atual.tipo == 'EOF':
            return None
        arvore = self.bloco()
        if self.token_atual.tipo != 'EOF':
            self._erro("Código inesperado após o final do programa.")
        return arvore

    def bloco(self):
        declaracoes = []
        while self.token_atual.tipo not in ('EOF', 'RCHAVE'):
            declaracoes.append(self.declaracao())
        return Bloco(declaracoes)

    def declaracao(self):
        if self.token_atual.tipo == 'EXIBIR':
            return self.declaracao_exibir()
        if self.token_atual.tipo == 'SE':
            return self.declaracao_se()
        if self.token_atual.tipo == 'FUNC':
            return self.declaracao_func()
        if self.token_atual.tipo == 'RETORNAR':
            return self.declaracao_retornar()
        if self.token_atual.tipo == 'ID' and self.tokens[self.pos + 1].tipo == 'IGUAL':
            return self.declaracao_atribuicao()
        return self.expressao()

    def declaracao_atribuicao(self):
        var = AcessoVar(self._consumir('ID'))
        self._consumir('IGUAL')
        valor = self.expressao()
        return AtribuicaoVar(var, valor)

    def declaracao_exibir(self):
        self._consumir('EXIBIR')
        self._consumir('LPAREN')
        no = self.expressao()
        self._consumir('RPAREN')
        return ChamadaExibir(no)

    def declaracao_retornar(self):
        self._consumir('RETORNAR')
        valor = self.expressao()
        return DeclaracaoRetornar(valor)
    
    def declaracao_func(self):
        self._consumir('FUNC')
        nome_func = self._consumir('ID')
        self._consumir('LPAREN')
        parametros = []
        if self.token_atual.tipo == 'ID':
            parametros.append(AcessoVar(self._consumir('ID')))
            while self.token_atual.tipo == 'VIRGULA':
                self._consumir('VIRGULA')
                parametros.append(AcessoVar(self._consumir('ID')))
        self._consumir('RPAREN')
        self._consumir('DOISPONTOS')
        
        # A Strix não usará indentação, mas blocos explícitos com { } ou fim de linha
        # Para simplificar, um bloco de função é apenas uma lista de declarações até o próximo nível
        # (Isso é uma simplificação. Uma linguagem real usaria indentação ou chaves)
        # Vamos assumir que o corpo da função é uma única declaração ou um bloco implícito
        corpo = self.bloco_de_codigo()
        return DeclaracaoFunc(nome_func, parametros, corpo)

    def bloco_de_codigo(self):
        # Simplificação: O "bloco" é apenas a próxima declaração
        # Uma implementação mais robusta usaria indentação ou chaves {}
        declaracoes = []
        # Vamos usar um modelo simplificado onde as funções não são aninhadas facilmente
        # e o corpo termina no fim do arquivo ou em outra declaração de nível superior.
        # Isto é uma limitação deste interpretador simples.
        # Para este exemplo, vamos considerar que um bloco é uma única declaração.
        # O ideal seria usar indentação ou chaves {}.
        # Por simplicidade, faremos com que o corpo seja a próxima declaração.
        declaracoes.append(self.declaracao())
        return Bloco(declaracoes)

    def declaracao_se(self):
        self._consumir('SE')
        condicao = self.expressao()
        self._consumir('DOISPONTOS')
        bloco_se = self.bloco_de_codigo()
        
        blocos_senaose = []
        while self.token_atual.tipo == 'SENAOSE':
            self._consumir('SENAOSE')
            cond_senaose = self.expressao()
            self._consumir('DOISPONTOS')
            bloco_senaose = self.bloco_de_codigo()
            blocos_senaose.append((cond_senaose, bloco_senaose))

        bloco_senao = None
        if self.token_atual.tipo == 'SENAO':
            self._consumir('SENAO')
            self._consumir('DOISPONTOS')
            bloco_senao = self.bloco_de_codigo()

        return DeclaracaoSe(condicao, bloco_se, blocos_senaose, bloco_senao)


    def expressao(self):
        return self.comparacao()

    def comparacao(self):
        no = self.termo_aditivo()
        while self.token_atual.tipo in ('IGUAL_IGUAL', 'DIFERENTE', 'MENOR', 'MENOR_IGUAL', 'MAIOR', 'MAIOR_IGUAL'):
            op = self.token_atual
            self._consumir(op.tipo)
            no = OperacaoBinaria(esq=no, op=op, dir=self.termo_aditivo())
        return no

    def termo_aditivo(self):
        no = self.termo_multiplicativo()
        while self.token_atual.tipo in ('MAIS', 'MENOS'):
            op = self.token_atual
            self._consumir(op.tipo)
            no = OperacaoBinaria(esq=no, op=op, dir=self.termo_multiplicativo())
        return no

    def termo_multiplicativo(self):
        no = self.fator()
        while self.token_atual.tipo in ('MULT', 'DIV'):
            op = self.token_atual
            self._consumir(op.tipo)
            no = OperacaoBinaria(esq=no, op=op, dir=self.fator())
        return no

    def fator(self):
        token = self.token_atual
        if token.tipo == 'NUMERO_INT':
            self._consumir('NUMERO_INT')
            return Numero(token)
        if token.tipo == 'NUMERO_FLOAT':
            self._consumir('NUMERO_FLOAT')
            return Numero(token)
        if token.tipo == 'STRING':
            self._consumir('STRING')
            return String(token)
        if token.tipo == 'FSTRING':
            self._consumir('FSTRING')
            # Extrair expressões dentro de {}
            import re
            expressoes_str = re.findall(r'\{(.*?)\}', token.valor)
            expressoes_nos = []
            # Este é um HACK. Uma solução real precisaria de um sub-parser.
            # Aqui, apenas criamos nós de acesso a variáveis para as expressões.
            for expr in expressoes_str:
                # Simplificação: apenas consideramos acesso a variáveis
                expressoes_nos.append(AcessoVar(Token('ID', expr.strip(), token.linha, token.coluna)))
            return FString(token, expressoes_nos)
        
        if token.tipo == 'ID':
            if self.tokens[self.pos + 1].tipo == 'LPAREN':
                return self.chamada_func()
            return self.acesso_var()

        if token.tipo == 'LPAREN':
            self._consumir('LPAREN')
            no = self.expressao()
            self._consumir('RPAREN')
            return no
        
        if token.tipo == 'DIGITAR':
            self._consumir('DIGITAR')
            self._consumir('LPAREN')
            prompt = self.expressao()
            self._consumir('RPAREN')
            return ChamadaDigitar(prompt)

        self._erro(f"Elemento de expressão inválido. Não esperava um token do tipo '{token.tipo}'.")

    def acesso_var(self):
        token = self._consumir('ID')
        return AcessoVar(token)
        
    def chamada_func(self):
        nome_func = self._consumir('ID')
        self._consumir('LPAREN')
        args = []
        if self.token_atual.tipo != 'RPAREN':
            args.append(self.expressao())
            while self.token_atual.tipo == 'VIRGULA':
                self._consumir('VIRGULA')
                args.append(self.expressao())
        self._consumir('RPAREN')
        return ChamadaFunc(nome_func, args)