
from __future__ import annotations

"""Determine tipos de expressões e valide seus contextos."""

    # 1. Use os símbolos anexados pela resolução de nomes.
    # 2. Determine cada expressão de baixo para cima.
    # 3. Valide operadores, chamadas, comandos e declarações.
    # 4. Anote expressões válidas e acumule os diagnósticos da passagem.

from ast_nodes import (
    Program,
    Expr,
    IntLiteral,
    BoolLiteral,
    IdentifierExpr,
    TypeName,
    UnaryExpr,
    UnaryOperator,
    BinaryExpr,
    BinaryOperator,
    CallExpr,
    VarDecl,
    Block,
    Assignment,
    WhileStmt,
    IfStmt,
    PrintStmt,
    StringLiteral,
    ReturnStmt,
    CallStmt,
)
from semantic_errors import (
    SemanticDiagnostic,
    SemanticError,
    SemanticErrorKind,
)

UNKNOWN = object()

def check_types(program: Program) -> None:
    diagnostics = [] #diagnostics é uma lista onde o analisador semântico vai guardando os erros encontrados
    for function in program.functions: #pega cada funcao do program
        for parameter in function.parameters: #pega paraemtro daquela funcao
            if parameter.type is TypeName.VOID: # paramentro so pode ser int ou bool, void n aceita
                diagnostics.append(SemanticDiagnostic #vai guardar o erro e continuar analisando o resto
                (SemanticErrorKind.VOID_PARAMETER,"parametro não pode ser void",parameter.span,))
        check_block(function.body, function.return_type, diagnostics) #passa comandos da funcao e o tipo que a funcao deve retornar
    if diagnostics:
        raise SemanticError(diagnostics)

def check_call(call, diagnostics):
    symbol = call.metadata["symbol"]
    has_error = False
    if len(call.arguments) != len(symbol.parameter_types):
        diagnostics.append(
            SemanticDiagnostic(
                SemanticErrorKind.ARITY_MISMATCH,
                "quantidade de argumentos incorreta",
                call.span,
            )
        )
        has_error = True

    for i in range(len(call.arguments)):
        argument = call.arguments[i]
        argument_type = check_expr(argument, diagnostics) #descobre tipo

        if argument_type is UNKNOWN: #c ja deu erro internamente
            has_error = True
            continue #passa pro prox arg
        if i < len(symbol.parameter_types): #v c tem a quantidade certa de parametro
            parameter_type = symbol.parameter_types[i] #pega oq a funcao esperava de tipo
            if argument_type is not parameter_type: # c n for, erro 
                diagnostics.append(SemanticDiagnostic(
                    SemanticErrorKind.ARGUMENT_TYPE_MISMATCH,
                    "tipo do argumento diferente do esperado",
                    argument.span,
                    )
                )
                has_error = True

    if has_error:
        return UNKNOWN

    return symbol.type

def check_expr(expr: Expr, diagnostics): #qual o tipo da expressao
    if isinstance(expr, IntLiteral): #vai pegar inteiro
        if expr.value < 0 or expr.value > 2**63 - 1:
            diagnostics.append(
            SemanticDiagnostic(
                SemanticErrorKind.INTEGER_LITERAL_OUT_OF_RANGE,
                "literal inteiro fora do intervalo permitido",
                expr.span,
                )
            )
            return UNKNOWN

        expr.metadata["type"] = TypeName.INT
        return TypeName.INT
    
    if isinstance(expr, BoolLiteral): #vai pegar bool :true or false
        expr.metadata["type"] = TypeName.BOOL
        return TypeName.BOOL
    
    if isinstance(expr, IdentifierExpr): #vai pegar identificador 
        symbol = expr.metadata["symbol"] # pega o símbolo inteiro associado ao identificador
        expr.metadata["type"] = symbol.type #das informações do simbolo, pega somente a infrmação type
        return symbol.type 

    if isinstance(expr, UnaryExpr): #ve c é uma expressao unaria
        operand_type = check_expr(expr.operand, diagnostics) #vai pegar o operando, (- ou !), se for -, sabemos que é int, se for ! é bool
        if operand_type is UNKNOWN:
            return UNKNOWN
        if expr.operator is UnaryOperator.NEGATE: #v c é -, e se é um inteiro, só funciona com inteiros
            if operand_type != TypeName.INT:
                #return None #retornar erro c n for int
                diagnostics.append(SemanticDiagnostic(
                    SemanticErrorKind.INVALID_UNARY_OPERAND,
                     "operador - exige operando int",
                    expr.span,
                    )
                )
                return UNKNOWN
            expr.metadata["type"] = TypeName.INT
            return TypeName.INT

        if expr.operator is UnaryOperator.NOT: #v c é ! 
            if operand_type is not TypeName.BOOL: #c o tipo n for bool é erro
                #return #error
                diagnostics.append(SemanticDiagnostic(
                    SemanticErrorKind.INVALID_UNARY_OPERAND,
                    "operador ! exige operando bool",
                    expr.span,
                    )
                )
                return UNKNOWN
            expr.metadata["type"] = TypeName.BOOL
            return TypeName.BOOL

    if isinstance(expr, BinaryExpr): #expressao possui dois lados e um op binario
        left_type = check_expr(expr.left, diagnostics) #pegamos lado esquerdo
        right_type = check_expr(expr.right, diagnostics) #pegamos lado direito

        if left_type is UNKNOWN or right_type is UNKNOWN:
            return UNKNOWN

        if expr.operator in { #v c o operador pertence
            BinaryOperator.ADD,
            BinaryOperator.SUBTRACT,
            BinaryOperator.MULTIPLY,
            BinaryOperator.DIVIDE,
            BinaryOperator.REMAINDER,
        }:
            if left_type is not TypeName.INT or right_type is not TypeName.INT:  
                diagnostics.append(SemanticDiagnostic(
                    SemanticErrorKind.INVALID_BINARY_OPERANDS,
                    "operador aritmético exige dois operandos int",
                    expr.span,
                    )
                )
                return UNKNOWN
            expr.metadata["type"] = TypeName.INT
            return TypeName.INT

        if expr.operator in { #v c é == ou != , vai ter que dar bool no fim 
            BinaryOperator.EQUAL,
            BinaryOperator.NOT_EQUAL,
            }:
            if (left_type is not right_type or left_type not in {TypeName.INT, TypeName.BOOL}) :#c n for do mesmo tipo, da erro
                    diagnostics.append(SemanticDiagnostic(
                        SemanticErrorKind.INVALID_BINARY_OPERANDS,
                        "== e != exigem operandos do mesmo tipo",
                        expr.span,
                        )
                    )
                    return UNKNOWN

            expr.metadata["type"] = TypeName.BOOL
            return TypeName.BOOL


        if expr.operator in {
            BinaryOperator.LESS,
            BinaryOperator.LESS_EQUAL,
            BinaryOperator.GREATER,
            BinaryOperator.GREATER_EQUAL
            }:

            if left_type is not TypeName.INT or right_type is not TypeName.INT: #precisa ser int , int para aceitar e retornar bool
                diagnostics.append(SemanticDiagnostic(
                    SemanticErrorKind.INVALID_BINARY_OPERANDS,
                    "operador relacional exige dois operandos int",
                    expr.span,
                    )
                )
                return UNKNOWN
            expr.metadata["type"] = TypeName.BOOL
            return TypeName.BOOL

        if expr.operator in {  # && ou ||
            BinaryOperator.LOGICAL_AND, 
            BinaryOperator.LOGICAL_OR,
        }:
            if left_type is not TypeName.BOOL or right_type is not TypeName.BOOL: #ambos os lados precisar ser bool e volta bool
                diagnostics.append(SemanticDiagnostic(
                    SemanticErrorKind.INVALID_BINARY_OPERANDS,
                    "operador lógico exige dois operandos bool",
                    expr.span,
                    )
                )
                return UNKNOWN
            expr.metadata["type"] = TypeName.BOOL
            return TypeName.BOOL #
    if isinstance(expr, CallExpr):
        call_type = check_call(expr, diagnostics)
        symbol = expr.metadata["symbol"]

        if symbol.type is TypeName.VOID: #se a chamada da funcao esta sendo usada como um valor , ela n pode ser void
            diagnostics.append(SemanticDiagnostic(
                SemanticErrorKind.VOID_VALUE_USED,
                "valor void não pode ser usado como expressão",
                expr.span,
                )
            )
            return UNKNOWN

        if call_type is UNKNOWN:
            return UNKNOWN

        expr.metadata["type"] = call_type
        return call_type
        # symbol = expr.metadata["symbol"] #pega o simbolo 
        # if len(expr.arguments) != len(symbol.parameter_types): # v c o parametro é igual ao definido
        #     return None
        # for i in range(len(expr.arguments)): #pegar os parametros
        #     argument = expr.arguments[i] #salva em argument
        #     parameter_type = symbol.parameter_types[i] #salva o tipo que o paramentro deve ser
        #     argument_type = check_expr(argument) #verifica o tipo e colcoa nametype em arguemnt_type
        #     if argument_type is not parameter_type: #compara c o paramentro passado é igual ao tipo que deve ser 
        #         return None
     
        # expr.metadata["type"] = symbol.type
        # return symbol.type

def check_statement(stmt,  return_type, diagnostics):
    if isinstance(stmt, Block):
        check_block(stmt, return_type, diagnostics)
        
    if isinstance(stmt, VarDecl):  # variavel declarada com uma atribuicao 
        if stmt.type is TypeName.VOID: #variavel nm pode ser do tipo void
            diagnostics.append(SemanticDiagnostic(
                SemanticErrorKind.VOID_VARIABLE,
                "variável não pode ser do tipo void",
                stmt.span,
                )
            )
        if stmt.initializer is not None: #v c recebeu um valor incial, c recebeu 
            initializer_type = check_expr(stmt.initializer, diagnostics) #c recebeu um valor, descobre o tipo que ta incializando a variavel
            if (stmt.type is not TypeName.VOID and initializer_type is not UNKNOWN
                and initializer_type is not stmt.type
            ):
                diagnostics.append(SemanticDiagnostic(
                    SemanticErrorKind.INITIALIZER_TYPE_MISMATCH,
                    "tipo do valor inicial diferente do tipo da variável",
                    stmt.initializer.span,
                    )
                )

            
    if isinstance(stmt, Assignment): #quando atribui um valor para um varaivael ja declarada ex: x = 10
        target_type = check_expr(stmt.target, diagnostics) #identificador
        value_type = check_expr(stmt.value, diagnostics) #pega o tipo do valor que vai colocar no identificador
        if (target_type is not UNKNOWN and value_type is not UNKNOWN
            and target_type is not value_type):
            diagnostics.append(SemanticDiagnostic(
                SemanticErrorKind.ASSIGNMENT_TYPE_MISMATCH,
                "tipo atribuído diferente do tipo da variável",
                stmt.value.span,
                )
            )


    if isinstance(stmt, IfStmt): #if
        condition_type = check_expr(stmt.condition, diagnostics) #pega a condicao e verifica c o tipo vai dar bool
        if (condition_type is not UNKNOWN and condition_type is not TypeName.BOOL): # v c a condicao é bool, if so aceita bool
            diagnostics.append(SemanticDiagnostic(
                SemanticErrorKind.CONDITION_TYPE_MISMATCH,
                "condição do if deve ser bool",
                stmt.condition.span,
                )
            )
        
        check_block(stmt.then_block, return_type, diagnostics)
        if stmt.else_block is not None:
            check_block(stmt.else_block,  return_type, diagnostics)


    if isinstance(stmt, WhileStmt): #while (mesma logica do if)
        condition_type = check_expr(stmt.condition,diagnostics)
        if (condition_type is not UNKNOWN and condition_type is not TypeName.BOOL):
            diagnostics.append(SemanticDiagnostic(
                SemanticErrorKind.CONDITION_TYPE_MISMATCH,
                "condição do while deve ser bool",
                stmt.condition.span,
                )
            )
        check_block(stmt.body, return_type, diagnostics) # v os comadnos do while


    if isinstance(stmt, CallStmt):
        call_type = check_call(stmt.call, diagnostics)
        if call_type is not UNKNOWN:
            stmt.call.metadata["type"] = call_type

    if isinstance(stmt, PrintStmt):
        for item in stmt.items: #vai ver todos os termos
            if isinstance(item, StringLiteral): # "......."
                continue

            check_expr(item,diagnostics)

    if isinstance(stmt, ReturnStmt): # v c é um return
        if stmt.value is None: # se for somente return
            if return_type is not TypeName.VOID: #v c a funcao esta pedindo retorno void, c n, erro
                 diagnostics.append(SemanticDiagnostic(
                    SemanticErrorKind.RETURN_MISMATCH,
                    "return sem valor em função que exige retorno",
                    stmt.span,
                    )
                )
        else:
            value_type = check_expr(stmt.value, diagnostics)
            if return_type is TypeName.VOID:
                diagnostics.append(
                    SemanticDiagnostic(
                        SemanticErrorKind.RETURN_MISMATCH,
                        "função void não pode retornar valor",
                        stmt.value.span,
                    )
                )

            elif value_type is not UNKNOWN:
                if value_type is not return_type:
                    diagnostics.append(
                        SemanticDiagnostic(
                            SemanticErrorKind.RETURN_MISMATCH,
                            "tipo retornado diferente do tipo da função",
                            stmt.value.span,
                        )
                    )
def check_block(block: Block,  return_type, diagnostics):
    for stmt in block.statements:
        check_statement(stmt,  return_type, diagnostics)
"""Sabe pela propria AST que IntLiteral é int e BoolLiteral é bool, mas usamos 
check_expr() para transformar todas as expressões em uma forma padronizada de obter seu tipo. 
fazemos isso mais por causa dos identificadores,pq o tipo n vem da AST ele fica no símbolo resolvido anteriormente. 
Com todos retornando um TypeName, conseguimos comparar facilmente...
no IdentifierExpr, o tipo não vem diretamente nesse nó da AST; 
ele é obtido do Symbol que o name_resolver associou a esse nó.
"""