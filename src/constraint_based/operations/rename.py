from .operation import Operation
from ..internal_schema import TableSchema
from ..commons import get_table_id
from ..constraints.logic_expressions import *
from ..constraints.comparison_expressions import *


class Rename(Operation):

    def __init__(self, input_schema: TableSchema, new_table_name: str):
        super(Rename, self).__init__()
        self.input_schema = input_schema
        self.new_table_name = new_table_name
        self.__init_output_schema(new_table_name)

    def __eq__(self, other):
        return type(self) == type(other) and self.input_schema == other.input_schema and \
               self.new_table_name == other.new_table_name

    def __init_output_schema(self, new_table_name):
        output_table_id = get_table_id()
        self.output_schema = TableSchema(output_table_id, new_table_name, self.input_schema.size_bound)
        self.mapping = {}
        for column in self.input_schema:
            output_column = deepcopy(column)
            output_column.referred_table_name = new_table_name
            c_id, _, _, _, _ = column.get_info()
            self.mapping[c_id] = c_id
            self.output_schema.append(output_column)
        vManager.add_table(self.output_schema)

    def semantic_constraints(self):
        constraints = TRUE([])

        input_table_id, _ = self.input_schema.get_info()
        input_size_variable = vManager.get_variable(input_table_id, -1, -1)

        output_table_id, _ = self.output_schema.get_info()
        output_table_variable = vManager.get_variable(output_table_id, -1, -1)

        cases = []
        for table_size in range(self.output_schema.size_bound + 1):
            input_size_constraint = Equal_Expression(input_size_variable, Literal(table_size))
            output_size_constraint = Equal_Expression(output_table_variable, Literal(table_size))

            args = [output_size_constraint]
            for tuple_index in range(table_size):
                for column in self.output_schema:
                    c_id = column.column_id
                    input_entry = vManager.get_variable(input_table_id, tuple_index, c_id)
                    output_entry = vManager.get_variable(output_table_id, tuple_index, c_id)
                    arg = Equal_Expression(input_entry, output_entry)
                    arg_null = Equal_Expression(Is_Null_Expression(input_entry), Is_Null_Expression(output_entry))
                    args += [arg, arg_null]

            if len(args) > 1:
                then = AND_Expression(args)
            else:
                then = args[0]

            case_then = Implies_Expression([input_size_constraint, then])

            cases.append(case_then)

        lower_bound = Greater_Equal_Expression(input_size_variable, Literal(0))
        upper_bound = Less_Equal_Expression(input_size_variable, Literal(self.output_schema.size_bound))
        constraints = AND_Expression([constraints, lower_bound, upper_bound] + cases)

        return constraints

    def preserving_constraints(self) -> Logic_Expression:
        return TRUE([])

    def __str__(self):
        return f"{self.output_schema} = Rename({self.input_schema}, <newName>)\n"
