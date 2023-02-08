import pglast.ast
from .constraints.comparison_expressions import *
from .constraints.logic_expressions import *
from .constraints.literal_expression import *
from .constraints.utils import get_non_null_comp_expr, get_comp_expr

table_id = -1


def get_table_id() -> int:
    global table_id
    table_id += 1
    return table_id

def reset_table_id():
    global table_id
    table_id = -1


def A_Const2var(A_Const):
    assert isinstance(A_Const, pglast.ast.A_Const)
    val = A_Const.val
    if isinstance(val, pglast.ast.Integer):
        return Literal(int(val.val))
        # return int(val.val)
    elif isinstance(val, pglast.ast.String):
        return Literal(str(val.val))
        # return str(val.val)
    elif isinstance(val, pglast.ast.Decimal):
        return Literal(float(val.val))
        # return float(val.val)
    else:
        raise TypeError(f"undefined type {val}")


def parse_A_Expr(A_Expr, colrRef2var):
    assert isinstance(A_Expr, pglast.ast.A_Expr)

    # parse expression
    lexpr = A_Expr.lexpr
    rexpr = A_Expr.rexpr
    if isinstance(lexpr, pglast.ast.ColumnRef):
        lvar = colrRef2var(lexpr)
    else:
        assert isinstance(rexpr, pglast.ast.A_Const)
        lvar = A_Const2var(lexpr)

    if isinstance(rexpr, pglast.ast.ColumnRef):
        rvar = colrRef2var(rexpr)
    else:
        assert isinstance(rexpr, pglast.ast.A_Const)
        rvar = A_Const2var(rexpr)

    # parse operator
    name = A_Expr.name
    assert len(name) == 1
    operator = name[0].val

    # location = A_Expr.location

    # construct constraint
    kind = A_Expr.kind
    if kind == 0:
        return get_non_null_comp_expr(operator, lvar, rvar)
    else:
        raise TypeError(f"undefined A_Expr kind {kind}")


def parse_predicate(pglast_predicate, colref2var):
    if isinstance(pglast_predicate, pglast.ast.A_Expr):
        arg = parse_A_Expr(pglast_predicate, colref2var)
        return Id_Expression([arg])
    elif isinstance(pglast_predicate, pglast.ast.BoolExpr):
        raw_args = pglast_predicate.args
        args = []
        for raw_arg in raw_args:
            if isinstance(raw_arg, pglast.ast.A_Expr):
                arg = parse_A_Expr(raw_arg, colref2var)
                args.append(arg)
            elif isinstance(raw_arg, pglast.ast.BoolExpr):
                arg = parse_predicate(raw_arg, colref2var)
                args.append(arg)
            else:
                raise TypeError(f"undefined arg {raw_arg}")

        boolop = pglast_predicate.boolop
        if boolop == 0:  # AND
            return AND_Expression(args)
        elif boolop == 1:  # OR
            return OR_Expression(args)
        elif boolop == 2:  # NOT
            return NOT_Expression(args)
        else:
            raise TypeError(f"undefined boolean operator {boolop}")
    elif pglast_predicate is None:
        return TRUE([])
    else:
        raise TypeError(f"undefined predicate {pglast_predicate}")
