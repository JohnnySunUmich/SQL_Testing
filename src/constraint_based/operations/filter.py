import pglast.ast
from itertools import product

from .operation import Operation
from ..internal_schema import TableSchema
from ..commons import get_table_id, parse_predicate
from ..constraints.logic_expressions import *
from ..constraints.comparison_expressions import *
from ..constraints.literal_expression import *

from copy import deepcopy


class Filter(Operation):
    def __init__(self, input_schema: TableSchema, raw_predicate):
        super(Filter, self).__init__()
        self.input_schema = input_schema
        self.__init_output_schema()
        self.raw_predicate = raw_predicate

    def __eq__(self, other):
        return type(self) == type(other) and self.input_schema == other.input_schema and \
               self.raw_predicate == other.raw_predicate

    def __init_output_schema(self):
        _, input_table_name = self.input_schema.get_info()
        output_table_id = get_table_id()
        self.output_schema = TableSchema(output_table_id, input_table_name, self.input_schema.size_bound)
        self.mapping = {}
        for column in self.input_schema:
            output_column = deepcopy(column)
            c_id, _, _, _, _ = column.get_info()
            self.output_schema.append(output_column)
            self.mapping[c_id] = c_id
        vManager.add_table(self.output_schema)

    def copy_input_schema(self, other):
        self.input_schema = deepcopy(other.input_schema)

    def gen_colRef2var(self, tuple_index):
        def colRef2var(ColumnRef):
            assert isinstance(ColumnRef, pglast.ast.ColumnRef)
            fields = ColumnRef.fields
            if len(fields) == 1:
                column_name = fields[0].val
                table_id, _ = self.input_schema.get_info()
                for column in self.input_schema:
                    c_id, c_name, _, _, _ = column.get_info()
                    if c_name == column_name:
                        return vManager.get_variable(table_id, tuple_index, c_id)
            elif len(fields) == 2:
                column_name = fields[-1].val
                table_name = fields[0].val
                table_id, _ = self.input_schema.get_info()
                for column in self.input_schema:
                    c_id, c_name, _, rt_name, _ = column.get_info()
                    if c_name == column_name and table_name == rt_name:
                        return vManager.get_variable(table_id, tuple_index, c_id)
            raise ValueError(f"not found field {fields}")

        return colRef2var

    def semantic_constraints(self) -> Logic_Expression:
        constraints = TRUE([])

        input_table_id, _ = self.input_schema.get_info()
        input_size_variable = vManager.get_variable(input_table_id, -1, -1)

        output_table_id, _ = self.output_schema.get_info()
        output_size_variable = vManager.get_variable(output_table_id, -1, -1)

        cases = []
        for table_size in range(self.output_schema.size_bound + 1):
            input_size_constraint = Equal_Expression(input_size_variable, Literal(table_size))

            # enumerate all possible assignments of predicates on each tuple
            for assignment in product([0, 1], repeat=table_size):
                assignment = list(assignment)
                args = [input_size_constraint]

                # construct predicate constraints
                for tuple_index, ass in enumerate(assignment):
                    colRef2var = self.gen_colRef2var(tuple_index)
                    arg = parse_predicate(self.raw_predicate, colRef2var)
                    if ass == 1:
                        args.append(arg)
                    else:
                        args.append(NOT_Expression([arg]))
                if len(args) > 1:
                    case = AND_Expression(args)
                else:
                    case = args[0]

                # construct output table size constraints
                output_size_constraint = Equal_Expression(output_size_variable, Literal(sum(assignment)))

                # construct table entry mapping
                args = [output_size_constraint]
                output_tuple_index = 0
                for tuple_index, ass in enumerate(assignment):
                    if ass == 0:
                        continue
                    for column in self.input_schema:
                        c_id, _, _, _, _ = column.get_info()
                        input_entry = vManager.get_variable(input_table_id, tuple_index, c_id)
                        output_entry = vManager.get_variable(output_table_id, output_tuple_index, c_id)
                        arg = Equal_Expression(input_entry, output_entry)
                        args.append(arg)
                        arg = Equal_Expression(Is_Null_Expression(input_entry), Is_Null_Expression(output_entry))
                        args.append(arg)
                    output_tuple_index += 1
                if len(args) > 1:
                    then = AND_Expression(args)
                else:
                    then = args[0]

                # construct case -> then
                case_then = Implies_Expression([case, then])

                # ANDing constraints together
                cases.append(case_then)

        # construct trivial constraints for table size
        lower_bound = Greater_Equal_Expression(input_size_variable, Literal(0))
        upper_bound = Less_Equal_Expression(input_size_variable, Literal(self.output_schema.size_bound))
        constraints = AND_Expression([constraints, lower_bound, upper_bound] + cases)

        return constraints

    def mutated_semantic_constraint(self, mutant):
        raw_predicate = self.raw_predicate
        self.raw_predicate = mutant
        constraints = self.semantic_constraints()
        self.raw_predicate = raw_predicate
        return constraints

    def mutation_constraints(self, mutant, mutation_type: str = "predicate") -> Logic_Expression:
        constraints = TRUE([])

        input_table_id, _ = self.input_schema.get_info()
        input_size_variable = vManager.get_variable(input_table_id, -1, -1)

        cases = []
        for table_size in range(self.output_schema.size_bound + 1):
            input_size_constraint = Equal_Expression(input_size_variable, Literal(table_size))

            args = [NOT_Expression([TRUE([])])]
            for tuple_index in range(table_size):
                colRef2var = self.gen_colRef2var(tuple_index)
                predicate1 = parse_predicate(self.raw_predicate, colRef2var)
                predicate2 = parse_predicate(mutant.raw_predicate, colRef2var)
                arg = OR_Expression([
                    AND_Expression([
                        NOT_Expression([predicate1]), predicate2
                    ]),
                    AND_Expression([
                        predicate1, NOT_Expression([predicate2])
                    ])
                ])
                args.append(arg)
            if len(args) > 1:
                then = OR_Expression(args)
            else:
                then = args[0]

            case_then = Implies_Expression([input_size_constraint, then])

            cases.append(case_then)

        lower_bound = Greater_Equal_Expression(input_size_variable, Literal(0))
        upper_bound = Less_Equal_Expression(input_size_variable, Literal(self.output_schema.size_bound))
        constraints = AND_Expression([constraints, lower_bound, upper_bound] + cases)

        return constraints

    def preserving_constraints(self) -> Logic_Expression:
        constraints = TRUE([])

        input_table_id, _ = self.input_schema.get_info()
        input_size_variable = vManager.get_variable(input_table_id, -1, -1)

        # enumerate all possible table sizes
        cases = []
        for table_size in range(self.output_schema.size_bound + 1):
            # if table size
            case = Equal_Expression(input_size_variable, Literal(table_size))

            # then all sat
            args = [TRUE([])]
            for tuple_index in range(table_size):
                colRef2var = self.gen_colRef2var(tuple_index)
                arg = parse_predicate(self.raw_predicate, colRef2var)
                args.append(arg)
            if len(args) > 0:
                then = AND_Expression(args)
            else:
                then = args[0]

            # construct case-then constraint
            case_then = Implies_Expression([case, then])

            cases.append(case_then)

        constraints = AND_Expression([constraints] + cases)

        return constraints

    def __str__(self):
        return f"{self.output_schema} = Filter({self.input_schema}, <predicate>)\n"
