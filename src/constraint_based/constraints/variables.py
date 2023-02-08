from collections import defaultdict
from copy import deepcopy

from ..internal_schema import TableSchema

class Variable:
    def __init__(self, table_id, tuple_index, column_id, column_type, column_name):
        self.table_id = table_id
        self.tuple_index = tuple_index
        self.column_id = column_id
        self.identity = [table_id, tuple_index, column_id]
        self.type = column_type
        self.exists = True
        self.column_name = column_name

    def __eq__(self, other):
        return self.identity == other.identity

    def __str__(self):
        T_id, t_id, c_id = self.identity
        if t_id == -1 and c_id == -1:
            return f'SIZE({T_id})'
        return f"T{T_id}[{t_id}].{c_id}"

    def __repr__(self):
        T_id, t_id, c_id = self.identity
        return f"T{T_id}[{t_id}].{c_id}"

    def accept(self, visitor):
        method_name = f'visit_{self.__class__.__name__.lower()}'
        visit = getattr(visitor, method_name)
        return visit(self)


class VariableManager:
    def __init__(self):
        self.variables = defaultdict(list)
        self.sizes = {}

    def add_table(self, schema: TableSchema):
        table_id, _ = schema.get_info()
        self.sizes[table_id] = Variable(table_id, -1, -1, 'int', 'size')
        for tuple_index in range(schema.size_bound):
            columns = [None for _ in range(len(schema))]
            for column in schema:
                c_id, c_name, c_type, _, _ = column.get_info()
                columns[c_id] = Variable(table_id, tuple_index, c_id, c_type, c_name)
            self.variables[table_id].append(columns)

    def get_variable(self, table_id, tuple_index, column_id) -> Variable:
        if tuple_index == -1 and column_id == -1:
            return self.sizes[table_id]
        return self.variables[table_id][tuple_index][column_id]

    def reset(self):
        self.variables = defaultdict(list)
        self.sizes = {}


global vManager
vManager = VariableManager()
