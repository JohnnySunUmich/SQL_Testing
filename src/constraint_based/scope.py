from z3 import *


# Z3 scope
class Scope:
    def __init__(self):
        self.sorts = {
            'tuple': DeclareSort('TupleSort'),
            'table': DeclareSort('TableSort'),
            'int': IntSort(),
            'bool': BoolSort(),
            'varchar': StringSort(),
            'date': IntSort(),
            'enum': StringSort(),
            'time': IntSort()
        }

        self.functions = {
            # ========== special uninterpreted functions ==========
            # SIZE(table_id) -> int
            'SIZE': Function('SIZE', self.sorts['int'], self.sorts['int']),
            # NULL(table_id, column_id, row_id) -> Boolean
            'NULL': Function('NULL', self.sorts['int'], self.sorts['int'], self.sorts['int'], self.sorts['bool']),

            # ========== SQL built-in functions ==========
            'abs': lambda x: If(x >= 0, x, -x),
        }

        self.table_columns = {}
