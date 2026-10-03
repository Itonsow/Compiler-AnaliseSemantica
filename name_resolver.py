from __future__ import annotations

from ast_nodes import (
    Program,
    TypeName,
)
from semantic_errors import SemanticDiagnostic, SemanticError, SemanticErrorKind
from symbols import FunctionSymbol, Scope, Symbol, SymbolKind

class ResolvedorNomes:
    def __init__(self):
        self.funcoes = {}
        self.diagnosticos = []

    def resolver(self, programa): # funcao principal do resolvedor de nomes. ela chama as funcoes q vao percorrer a arvore e registrar os simbolos, escopos e nomes usados
        # pega todas as funcoes do programa e registra elas na tabela de simbolos de funcoes
        self.registrar_funcoes(programa)

        # veficia se existe uma funcao main valida
        self.validar_main(programa)

        # percorre todas as funcao do programa. verifica os parametros, os escopos e os nomes usados dentro de cada funcao
        for funcao in programa.functions:
            self.resolver_funcao(funcao)

        #se algm problema foi encontrado, lanca todos os erros encontrados no final
        if self.diagnosticos:
            raise SemanticError(self.diagnosticos)

    def registrar_funcoes(self, programa): # registra todas as funcoes do programa na tabela de simbolos e verifica se ja existe outra funcao com o msm nome
        for funcao in programa.functions:
            tipos_parametros = []

            # coleta os tipos dos parametros da funcao
            for parametro in funcao.parameters:
                tipos_parametros.append(parametro.type)

            simbolo = FunctionSymbol(funcao.name, SymbolKind.FUNCTION, funcao.return_type, funcao, tuple(tipos_parametros))

            funcao.metadata["symbol"] = simbolo

            if funcao.name in self.funcoes: # se ja existe uma funcao com o msm nome, registra erro
                mensagem = f"função '{funcao.name}' já foi declarada"
                self.diagnosticos.append(SemanticDiagnostic(SemanticErrorKind.DUPLICATE_FUNCTION, mensagem, funcao.span))
            else:
                #caso a funcao ainda nao exista, adiciona o simbolo a tabela de simbolos de funcoes
                self.funcoes[funcao.name] = simbolo

    def resolver_funcao(self, funcao): #cria um escopo p cada funcao, registra os parametros e analisa o corpo da funcao
            escopo = Scope(None)

            funcao.body.metadata["scope"] = escopo

            for parametro in funcao.parameters:
                simbolo = Symbol(parametro.name, SymbolKind.PARAMETER, parametro.type, parametro)

                parametro.metadata["symbol"] = simbolo

                # verifica se ja existe outro parametro com o msm nome
                if parametro.name in escopo.symbols:
                    mensagem = f"'{parametro.name}' já foi declarado neste escopo"
                    self.diagnosticos.append(SemanticDiagnostic(SemanticErrorKind.DUPLICATE_DECLARATION, mensagem, parametro.span))
                else:
                    #se o nome nao foi usado, adiciona o parametro ao escopo
                    escopo.symbols[parametro.name] = simbolo

            #dps de registrar os parametros, analisa cada comando q aparece dentro do corpo da funcao
            for comando in funcao.body.statements:
                self.resolver_comando(comando, escopo)

    def validar_main(self, programa): # procura pela funcao main e verifica se ela eh valida
        # procura pela funcao main entre as funcoes do programa
        main = self.funcoes.get("main")

        #se n encontrou uma main, registra erro
        if main is None:
            self.diagnosticos.append(SemanticDiagnostic(SemanticErrorKind.INVALID_MAIN, "o programa deve possuir int main()", programa.span))
            return

        #confere se a main retorna int e nao recebe parametros, senao registra erro
        if main.type != TypeName.INT or main.parameter_types:
            self.diagnosticos.append(SemanticDiagnostic(SemanticErrorKind.INVALID_MAIN, "a assinatura de main deve ser int main()", main.declaration.span))

def resolve_names(program: Program) -> None:
    """Construa escopos, símbolos e vínculos entre usos e declarações."""

    # 1. Colete todas as assinaturas de função.
    # 2. Valide a existência e a assinatura de main.
    # 3. Percorra os corpos em ordem, criando um escopo para cada bloco.
    # 4. Anote declarações, usos e blocos na AST.
    # 5. Acumule os diagnósticos desta passagem antes de lançar SemanticError.
    #raise NotImplementedError("implemente a resolução de nomes")

    resolvedor = ResolvedorNomes()
    resolvedor.resolver(program)
