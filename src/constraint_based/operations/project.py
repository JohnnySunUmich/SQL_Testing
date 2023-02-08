import pglast.ast

from .operation import Operation
from ..internal_schema import TableSchema, ColumnSchema
from ..commons import get_table_id
from ..constraints.logic_expressions import *
from ..constraints.comparison_expressions import *
from ..constraints.utils import get_non_null_comp_expr


class Project(Operation):

    def __init__(self, input_schema: TableSchema, target_list: list, distinct_columns: list | None = None):
        super(Project, self).__init__()
        self.input_schema = input_schema
        self.target_list = target_list
        self.distinct_columns = distinct_columns
        self.__init_output_schema(target_list)

    def __eq__(self, other):
        return type(self) == type(other) and self.input_schema == other.input_schema and \
               self.target_list == other.target_list and self.distinct_columns == other.distinct_columns

    def __init_output_schema(self, target_list):
        _, input_table_name = self.input_schema.get_info()
        output_table_id = get_table_id()
        self.output_schema = TableSchema(output_table_id, input_table_name, self.input_schema.size_bound)
        self.mapping = {}
        column_id = 0
        # deal with *
        if len(target_list) == 1 and isinstance(target_list[0], pglast.ast.ResTarget) \
                and isinstance(target_list[0].val, pglast.ast.ColumnRef) and isinstance(target_list[0].val.fields[-1],
                                                                                        pglast.ast.A_Star):
            for column in self.input_schema:
                c_id, c_name, c_type, rt_name, agg = column.get_info()
                self.mapping[column_id] = c_id
                output_column = ColumnSchema(column_id, c_name, c_type, rt_name, agg)
                column_id += 1
                self.output_schema.append(output_column)
            vManager.add_table(self.output_schema)
            return
        for res_target in target_list:
            assert isinstance(res_target, pglast.ast.ResTarget)
            target_val = res_target.val
            target_name = res_target.name
            if isinstance(target_val, pglast.ast.ColumnRef):
                referred_column_name = target_val.fields[-1].val
                referred_table_name = None if len(target_val.fields) < 2 else target_val.fields[0].val
                output_column_type = None
                for column in self.input_schema:
                    c_id, c_name, c_type, rt_name, _ = column.get_info()
                    if (referred_table_name == rt_name or referred_table_name is None) \
                            and referred_column_name == c_name:
                        self.mapping[column_id] = c_id
                        output_column_type = c_type
                        referred_table_name = rt_name
                        break
                # DEBUG:
                if column_id not in self.mapping:
                    print(f"not found column {referred_table_name}.{referred_column_name}")
                    print(self.input_schema)
                    raise Exception
                output_column_name = target_name if target_name else referred_column_name
                output_column = ColumnSchema(column_id, output_column_name, output_column_type, referred_table_name)
                column_id += 1
                self.output_schema.append(output_column)
            elif isinstance(target_val, pglast.ast.FuncCall):
                assert len(target_val.funcname) == 1
                funcname = target_val.funcname[0].val
                assert target_val.agg_star or len(target_val.args) == 1
                arg = target_val.args[0] if target_val.args and len(target_val.args) == 1 else '*'
                if isinstance(arg, pglast.ast.ColumnRef):
                    referred_column_name = arg.fields[-1].val
                    referred_table_name = None if len(arg.fields) < 2 else arg.fields[0].val
                    output_column_type = 'int'
                    for column in self.input_schema:
                        c_id, c_name, c_type, rt_name, _ = column.get_info()
                        if (referred_table_name == rt_name or referred_table_name is None) \
                                and referred_column_name == c_name:
                            referred_table_name = rt_name
                            self.mapping[column_id] = -c_id
                            break
                elif arg == '*':
                    referred_column_name = "*"
                    referred_table_name = None
                    output_column_type = "int"
                    self.mapping[column_id] = -1000  # ad-hoc dealing with star
                else:
                    raise TypeError(f"undefined type {arg}")
                output_column_name = target_name if target_name else referred_column_name
                output_column = ColumnSchema(column_id, output_column_name, output_column_type, referred_table_name,
                                             funcname)
                column_id += 1
                self.output_schema.append(output_column)
            else:
                raise TypeError(f"undefined type {target_val}")
        vManager.add_table(self.output_schema)

    def copy_input_schema(self, other):
        self.input_schema = deepcopy(other.input_schema)


    def semantic_constraints(self) -> Logic_Expression:
        constraints = TRUE([])

        input_table_id, _ = self.input_schema.get_info()
        input_size_variable = vManager.get_variable(input_table_id, -1, -1)

        output_table_id, _ = self.output_schema.get_info()
        output_size_variable = vManager.get_variable(output_table_id, -1, -1)

        cases = []
        for table_size in range(self.output_schema.size_bound + 1):
            input_size_constraint = Equal_Expression(input_size_variable, Literal(table_size))
            output_size_constraint = Equal_Expression(output_size_variable, Literal(table_size))

            args = [output_size_constraint]
            for tuple_index in range(table_size):
                for column in self.output_schema:
                    c_id = column.column_id
                    if self.mapping[c_id] < 0:
                        # the output column is a function call, skip it for now
                        continue
                    input_entry = vManager.get_variable(input_table_id, tuple_index, self.mapping[c_id])
                    output_entry = vManager.get_variable(output_table_id, tuple_index, c_id)
                    arg = Equal_Expression(input_entry, output_entry)
                    arg_null = Equal_Expression(Is_Null_Expression(output_entry), Is_Null_Expression(input_entry))
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

    def mutation_constraints(self, mutant, mutation_type: str = "distinct"):
        if mutation_type == "distinct":
            # there exists two identical rows in the input able
            size_cases = []
            table_id = self.input_schema.table_id
            table_size_variable = vManager.get_variable(table_id, -1, -1)
            for table_size in range(self.input_schema.size_bound+1):
                if table_size < 2:
                    continue
                case = Equal_Expression(table_size_variable, Literal(table_size))
                args = [NOT_Expression([TRUE([])])]
                for tuple_index1 in range(table_size):
                    for tuple_index2 in range(tuple_index1 + 1, table_size):
                        tuple_arg = []
                        for output_column in self.mapping:
                            input_column_id = self.mapping[output_column]
                            if input_column_id < 0:
                                continue
                            var1 = vManager.get_variable(table_id, tuple_index1, input_column_id)
                            var2 = vManager.get_variable(table_id, tuple_index2, input_column_id)
                            tuple_arg.append(get_non_null_comp_expr('=', var1, var2))
                        args.append(AND_Expression(tuple_arg))
                then = OR_Expression(args)
                case_then = Implies_Expression([case, then])
                size_cases.append(case_then)
            size_constriant = Greater_Equal_Expression(table_size_variable, Literal(2))
            constraints = AND_Expression(size_cases + [size_constriant])
            return constraints
        else:
            raise Exception(f"does not support {mutation_type} type in project operation")

    def __str__(self):
        return f"{self.output_schema} = Project({self.input_schema}, <targetList>)\n"
