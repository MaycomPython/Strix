# interpreter.py

from lexer import StrixError
import re

class StrixRuntimeError(StrixError):
    """Erro para problemas em tempo de execução."""
    def __init__(self, mensagem, token):
        linha = token.linha if token else None
        coluna = token.coluna if token else None
        super().__init__(f"Erro de Execução: {mensagem}", linha, coluna, None)

class ReturnSignal(Exception):
    """Sinal usado para implementar a declaração 'retornar'."""
    def __init__(self, valor):
        self.valor = valor

class Funcao:
    """Representa uma função definida pelo usuário."""
    def __init__(self, declaracao, ambiente_fechado):
        self.declaracao = declaracao
        self.ambiente_fechado = ambiente_fechado # O ambiente onde a função foi criada

    def chamar(self, interpretador, argumentos):
        if len(argumentos) != len(self.declaracao.parametros):
            raise StrixRuntimeError(
                f"Função '{self.declaracao.nome_func.valor}' esperava "
                f"{len(self.declaracao.parametros)} argumentos, mas recebeu {len(argumentos)}.",
                self.declaracao.nome_func
            )
        
        # Cria um novo ambiente para a execução da função
        ambiente_chamada = Ambiente(enclosing=self.ambiente_fechado)
        
        # Mapeia os argumentos para os nomes dos parâmetros no novo ambiente
        for param_no, arg_valor in zip(self.declaracao.parametros, argumentos):
            ambiente_chamada.definir(param_no.var.valor, arg_valor)

        try:
            # Executa o corpo da função no novo ambiente
            interpretador.executar_bloco(self.declaracao.corpo, ambiente_chamada)
        except ReturnSignal as ret:
            return ret.valor
        
        # Funções sem 'retornar' explícito retornam nulo (None)
        return None


class Ambiente:
    """Gerencia os escopos de variáveis (ambiente de execução)."""
    def __init__(self, enclosing=None):
        self.valores = {}
        self.enclosing = enclosing

    def definir(self, nome, valor):
        self.valores[nome] = valor

    def obter(self, token_var):
        nome = token_var.valor
        if nome in self.valores:
            return self.valores[nome]
        if self.enclosing is not None:
            return self.enclosing.obter(token_var)
        raise StrixRuntimeError(f"Variável '{nome}' não foi definida.", token_var)

    def atribuir(self, token_var, valor):
        nome = token_var.valor
        if nome in self.valores:
            self.valores[nome] = valor
            return
        if self.enclosing is not None:
            self.enclosing.atribuir(token_var, valor)
            return
        raise StrixRuntimeError(f"Variável '{nome}' não foi definida para atribuição.", token_var)


class Interpreter:
    """
    Executa o código Strix caminhando pela AST (Árvore de Sintaxe Abstrata).
    """
    def __init__(self):
        self.ambiente = Ambiente()

    def interpret(self, arvore):
        return self.executar(arvore)

    def executar(self, no):
        # Padrão Visitor: chama o método correspondente ao tipo do nó
        nome_metodo = f'visitar_{type(no).__name__}'
        visitante = getattr(self, nome_metodo, self.visitante_generico)
        return visitante(no)

    def visitante_generico(self, no):
        raise Exception(f"Nenhum método 'visitar_{type(no).__name__}' definido")

    def executar_bloco(self, bloco, ambiente):
        ambiente_anterior = self.ambiente
        self.ambiente = ambiente
        try:
            for declaracao in bloco.declaracoes:
                self.executar(declaracao)
        finally:
            self.ambiente = ambiente_anterior
    
    def visitar_Bloco(self, no):
        for declaracao in no.declaracoes:
            self.executar(declaracao)

    def visitar_AtribuicaoVar(self, no):
        nome_var = no.var.var.valor
        valor = self.executar(no.valor)
        self.ambiente.definir(nome_var, valor)
        return valor
    
    def visitar_AcessoVar(self, no):
        return self.ambiente.obter(no.var)

    def visitar_Numero(self, no):
        return no.valor
    
    def visitar_String(self, no):
        return no.valor

    def visitar_FString(self, no):
        template = no.valor
        valores_expr = {}
        for expr_no in no.expressoes:
            # A chave é o nome da variável no template (ex: "nome")
            chave = expr_no.var.valor
            # O valor é o resultado da execução do nó (ex: "Mundo")
            valores_expr[chave] = self.executar(expr_no)

        # Substitui {variavel} pelo seu valor
        # Esta é uma forma simples, mas funcional
        resultado = template
        for chave, valor in valores_expr.items():
            resultado = resultado.replace(f"{{{chave}}}", str(valor))
        
        return resultado


    def visitar_ChamadaExibir(self, no):
        valor = self.executar(no.no)
        print(valor)

    def visitar_ChamadaDigitar(self, no):
        prompt = self.executar(no.no_prompt)
        return input(prompt)

    def visitar_DeclaracaoSe(self, no):
        if self._eh_verdadeiro(self.executar(no.condicao)):
            self.executar(no.bloco_se)
            return

        for cond_senaose, bloco_senaose in no.blocos_senaose:
            if self._eh_verdadeiro(self.executar(cond_senaose)):
                self.executar(bloco_senaose)
                return

        if no.bloco_senao:
            self.executar(no.bloco_senao)

    def visitar_DeclaracaoFunc(self, no):
        nome_func = no.nome_func.valor
        funcao = Funcao(no, self.ambiente)
        self.ambiente.definir(nome_func, funcao)

    def visitar_ChamadaFunc(self, no):
        nome_func_token = no.nome_func
        funcao = self.ambiente.obter(nome_func_token)

        if not isinstance(funcao, Funcao):
            raise StrixRuntimeError(f"'{nome_func_token.valor}' não é uma função.", nome_func_token)
        
        argumentos = [self.executar(arg) for arg in no.args]
        return funcao.chamar(self, argumentos)

    def visitar_DeclaracaoRetornar(self, no):
        valor = self.executar(no.valor)
        raise ReturnSignal(valor)

    def _eh_verdadeiro(self, valor):
        if valor is None:
            return False
        if isinstance(valor, bool):
            return valor
        if isinstance(valor, (int, float)):
            return valor != 0
        return True # Strings não vazias, listas, etc.

    def visitar_OperacaoBinaria(self, no):
        esq = self.executar(no.esq)
        dir = self.executar(no.dir)
        op = no.op.tipo

        # Operações Aritméticas
        if op == 'MAIS':
            if isinstance(esq, (int, float)) and isinstance(dir, (int, float)):
                return esq + dir
            if isinstance(esq, str) or isinstance(dir, str):
                return str(esq) + str(dir)
            raise StrixRuntimeError("Operação '+' inválida entre os tipos fornecidos.", no.op)
        if op == 'MENOS': return esq - dir
        if op == 'MULT': return esq * dir
        if op == 'DIV': 
            if dir == 0:
                raise StrixRuntimeError("Divisão por zero.", no.op)
            return esq / dir

        # Operações de Comparação
        if op == 'IGUAL_IGUAL': return esq == dir
        if op == 'DIFERENTE': return esq != dir
        if op == 'MENOR': return esq < dir
        if op == 'MENOR_IGUAL': return esq <= dir
        if op == 'MAIOR': return esq > dir
        if op == 'MAIOR_IGUAL': return esq >= dir