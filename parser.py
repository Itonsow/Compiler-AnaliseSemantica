from __future__ import annotations
from collections.abc import Sequence
from Lexer import Token, TokenKind
from ast_nodes import (
    Block,
    Expr,
    FunctionDecl,
    Node,
    Parameter,
    PrintItem,
    Program,
    SourceSpan,
    Stmt,
    StringLiteral,
    TypeName,
    VarDecl,
    WhileStmt,
    BinaryExpr,
    BinaryOperator,
    UnaryExpr,
    UnaryOperator,
    Assignment,
    CallStmt,
    CallExpr,
    IdentifierExpr,
    IfStmt,
    ReturnStmt,
    PrintStmt,
    IntLiteral,
    BoolLiteral,
)


TYPE_START = {TokenKind.KW_INT, TokenKind.KW_BOOL, TokenKind.KW_VOID} #tipo do token
EXPRESSION_START = { #quais tokens pode iniciar uma expressao
    
    TokenKind.IDENTIFIER,
    TokenKind.INT_LITERAL,
    TokenKind.KW_FALSE,
    TokenKind.KW_TRUE,
    TokenKind.LEFT_PAREN,
    TokenKind.LOGICAL_NOT,
    TokenKind.MINUS,
}
STATEMENT_START = TYPE_START | { ###########
    TokenKind.IDENTIFIER,
    TokenKind.KW_IF,
    TokenKind.KW_WHILE,
    TokenKind.KW_RETURN,
    TokenKind.KW_PRINT,
    TokenKind.LEFT_BRACE,
}


TYPE_BY_TOKEN = {  #dicionario de conversao
    TokenKind.KW_INT: TypeName.INT,
    TokenKind.KW_BOOL: TypeName.BOOL,
    TokenKind.KW_VOID: TypeName.VOID,
}


class ParserError(Exception):  #erro
    def __init__(self, token: Token, expected: set[TokenKind]):
        self.token = token #token que causou o problema
        self.expected = frozenset(expected) #quais tokens seriam permititods inves do token que causou o prob
        super().__init__()

    @property
    def line(self) -> int:
        return self.token.line

    @property
    def column(self) -> int:
        return self.token.column

    def __str__(self) -> str: #erro em mensagem
        names = ", ".join(kind.name for kind in sorted(
            self.expected,
            key=lambda kind: kind.value,
        ))
        return (
            f"erro sintático em {self.line}:{self.column}: esperado {{{names}}}, "
            f"encontrado {self.token.kind.name} ({self.token.lexeme!r})"
        )


class Parser:
    def __init__(self, tokens: Sequence[Token]):  #recebe os tokens produzidos pelo lexer
        self.tokens = list(tokens) #coloca em uma lista
        if not self.tokens:
            raise ValueError("a sequência de tokens deve terminar em EOF") #ve setem eOF, deve aparecer somnte 1 vez e no fim
        if self.tokens[-1].kind is not TokenKind.EOF:
            raise ValueError("o último token deve ser EOF")
        if any(token.kind is TokenKind.EOF for token in self.tokens[:-1]):
            raise ValueError("EOF deve aparecer uma única vez, no final")
        self.current = 0 #comeca em 0

    def peek(self, offset: int = 0) -> Token:  #vai olhar o token atual, sem consukmir ele
        #da pra olhar pra frente com essa funcao, tipo peek(1) (lookahead)
        index = min(self.current + offset, len(self.tokens) - 1)
        return self.tokens[index] #retornar token atual

    def check(self, kind: TokenKind) -> bool: #verifica o tipo do token
        return self.peek().kind is kind #retorna como kind o tipo do token

    def advance(self) -> Token: #pega o token atual(consome) e vai para o proximo  ////////////////////////////////
        token = self.peek() #coloca o token atual em token
        if self.current < len(self.tokens) - 1:
            self.current += 1 #avanca pro proxi
        return token 

    def match(self, *kinds: TokenKind) -> Token | None:  #se for umt token consuma, se n, tudo bem tbm
        if self.peek().kind in kinds:
            return self.advance() 
        return None

    def expect(self, kinds: TokenKind | set[TokenKind]) -> Token:  #espera que o token esteja no lugar certo, c n estiver retirna erro
        expected = kinds if isinstance(kinds, set) else {kinds}
        token = self.peek()  #/////////////////////////
        if token.kind not in expected:
            raise ParserError(token, set(expected))
        return self.advance()

    @staticmethod
    def _token_span(token: Token) -> SourceSpan: #cria um sourcespan pra cada token
        return SourceSpan(
            token.line,
            token.column,
            token.line,
            token.column + len(token.lexeme),
        )

    @staticmethod
    def _start(value: Token | Node) -> tuple[int, int]: #pega posicao incial
        if isinstance(value, Node):
            return value.span.start_line, value.span.start_column
        return value.line, value.column

    @staticmethod
    def _end(value: Token | Node) -> tuple[int, int]: #pega a posicao final 
        if isinstance(value, Node):
            return value.span.end_line, value.span.end_column
        return value.line, value.column + len(value.lexeme)

    @classmethod
    def _span(cls, first: Token | Node, last: Token | Node) -> SourceSpan:
        start_line, start_column = cls._start(first)
        end_line, end_column = cls._end(last)
        return SourceSpan(start_line, start_column, end_line, end_column)

    def parse(self) -> Program: #comela com o simbolo inicial da gramatica
        return self.parse_program()

    # program ::= function* EOF  #*zero ou mais
    def parse_program(self) -> Program:
        start = self.peek()
        functions: list[FunctionDecl] = []
        while self.peek().kind in TYPE_START: #enquanto tiver vai chamando
            functions.append(self.parse_function())
        eof = self.expect(TokenKind.EOF) #espera um EOF no fim
        return Program(functions, span=self._span(start, eof))

    # function ::= type IDENTIFIER ... block
    def parse_function(self) -> FunctionDecl: #reconhece a funcao
        start = self.peek() #guarda token inicial para o span
        return_type = self.parse_type() #consome
        name = self.expect(TokenKind.IDENTIFIER)
        self.expect(TokenKind.LEFT_PAREN)
        parameters = (
            self.parse_parameter_list()
            if self.peek().kind in TYPE_START
            else []
        )
        self.expect(TokenKind.RIGHT_PAREN)
        body = self.parse_block()
        return FunctionDecl(
            return_type,
            name.lexeme,
            parameters,
            body,
            span=self._span(start, body),
        )

    # type ::= KW_INT | KW_BOOL | KW_VOID
    def parse_type(self) -> TypeName: #precisa bater com algm desses 3
        token = self.expect(TYPE_START)
        return TYPE_BY_TOKEN[token.kind] #converte

    def parse_parameter_list(self) -> list[Parameter]:
        #raise NotImplementedError("implemente parameter_list")
        #parameter_list ::= parameter (COMMA parameter)*

        parametros = [self.parse_parameter()] #pega o primeiro parametro
        while self.match(TokenKind.COMMA): # se tiver virgula, consome e vai no loop
            parametros.append(self.parse_parameter()) # pega o proximo parametro

        return parametros # devolve a lista de parametros

    def parse_parameter(self) -> Parameter: #cuida de um parametro
        #raise NotImplementedError("implemente parameter")
        #parameter ::= type IDENTIFIER

        inicio = self.peek() # guarda onde comecou
        tipo = self.parse_type() # reconhece o tipo
        nome = self.expect(TokenKind.IDENTIFIER) # exige o nome da variavel

        return Parameter(tipo, nome.lexeme, span=self._span(inicio, nome)) #retorna o parametro

    def parse_block(self) -> Block: # {}
        #raise NotImplementedError("implemente block")
        #block ::= LEFT_BRACE statement* RIGHT_BRACE
        inicio = self.expect(TokenKind.LEFT_BRACE) # espera o {
        comandos = [] # lista de comandos
        while not self.check(TokenKind.RIGHT_BRACE): #enquanto n for }
            comandos.append(self.parse_statement()) #pega o comando
        fim = self.expect(TokenKind.RIGHT_BRACE) # espera o }
        return Block(comandos, span=self._span(inicio, fim))

    def parse_statement(self) -> Stmt: #controla, olha o token atual e decide oq fazer
        #raise NotImplementedError("implemente statement")
        #statement ::= declaration
        #    | id_or_call_statement
        #    | if_statement
        #    | while_statement
        #    | return_statement
        #    | print_statement
        #    | block
        tipo = self.peek().kind
        if tipo in TYPE_START:  # se comeca com int, bool ou void
            return self.parse_declaration()
        elif tipo == TokenKind.IDENTIFIER: # se comeca com nome(atribuicao ou chamada) 
            return self.parse_id_or_call_statement()  
        elif tipo == TokenKind.KW_IF: # se for if
            return self.parse_if_statement() 
        elif tipo == TokenKind.KW_WHILE: # se for while
            return self.parse_while_statement()
        elif tipo == TokenKind.KW_RETURN: # se for return
            return self.parse_return_statement()
        elif tipo == TokenKind.KW_PRINT: # se for print
            return self.parse_print_statement()
        elif tipo == TokenKind.LEFT_BRACE: # se for { bloco
            return self.parse_block()
        else: # se n for nenhum dos acima, da erro
            raise self.expect(STATEMENT_START) 

    def parse_id_or_call_statement(self) -> Stmt: #ve c é uma chamadna ou =
        #raise NotImplementedError("implemente id_or_call_statement")
        #id_or_call_statement ::= IDENTIFIER (ASSIGN expression | LEFT_PAREN arguments RIGHT_PAREN) SEMICOLON
        nome = self.expect(TokenKind.IDENTIFIER) #pega o nome da variavel

        #caso 1 atribuicao: x = 10;
        if self.match(TokenKind.ASSIGN): #se tiver um =, consome e pega a expressao
            valor = self.parse_expression() #pega a expressao
            fim = self.expect(TokenKind.SEMICOLON) #espera o ; no final
            alvo = IdentifierExpr(nome.lexeme, span=self._token_span(nome)) #cria a variavel que vai receber o valor (lado esquerdo do =)
            return Assignment(alvo, valor, span=self._span(nome, fim)) #retorna a atribuicao

        #caso 2 funcao: registrar(1, 2);
        elif self.match(TokenKind.LEFT_PAREN): #se tiver um (, consome e pega os argumentos
            argumentos = self.parse_arguments() #pega os argumentos
            fecha_parenteses = self.expect(TokenKind.RIGHT_PAREN) #espera o ) no final
            fim = self.expect(TokenKind.SEMICOLON) #espera o ; no final
            chamada = CallExpr(nome.lexeme, argumentos, span=self._span(nome, fecha_parenteses)) #monta a chamada da funcao com os argumentos que tao dentro do ()
            return CallStmt(chamada, span=self._span(nome, fim)) #retorna a chamada
        
        else: #se n for nenhum dos dois, da erro
            raise self.expect({TokenKind.ASSIGN, TokenKind.LEFT_PAREN})

    def parse_declaration(self) -> Stmt: #
        #raise NotImplementedError("implemente declaration")
        #declaration ::= type IDENTIFIER (ASSIGN expression)? SEMICOLON
        inicio = self.peek() #guarda onde comecou
        tipo = self.parse_type() #pega o tipo(int, bool)
        nome = self.expect(TokenKind.IDENTIFIER) #pega o nome da variavel
        valor = None #comeca sem valor
        if self.match(TokenKind.ASSIGN): #se tiver um =, consome e pega a expressao
            valor = self.parse_expression()
        fim = self.expect(TokenKind.SEMICOLON) #espera o ; no final
        return VarDecl(tipo, nome.lexeme, valor, span=self._span(inicio, fim))

    def parse_if_statement(self) -> Stmt: 
        #raise NotImplementedError("implemente if_statement")
        #if_statement ::= KW_IF LEFT_PAREN expression RIGHT_PAREN block (KW_ELSE block)?
        inicio = self.expect(TokenKind.KW_IF) # espera e consome a palavra if
        self.expect(TokenKind.LEFT_PAREN) # espera o (
        condicao = self.parse_expression() #pega a expressao/condicao do if
        self.expect(TokenKind.RIGHT_PAREN) # espera o )
        bloco_if = self.parse_block() # le o bloco de codigo {}
        bloco_else = None #inicia o bloco else como None pois pode ter caso q nao tem
        if self.match(TokenKind.KW_ELSE): #se tiver um else, consome e pega o bloco
            bloco_else = self.parse_block() # le o bloco de codigo {}

        if bloco_else is not None: #se tiver um bloco else, retorna o if com else
            return IfStmt(condicao, bloco_if, bloco_else, span=self._span(inicio, bloco_else))
        else: #se n tiver um bloco else, retorna o if sem else
            return IfStmt(condicao, bloco_if, None, span=self._span(inicio, bloco_if))


    def parse_while_statement(self) -> Stmt:
        #raise NotImplementedError("implemente while_statement")
        #while_statement ::= KW_WHILE LEFT_PAREN expression RIGHT_PAREN block
        inicio = self.expect(TokenKind.KW_WHILE) # espera e consome a palavra while
        self.expect(TokenKind.LEFT_PAREN) # espera o (
        condicao = self.parse_expression() #pega a expressao/condicao do while
        self.expect(TokenKind.RIGHT_PAREN) # espera o )
        corpo = self.parse_block() # le o bloco de codigo {}
        return WhileStmt(condicao, corpo, span=self._span(inicio, corpo)) #retorna o while

    def parse_return_statement(self) -> Stmt:   #reconhecer o comando return
        #raise NotImplementedError("implemente return_statement")
        #return_statement ::= KW_RETURN expression? SEMICOLON  (?- aceita, return; e return x;)
        token_esperado = self.expect(TokenKind.KW_RETURN)
        expressao = None


        if self.peek().kind in EXPRESSION_START: #vai ver c tem alguma expressao dps do return
            expressao = self.parse_expression() #se tiver vai mandar pro expression interpretar ela

        fim = self.expect(TokenKind.SEMICOLON) #dps do return ou da expresssao, deve vir obrigatoriamente um ;
        return ReturnStmt(  #oq vai pra AST
            expressao,
            span  = self._span(token_esperado, fim)
        )


    def parse_print_statement(self) -> Stmt: #reconhece um comando compelto
        #raise NotImplementedError("implemente print_statement")
        #print_statement ::= KW_PRINT LEFT_PAREN print_item (COMMA print_item)* RIGHT_PAREN SEMICOLON #tem que ter no minino uma coisa para printar
        token_inicial_esperado = self.expect(TokenKind.KW_PRINT)

        self.expect(TokenKind.LEFT_PAREN) #dos do print, é esperado um (
        prints = [self.parse_print_item()] #lista dos prints, prints vai ter o primeiro termo do print
        while self.match(TokenKind.COMMA): #vai ver c o token atual é uma virgula
            prints.append(self.parse_print_item()) #se for virgula, tem mais termo, vai la pegar
        self.expect(TokenKind.RIGHT_PAREN) #dps dos termos do print é esperadoum )

        fim = self.expect(TokenKind.SEMICOLON) #é esperado um ; dps do do fechamento do )
        return PrintStmt( 
            prints,
            span = self._span(token_inicial_esperado,fim)
        )


    def parse_print_item(self) -> PrintItem: #vai ver c esta imprindo uma string ou uma expressao
        #print_item ::= expression | string_literals
        if self.check(TokenKind.STRING_LITERAL): #Verifica se o token atual é uma string
            return self.parse_string_literals()
        if self.peek().kind in EXPRESSION_START: #C n é string verifica se é alguma coisa que pode comecar expressao
            return self.parse_expression()#funcao responsalve por expressoes
        tokens_esperados = EXPRESSION_START | {TokenKind.STRING_LITERAL} #se n for nenhuma das duas, erro
        
        raise ParserError( #########
            self.peek(),
            tokens_esperados
        )


    def parse_string_literals(self) -> StringLiteral: #REconhece e transforma uma ou mais string em um unico stringLIteral
        #string_literals ::= STRING_LITERAL+
        token_esperado = self.expect(TokenKind.STRING_LITERAL) #tem que existir pelo menos uma string
        ultimo = token_esperado #como temos somente uma string, ela vai ser o inicio e o fim do span
        valor = token_esperado.value

        while self.check(TokenKind.STRING_LITERAL): #V c tem outra string seguida dessa
            ultimo = self.advance()
            valor += ultimo.value

        return StringLiteral(
            valor,
            span = self._span(token_esperado, ultimo)
        )

    def parse_expression(self) -> Expr:
        #raise NotImplementedError("implemente expression")
        #expression ::= logical_or
        return self.parse_logical_or() # expressao ::= logical_or

    def parse_logical_or(self) -> Expr:
        #raise NotImplementedError("implemente logical_or")
        #logical_or ::= logical_and (LOGICAL_OR logical_and)*
        expr = self.parse_logical_and() #le o lado esquerdo
        while self.match(TokenKind.LOGICAL_OR): #enquanto tiver ||
            direita = self.parse_logical_and() #le o lado direito
            expr = BinaryExpr(BinaryOperator.LOGICAL_OR, expr, direita, span=self._span(expr, direita)) # junta os dois lados
        return expr

    def parse_logical_and(self) -> Expr:
        #raise NotImplementedError("implemente logical_and")
        #logical_and ::= equality (LOGICAL_AND equality)*
        expr = self.parse_equality() #le o lado esquerdo
        while self.match(TokenKind.LOGICAL_AND): #enquanto tiver &&
            direita = self.parse_equality() #le o lado direito
            expr = BinaryExpr(BinaryOperator.LOGICAL_AND, expr, direita, span=self._span(expr, direita)) # junta os dois lados
        return expr

    def parse_equality(self) -> Expr:
        #raise NotImplementedError("implemente equality")
        #equality ::= relational ((EQUAL_EQUAL | NOT_EQUAL) relational)*
        expr = self.parse_relational() #le o lado esquerdo
        operadores = {TokenKind.EQUAL_EQUAL, TokenKind.NOT_EQUAL} #operadores de igualdade
        while self.peek().kind in operadores: #enquanto tiver == ou !=
            token = self.advance() #consome o "==" ou "!="
            if token.kind == TokenKind.EQUAL_EQUAL: #se for ==
                operador = BinaryOperator.EQUAL
            elif token.kind == TokenKind.NOT_EQUAL: #se for !=
                operador = BinaryOperator.NOT_EQUAL
            direita = self.parse_relational() #le o lado direito
            expr = BinaryExpr(operador, expr, direita, span=self._span(expr, direita)) # junta os dois lados
        return expr

    def parse_relational(self) -> Expr:
        #raise NotImplementedError("implemente relational")
        #relational ::= additive ((LESS | LESS_EQUAL | GREATER | GREATER_EQUAL) additive)*
        expr = self.parse_additive() #le o lado esquerdo
        operadores = {TokenKind.LESS: BinaryOperator.LESS, TokenKind.LESS_EQUAL: BinaryOperator.LESS_EQUAL, TokenKind.GREATER: BinaryOperator.GREATER, TokenKind.GREATER_EQUAL: BinaryOperator.GREATER_EQUAL}
        while self.peek().kind in operadores: #enquanto tiver <, <=, >, >=
            token = self.advance() #consome o operador
            operador = operadores[token.kind] #pega o operador
            direita = self.parse_additive() #le o lado direito
            expr = BinaryExpr(operador, expr, direita, span=self._span(expr, direita)) # junta os dois lados
        return expr

    def parse_additive(self) -> Expr:
        #raise NotImplementedError("implemente additive")
        #additive ::= multiplicative ((PLUS | MINUS) multiplicative)*
        expr = self.parse_multiplicative() # le o lado esquerdo
        operadores = {TokenKind.PLUS, TokenKind.MINUS}
        while self.peek().kind in operadores: # enquanto tiver + ou -
            token = self.advance() # consome o "+" ou "-"
            if token.kind == TokenKind.PLUS:
                operador = BinaryOperator.ADD
            else:
                operador = BinaryOperator.SUBTRACT
            direita = self.parse_multiplicative() # le o lado direito
            expr = BinaryExpr(operador, expr, direita, span=self._span(expr, direita))
        return expr

    def parse_multiplicative(self) -> Expr:
        #raise NotImplementedError("implemente multiplicative")
        #multiplicative ::= unary ((STAR | SLASH | PERCENT) unary)*
        expr = self.parse_unary() # le o lado esquerdo
        operadores = {TokenKind.STAR, TokenKind.SLASH, TokenKind.PERCENT}
        while self.peek().kind in operadores: # enquanto tiver *, / ou %
            token = self.advance() # consome o operador
            if token.kind == TokenKind.STAR: # se for *
                operador = BinaryOperator.MULTIPLY
            elif token.kind == TokenKind.SLASH: # se for /
                operador = BinaryOperator.DIVIDE
            else: # se for %
                operador = BinaryOperator.REMAINDER
            direita = self.parse_unary() # le o lado direito
            expr = BinaryExpr(operador, expr, direita, span=self._span(expr, direita)) # junta os dois lados
        return expr

    def parse_unary(self) -> Expr:
        #raise NotImplementedError("implemente unary")
        #unary ::= (LOGICAL_NOT | MINUS) unary | primary
        if self.peek().kind in {TokenKind.LOGICAL_NOT, TokenKind.MINUS}: # comeca com ! ou -
            token = self.advance() # consome o '!' ou '-'
            if token.kind == TokenKind.LOGICAL_NOT: # se for !
                operador = UnaryOperator.NOT
            else: # se for -
                operador = UnaryOperator.NEGATE
            operando = self.parse_unary() #suportar--x ou !!ativo /// MINUS (MINUS  unary) ////// LOGICAL_NOT (LOGICAL_NOT primary) →! ! ativo
            return UnaryExpr(operador, operando, span=self._span(token, operando))

        # se n for ! ou -, chama parse_primary
        return self.parse_primary()


        
    def parse_primary(self) -> Expr: #reconehce as unidades baiscas das expressoes
    # Tipo, x + 10, idade >= 18, quem parse_primary vai ver é o x,10,idade,18
    #cada fucnao vai cuidar de um nivel de "prioridade",  multi, adic
        #primary ::= LEFT_PAREN expression RIGHT_PAREN
        #  | IDENTIFIER (LEFT_PAREN arguments RIGHT_PAREN)?
        #  | INT_LITERAL
        #  | KW_TRUE
        #  | KW_FALSE
        if self.check(TokenKind.LEFT_PAREN): #V c comeca com (
            inicio = self.advance() #consome ( e vai pro prox
            expr = self.parse_expression() #token ta no conteudo entre os (), chama pra tratar a expressao
            fim = self.expect(TokenKind.RIGHT_PAREN) #esperado )
            expr.span = self._span(inicio, fim) #span da expressao começa ( e termina no )
            return expr

        if self.check(TokenKind.IDENTIFIER): #se for identeifcador
            nome = self.advance() #consome o identifcador e vai pro prox

            if self.match(TokenKind.LEFT_PAREN): #v c o identicador antrior é uma funcao ou n
            #se dps do identifcador ter ( é uma chada de funcao
                argumentos = self.parse_arguments() #chama pra tratar os argumetnos
                fim = self.expect(TokenKind.RIGHT_PAREN) #esperado o )

                return CallExpr( #no da chamad de funcao
                    nome.lexeme, #nome fucao
                    argumentos, #lsita de arg
                    span=self._span(nome, fim)
                )

            return IdentifierExpr( # c n for chamada de funcao, retorna o identificador
                nome.lexeme, #nome indetificador
                span=self._token_span(nome)# comeco e fim dele
            )

        if self.check(TokenKind.INT_LITERAL): #v c é numero(int)
            token = self.advance() #consome numero e vai pro prox

            return IntLiteral( #nó do int
                token.value, #valor
                span=self._token_span(token) #posicao do numero
            )

        if self.check(TokenKind.KW_TRUE): #true:
            token = self.advance() #consome e prox

            return BoolLiteral( #No da ast de true
                token.value,
                span=self._token_span(token)
            )

        if self.check(TokenKind.KW_FALSE):
            token = self.advance()

            return BoolLiteral(
                token.value,
                span=self._token_span(token)
            )

        esperado = { #cehgou até aqui, n entrou nenhum if anterior, ent é erro
            TokenKind.LEFT_PAREN,
            TokenKind.IDENTIFIER,
            TokenKind.INT_LITERAL,
            TokenKind.KW_TRUE,
            TokenKind.KW_FALSE,
        }

        raise ParserError(self.peek(), esperado) #mensagem de erro sintatico

    def parse_arguments(self) -> list[Expr]: #argumentos de uma chamada, pode n ter um arguemnto, (*)
        
        #arguments ::= (expression (COMMA expression)*)?
        argumentos = []
        if self.peek().kind not in EXPRESSION_START : #v c pode comecar expressao, c n pode, nenhum agumento
        #token pode ser um expression_start OU um ) (se o peek for ")", nenhum argumetno)
            return argumentos

        argumentos.append(self.parse_expression())

        while self.match(TokenKind.COMMA) :    #c tiver virugla, outro arugmento
            argumentos.append(self.parse_expression())
        return argumentos

