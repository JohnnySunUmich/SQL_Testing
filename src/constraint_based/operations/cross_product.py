import math
from typing import List
from copy import copy, deepcopy
from itertools import product
from collections import defaultdict

from .operation import Operation
from ..internal_schema import TableSchema
from ..commons import get_table_id
from ..constraints.logic_expressions import *
from ..constraints.comparison_expressions import Equal_Expression, Literal


class CrossProduct(Operation):
    def __init__(self, input_schemas: List[TableSchema], mode: str = "optimistic"):
        super(CrossProduct, self).__init__()
        self.input_schemas = input_schemas
        self.mode = mode
        self.__init_output_schema()

    def __eq__(self, other):
        if type(self) == type(other):
            for idx, input_schema in enumerate(self.input_schemas):
                if input_schema != other.input_schemas[idx]:
                    return False
            return True
        return False

    def __init_output_schema(self):
        input_table_names = []
        for input_schema in self.input_schemas:
            input_table_names.append(input_schema.table_name)
        output_table_name = "_".join(input_table_names)
        output_table_id = get_table_id()
        if self.mode == "optimistic":
            output_size_bound = min([input_schema.size_bound for input_schema in self.input_schemas])
        else:
            output_size_bound = math.prod([input_schema.size_bound for input_schema in self.input_schemas])

        self.output_schema = TableSchema(output_table_id, output_table_name, output_size_bound)
        self.mapping = {}
        column_id = 0
        for input_schema in self.input_schemas:
            table_id, _ = input_schema.get_info()
            for column in input_schema:
                output_column = deepcopy(column)
                output_column.column_id = column_id
                self.output_schema.append(output_column)
                self.mapping[column_id] = [table_id, column.column_id]
                column_id += 1
        vManager.add_table(self.output_schema)

    def __get_size(self):
        combs = (list(range(input_schema.size_bound)) for input_schema in self.input_schemas)
        combs = product(*combs)

        outputs = []
        for comb in combs:
            comb = list(comb)
            if math.prod(comb) <= self.output_schema.size_bound:
                outputs.append(comb)
        return outputs

    def semantic_constraints(self) -> Logic_Expression:
        output_table_id, _ = self.output_schema.get_info()
        output_size_variable = vManager.get_variable(output_table_id, -1, -1)

        input_size_lists = self.__get_size()
        cases = []
        for input_size_list in input_size_lists:
            output_size = math.prod(input_size_list)
            output_size_constraint = Equal_Expression(output_size_variable, Literal(output_size))
            case = [TRUE([])]
            then = [output_size_constraint]
            for idx, input_size in enumerate(input_size_list):
                input_table_id, _ = self.input_schemas[idx].get_info()
                input_size_variable = vManager.get_variable(input_table_id, -1, -1)
                input_size_constraint = Equal_Expression(input_size_variable, Literal(input_size))
                case.append(input_size_constraint)
            for tuple_index in range(output_size):
                input_tuple_index = defaultdict(int)
                output_size_accum = copy(tuple_index)
                for idx, input_size in enumerate(input_size_list):
                    input_table_id, _ = self.input_schemas[idx].get_info()
                    if idx == len(input_size_list) - 1:
                        input_tuple_index[input_table_id] = output_size_accum
                    else:
                        partition = math.prod(input_size_list[idx+1:])
                        input_tuple_index[input_table_id] = output_size_accum // partition
                        output_size_accum = output_size_accum % partition
                # print(tuple_index, input_tuple_index)
                for column in self.output_schema:
                    c_id, _, _, _, _ = column.get_info()
                    output_entry = vManager.get_variable(output_table_id, tuple_index, c_id)
                    input_table_id, input_column_id = self.mapping[c_id]
                    input_entry = vManager.get_variable(input_table_id, input_tuple_index[input_table_id],
                                                        input_column_id)
                    then.append(Equal_Expression(input_entry, output_entry))
                    then.append(Equal_Expression(Is_Null_Expression(input_entry), Is_Null_Expression(output_entry)))
            case = AND_Expression(case)
            then = AND_Expression(then)
            cases.append(Implies_Expression([case, then]))

        # enforce input size constraint
        input_size_constraints = []
        for input_size_list in input_size_lists:
            input_size_case = []
            for idx, input_size in enumerate(input_size_list):
                input_table_id, _ = self.input_schemas[idx].get_info()
                input_size_variable = vManager.get_variable(input_table_id, -1, -1)
                input_size_case.append(Equal_Expression(input_size_variable, Literal(input_size)))
            input_size_constraints.append(AND_Expression(input_size_case))

        input_size_constraints = OR_Expression(input_size_constraints)

        constraints = AND_Expression([input_size_constraints] + cases)
        return constraints

    def preserving_constraints(self):
        return TRUE([])

    def __str__(self):
        inputs = ",".join([str(schema) for schema in self.input_schemas])
        return f"{self.output_schema} = CrossProduct({inputs})\n"
