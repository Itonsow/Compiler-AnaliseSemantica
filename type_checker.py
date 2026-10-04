
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
)


def check_types(program: Program) -> None:
    """Determine tipos de expressões e valide seus contextos."""
    pass

def check_expr(expr: Expr): #qual o tipo da expressao
    if isinstance(expr, IntLiteral): #vai pegar inteiro
        if(expr.value > 2**63 - 1):
            return #erro

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
        operand_type = check_expr(expr.operand) #vai pegar o operando, (- ou !), se for -, sabemos que é int, se for ! é bool
        if expr.operator is UnaryOperator.NEGATE: #v c é -, e se é um inteiro, só funciona com inteiros
            if operand_type != TypeName.INT:
                return None #retornar erro c n for int
            expr.metadata["type"] = TypeName.INT
            return TypeName.INT

        if expr.operator is UnaryOperator.NOT: #v c é ! 
            if operand_type is not TypeName.BOOL: #c o tipo n for bool é erro
                return #error
            expr.metadata["type"] = TypeName.BOOL
            return TypeName.BOOL

    if isinstance(expr, BinaryExpr): #expressao possui dois lados e um op binario
        left_type = check_expr(expr.left) #pegamos lado esquerdo
        right_type = check_expr(expr.right) #pegamos lado direito

        if expr.operator in { #v c o operador pertence
            BinaryOperator.ADD,
            BinaryOperator.SUBTRACT,
            BinaryOperator.MULTIPLY,
            BinaryOperator.DIVIDE,
            BinaryOperator.REMAINDER,
        }:
            if left_type is not TypeName.INT or right_type is not TypeName.INT:  
                return #errorS
            expr.metadata["type"] = TypeName.INT
            return TypeName.INT

        if expr.operator in { #v c é == ou != , vai ter que dar bool no fim 
            BinaryOperator.EQUAL,
            BinaryOperator.NOT_EQUAL,
            }:
            if left_type is not right_type: #c n for do mesmo tipo, da erro
                return None

            expr.metadata["type"] = TypeName.BOOL
            return TypeName.BOOL


        if expr.operator in {
            BinaryOperator.LESS,
            BinaryOperator.LESS_EQUAL,
            BinaryOperator.GREATER,
            BinaryOperator.GREATER_EQUAL
            }:

            if left_type is not TypeName.INT or right_type is not TypeName.INT: #precisa ser int , int para aceitar e retornar bool
                return None
            expr.metadata["type"] = TypeName.BOOL
            return TypeName.BOOL

        if expr.operator in {  # && ou ||
            BinaryOperator.LOGICAL_AND, 
            BinaryOperator.LOGICAL_OR,
        }:
            if left_type is not TypeName.BOOL or right_type is not TypeName.BOOL: #ambos os lados precisar ser bool e volta bool
                return None
            expr.metadata["type"] = TypeName.BOOL
            return TypeName.BOOL #

    if isinstance(expr, CallExpr): #funcao
        symbol = expr.metadata["symbol"] #pega o simbolo 
        if len(expr.arguments) != len(symbol.parameter_types): # v c o parametro é igual ao definido
            return None
        for i in range(len(expr.arguments)): #pegar os parametros
            argument = expr.arguments[i] #salva em argument
            parameter_type = symbol.parameter_types[i] #salva o tipo que o paramentro deve ser
            argument_type = check_expr(argument) #verifica o tipo e colcoa nametype em arguemnt_type
            if argument_type is not parameter_type: #compara c o paramentro passado é igual ao tipo que deve ser 
                return None
            
        expr.metadata["type"] = symbol.type
        return symbol.type

def check_statement(stmt):
    if isinstance(stmt, VarDecl):  # variavel declarada com uma atribuicao 
        if stmt.initializer is not None: #v c recebeu um valor incial, c recebeu 
            initializer_type = check_expr(stmt.initializer) #c recebeu um valor, descobre o tipo que ta incializando a variavel
            if initializer_type is not stmt.type: # se for diferente , ta errado
                return None
    if isinstance(stmt, Assignment): #quando atribui um valor para um varaivael ja declarada ex: x = 10
        target_type = check_expr(stmt.target) #identificador
        value_type = check_expr(stmt.value) #pega o tipo do valor que vai colocar no identificador
        if target_type is not value_type: # c n for igual, error
            return None

    if isinstance(stmt, IfStmt): #if
        condition_type = check_expr(stmt.condition) #pega a condicao e verifica c o tipo vai dar bool
        if condition_type is not TypeName.BOOL: # v c a condicao é bool, if so aceita bool
            return None
        
        check_block(stmt.then_block)
        if stmt.else_block is not None:
            check_block(stmt.else_block)

    if isinstance(stmt, WhileStmt): #while (mesma logica do if)
        condition_type = check_expr(stmt.condition)
        if condition_type is not TypeName.BOOL:
            return None

        check_block(stmt.body) # v os comadnos do while
        
def check_block(block: Block):
    for stmt in block.statements:
        check_statement(stmt)
"""Sabemos pela propria AST que IntLiteral é int e BoolLiteral é bool, mas usamos 
check_expr() para transformar todas as expressões em uma forma padronizada de obter seu tipo. 
fazemos isso mais por causa dos identificadores,pq o tipo n vem da AST ele fica no símbolo resolvido anteriormente. 
Com todos retornando um TypeName, conseguimos comparar facilmente...
no IdentifierExpr, o tipo não vem diretamente nesse nó da AST; 
ele é obtido do Symbol que o name_resolver associou a esse nó.
"""