from z3 import *

from .constraints.variables import Variable
from .utils.type_convertion import date2int
from .scope import Scope


class Visitor:
    def __init__(self, scope=None):
        if scope is None:
            self.scope = Scope()
        else:
            self.scope = scope

    def visit_variable(self, exp):
        # handle special variable for the table size
        if exp.tuple_index == -1 and exp.column_id == -1:
            return self.scope.functions['SIZE'](exp.table_id)

        # handle regular variable for table columns
        assert exp.type in self.scope.sorts, AssertionError(f'What is the column type? {exp.type}')
        if (exp.table_id, exp.column_id) not in self.scope.table_columns:
            self.scope.table_columns[(exp.table_id, exp.column_id)] = Function(f'T{exp.table_id}.{exp.column_id}',
                                                                               self.scope.sorts['int'],
                                                                               self.scope.sorts[exp.type])
        return self.scope.table_columns[(exp.table_id, exp.column_id)](exp.tuple_index)

    def visit_and_expression(self, exp):
        conjunct = []
        for item in exp.args:
            conjunct.append(item.accept(self))
        return And(conjunct)

    def visit_or_expression(self, exp):
        disjunct = []
        for item in exp.args:
            disjunct.append(item.accept(self))
        return Or(disjunct)

    def visit_not_expression(self, exp):
        return Not(exp.args[0].accept(self))

    def visit_implies_expression(self, exp):
        return Implies(exp.args[0].accept(self), exp.args[1].accept(self))

    def visit_equal_expression(self, exp):
        # f = []
        # if isinstance(exp.lexpr, Variable) and isinstance(exp.rexpr, Variable) and not (
        #         exp.lexpr.tuple_index & exp.lexpr.column_id == -1 or exp.rexpr.tuple_index & exp.rexpr.column_id == -1):
        #     f.append(
        #         self.scope.functions['NULL'](exp.lexpr.table_id, exp.lexpr.column_id, exp.lexpr.tuple_index) ==
        #         self.scope.functions['NULL'](exp.rexpr.table_id, exp.rexpr.column_id, exp.rexpr.tuple_index)
        #     )
        # f.append(exp.lexpr.accept(self) == exp.rexpr.accept(self))
        return exp.lexpr.accept(self) == exp.rexpr.accept(self)
        # return self.IfNotNullOrFalse(exp, exp.lexpr.accept(self) == exp.rexpr.accept(self))

    def visit_less_expression(self, exp):
        return exp.lexpr.accept(self) < exp.rexpr.accept(self)

    def visit_greater_expression(self, exp):
        return exp.lexpr.accept(self) > exp.rexpr.accept(self)

    def visit_less_equal_expression(self, exp):
        return exp.lexpr.accept(self) <= exp.rexpr.accept(self)

    def visit_greater_equal_expression(self, exp):
        return exp.lexpr.accept(self) >= exp.rexpr.accept(self)

    def visit_not_equal_expression(self, exp):
        return exp.lexpr.accept(self) != exp.rexpr.accept(self)

    def visit_id_expression(self, exp):
        return exp.args[0].accept(self)

    def visit_is_null_expression(self, exp):
        if not isinstance(exp.lexpr, Variable):
            raise TypeError('IS NULL is used with a non-variable expression')

        return self.scope.functions['NULL'](exp.lexpr.table_id, exp.lexpr.column_id, exp.lexpr.tuple_index)

    def visit_literal(self, exp):
        if type(exp.value) == str and exp.value.count('-') == 2:
            return date2int(exp.value)
        return exp.value

    def visit_true(self, exp):
        return True

    def IfNotNullOrFalse(self, exp, then_exp):
        if (isinstance(exp.lexpr, Variable) and exp.lexpr.tuple_index & exp.lexpr.column_id == -1) or (
                isinstance(exp.rexpr, Variable) and exp.rexpr.tuple_index & exp.rexpr.column_id == -1):
            return then_exp

        f = []
        if isinstance(exp.lexpr, Variable):
            f.append(
                Not(self.scope.functions['NULL'](exp.lexpr.table_id, exp.lexpr.column_id, exp.lexpr.tuple_index)))
        if isinstance(exp.rexpr, Variable):
            f.append(
                Not(self.scope.functions['NULL'](exp.rexpr.table_id, exp.rexpr.column_id, exp.rexpr.tuple_index)))
        f.append(then_exp)
        return And(*f)
