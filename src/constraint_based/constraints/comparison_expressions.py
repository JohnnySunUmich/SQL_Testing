from .base_expression import Expression
from .literal_expression import Literal
from .variables import Variable, vManager
from typing import Union
from copy import deepcopy


class Comparison_Expression(Expression):
    def __init__(self, lexpr: Union[Variable, Literal, Expression],
                 rexpr: Union[Variable, Literal, Expression, None] = None) -> None:
        self.lexpr = deepcopy(lexpr)
        self.rexpr = deepcopy(rexpr)

    def change_table_id(self, table_id, new_table_id):
        if isinstance(self.lexpr, Variable):
            t_id, tuple_index, column_id = self.lexpr.identity
            if t_id == table_id:
                self.lexpr = vManager.get_variable(new_table_id, tuple_index, column_id)
        if isinstance(self.rexpr, Variable):
            t_id, tuple_index, column_id = self.rexpr.identity
            if t_id == table_id:
                self.rexpr = vManager.get_variable(new_table_id, tuple_index, column_id)


class Less_Expression(Comparison_Expression):
    def __str__(self) -> str:
        return str(self.lexpr) + ' < ' + str(self.rexpr)


class Greater_Expression(Comparison_Expression):
    def __str__(self) -> str:
        return str(self.lexpr) + ' > ' + str(self.rexpr)


class Less_Equal_Expression(Comparison_Expression):
    def __str__(self) -> str:
        return str(self.lexpr) + ' <= ' + str(self.rexpr)


class Greater_Equal_Expression(Comparison_Expression):
    def __str__(self) -> str:
        return str(self.lexpr) + ' >= ' + str(self.rexpr)


class Equal_Expression(Comparison_Expression):
    def __str__(self) -> str:
        return str(self.lexpr) + ' = ' + str(self.rexpr)


class Not_Equal_Expression(Comparison_Expression):
    def __str__(self) -> str:
        return str(self.lexpr) + ' <> ' + str(self.rexpr)


class Is_Null_Expression(Comparison_Expression):
    def __str__(self) -> str:
        return f'{self.lexpr} IS NULL'

    def __repr__(self) -> str:
        return f'NULL({self.lexpr})'
