from .comparison_expressions import *
from .logic_expressions import AND_Expression, NOT_Expression, Is_Null_Expression
from .variables import Variable

def get_comp_expr(operator, lvar, rvar):
    if operator == '=':
        return Equal_Expression(lvar, rvar)
    elif operator == '>':
        return Greater_Expression(lvar, rvar)
    elif operator == '>=':
        return Greater_Equal_Expression(lvar, rvar)
    elif operator == '<':
        return Less_Expression(lvar, rvar)
    elif operator == '<=':
        return Less_Equal_Expression(lvar, rvar)
    elif operator == '<>':
        return Not_Equal_Expression(lvar, rvar)

def get_non_null_comp_expr(operator, lvar, rvar):
    args = []
    if isinstance(lvar, Variable):
        args.append(NOT_Expression([Is_Null_Expression(lvar)]))
    if isinstance(rvar, Variable):
        args.append(NOT_Expression([Is_Null_Expression(rvar)]))
    args.append(get_comp_expr(operator, lvar, rvar))
    return AND_Expression(args)