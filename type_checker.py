
from __future__ import annotations

"""Determine tipos de expressões e valide seus contextos."""

    # 1. Use os símbolos anexados pela resolução de nomes.
    # 2. Determine cada expressão de baixo para cima.
    # 3. Valide operadores, chamadas, comandos e declarações.
    # 4. Anote expressões válidas e acumule os diagnósticos da passagem.

from ast_nodes import ( #classes AST
    Program,
    Expr,
    IntLiteral,
    BoolLiteral,
    IdentifierExpr,
    TypeName,
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

"""Sabemos pela propria AST que IntLiteral é int e BoolLiteral é bool, mas usamos 
check_expr() para transformar todas as expressões em uma forma padronizada de obter seu tipo. 
fazemos isso mais por causa dos identificadores,pq o tipo n vem da AST ele fica no símbolo resolvido anteriormente. 
Com todos retornando um TypeName, conseguimos comparar facilmente...
no IdentifierExpr, o tipo não vem diretamente nesse nó da AST; 
ele é obtido do Symbol que o name_resolver associou a esse nó.
"""