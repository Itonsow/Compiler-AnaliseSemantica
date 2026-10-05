from __future__ import annotations

from ast_nodes import (
    Program,
    TypeName,
    VarDecl,
    Assignment,
    CallStmt,
    IfStmt,
    WhileStmt,
    ReturnStmt,
    PrintStmt,
    Block,
    Expr,
    IdentifierExpr,
    CallExpr,
    BinaryExpr,
    UnaryExpr
)
from semantic_errors import SemanticDiagnostic, SemanticError, SemanticErrorKind
from symbols import FunctionSymbol, Scope, Symbol, SymbolKind

class ResolvedorNomes:
    def __init__(self):
        self.funcoes = {}
        self.diagnosticos = []

    def resolver(self, programa): # funcao principal do resolvedor de nomes. ela chama as funcoes q vao percorrer a arvore e registrar os simbolos, escopos e nomes usados
        # pega todas as funcoes do programa e registra elas na tabela de simbolos de funcoes
        self.registrar_funcoes(programa) #registra primeiro as funcoes e dps analisa o corpo da funcao

        # veficia se existe uma funcao main valida
        self.validar_main(programa) #precisa ser exatamente um return : int ; e nenhuma paramentro

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
                diagnostico = SemanticDiagnostic(
                    kind=SemanticErrorKind.DUPLICATE_FUNCTION,
                    message=mensagem,
                    span=funcao.span,
                )
                self.diagnosticos.append(diagnostico)
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
                    diagnostico = SemanticDiagnostic(
                        kind=SemanticErrorKind.DUPLICATE_DECLARATION,
                        message=mensagem,
                        span=parametro.span,
                    )
                    self.diagnosticos.append(diagnostico)
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
            mensagem = "o programa deve possuir int main()"
            diagnostico = SemanticDiagnostic(
                kind=SemanticErrorKind.INVALID_MAIN,
                message=mensagem,
                span=programa.span,
            )
            self.diagnosticos.append(diagnostico)
            return

        #confere se a main retorna int e nao recebe parametros, senao registra erro
        if main.type != TypeName.INT or main.parameter_types:
            mensagem = "a assinatura de main deve ser int main()"
            diagnostico = SemanticDiagnostic(
                kind=SemanticErrorKind.INVALID_MAIN,
                message=mensagem,
                span=main.declaration.span,
            )
            self.diagnosticos.append(diagnostico)

    def resolver_comando(self, comando, escopo): #verifica o comando e guarda as variaveis no escopo.
        if isinstance(comando, VarDecl):
            simbolo = Symbol(
                name=comando.name,
                kind=SymbolKind.VARIABLE,
                type=comando.type,
                declaration=comando,
            )
            comando.metadata["symbol"] = simbolo
            if comando.name in escopo.symbols:
                mensagem = f"'{comando.name}' já foi declarado neste escopo"
                diagnostico = SemanticDiagnostic(
                    kind=SemanticErrorKind.DUPLICATE_DECLARATION,
                    message=mensagem,
                    span=comando.span,
                )
                self.diagnosticos.append(diagnostico)
            else:
                escopo.symbols[comando.name] = simbolo
    
            if comando.initializer is not None:
                self.resolver_expressao(comando.initializer, escopo)
    
        elif isinstance(comando, Assignment):
            self.resolver_expressao(comando.target, escopo)
            self.resolver_expressao(comando.value, escopo)
    
        elif isinstance(comando, CallStmt):
            self.resolver_expressao(comando.call, escopo)
    
        elif isinstance(comando, IfStmt):
            self.resolver_expressao(comando.condition, escopo)
            self.resolver_comando(comando.then_block, escopo)
            if comando.else_block is not None:
                self.resolver_comando(comando.else_block, escopo)
    
        elif isinstance(comando, WhileStmt):
            self.resolver_expressao(comando.condition, escopo)
            self.resolver_comando(comando.body, escopo)
    
        elif isinstance(comando, ReturnStmt):
            if comando.value is not None:
                self.resolver_expressao(comando.value, escopo)
    
        elif isinstance(comando, PrintStmt):
            for item in comando.items:
                if isinstance(item, Expr):
                    self.resolver_expressao(item, escopo)
    
        elif isinstance(comando, Block):
            novo_escopo = Scope(escopo)
            comando.metadata["scope"] = novo_escopo
    
            for comando_interno in comando.statements:
                self.resolver_comando(comando_interno, novo_escopo)

    def resolver_expressao(self, expressao, escopo): #verifica os nomes q sao usados na expressao e confirma se as variaveis foram declaradas
        if isinstance(expressao, IdentifierExpr):
            simbolo = self.procurar_variavel(expressao.name, escopo)
    
            if simbolo is None:
                mensagem = f"variável '{expressao.name}' não foi declarada"
                diagnostico = SemanticDiagnostic(
                    kind=SemanticErrorKind.UNDECLARED_VARIABLE,
                    message=mensagem,
                    span=expressao.span,
                )
                self.diagnosticos.append(diagnostico)
            else:
                expressao.metadata["symbol"] = simbolo
    
        elif isinstance(expressao, CallExpr):
            simbolo = self.funcoes.get(expressao.name)
    
            if simbolo is None:
                mensagem = f"função '{expressao.name}' não foi declarada"
                diagnostico = SemanticDiagnostic(
                    kind=SemanticErrorKind.UNDECLARED_FUNCTION,
                    message=mensagem,
                    span=expressao.span,
                )
                self.diagnosticos.append(diagnostico)
            else:
                expressao.metadata["symbol"] = simbolo
    
            for argumento in expressao.arguments:
                self.resolver_expressao(argumento, escopo)
    
        elif isinstance(expressao, BinaryExpr):
            self.resolver_expressao(expressao.left, escopo)
            self.resolver_expressao(expressao.right, escopo)
    
        elif isinstance(expressao, UnaryExpr):
            self.resolver_expressao(expressao.operand, escopo)

    def procurar_variavel(self, nome, escopo): #procura uma variavel no escopo atual e no acima
        escopo_atual = escopo
    
        while escopo_atual is not None:
            if nome in escopo_atual.symbols:
                return escopo_atual.symbols[nome]
            escopo_atual = escopo_atual.parent
    
        return None

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
