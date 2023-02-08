from typing import List
import math
from itertools import product

import pglast.ast

from .operation import Operation
from ..internal_schema import TableSchema
from ..commons import get_table_id, parse_predicate
from ..constraints.comparison_expressions import *
from ..constraints.logic_expressions import *

class Join(Operation):
    def __init__(self, input_schemas: List[TableSchema], predicate, mode: str = "optimistic"):
        super(Join, self).__init__()
        self.input_schemas = input_schemas
        self.mode = mode
        self.__init_output_schema()
        self.raw_predicate = predicate

    def __eq__(self, other):
        return type(self) == type(other) and \
               self.input_schemas[0] == other.input_schemas[0] and \
               self.input_schemas[1] == other.input_schemas[1] and \
               self.raw_predicate == other.raw_predicate

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
                column_id+= 1
        vManager.add_table(self.output_schema)

    def copy_input_schema(self, other):
        old_input_schemas = self.input_schemas
        self.input_schemas = deepcopy(other.input_schemas)
        old_new_mapping = {
            old_input_schemas[0].table_id: self.input_schemas[0].table_id,
            old_input_schemas[1].table_id: self.input_schemas[1].table_id,
        }
        for column_id in self.mapping:
            self.mapping[column_id][0] = old_new_mapping[self.mapping[column_id][0]]


    def predicate_mutation_constraints(self, mutant_predicate):
        input_table_id1, _ = self.input_schemas[0].get_info()
        input_table_id2, _ = self.input_schemas[1].get_info()
        output_table_id, _ = self.output_schema.get_info()
        input_size_variable1 = vManager.get_variable(input_table_id1, -1, -1)
        input_size_variable2 = vManager.get_variable(input_table_id2, -1, -1)
        output_size_variable = vManager.get_variable(output_table_id, -1, -1)

        input_size_lists = self.gen_size()
        cases = []
        for input_size_list in input_size_lists:
            output_size = math.prod(input_size_list)
            input_size_constraint1 = Equal_Expression(input_size_variable1, Literal(input_size_list[0])) # 2
            input_size_constraint2 = Equal_Expression(input_size_variable2, Literal(input_size_list[1])) # 1
            case = [input_size_constraint1, input_size_constraint2]
            args = [NOT_Expression([TRUE([])])]
            for tuple_index in range(output_size):
                input_tuple_index = {self.input_schemas[0].table_id: tuple_index // input_size_list[1], # 0, 0
                                     self.input_schemas[1].table_id: tuple_index % input_size_list[1]}  # 0,
                colRef2var = self.gen_colRef2var(input_tuple_index)
                arg = parse_predicate(self.raw_predicate, colRef2var)
                arg_M = parse_predicate(mutant_predicate, colRef2var)
                args.append(OR_Expression([
                    AND_Expression([arg, NOT_Expression([arg_M])]),
                    AND_Expression([NOT_Expression([arg]), arg_M])]))
            then = OR_Expression(args)
            case = AND_Expression(case)
            case_then = Implies_Expression([case, then])
            cases.append(case_then)

        constraints = AND_Expression(cases)
        return constraints

    def join_type_mutation_constraints(self, types: List[str]):
        if "inner" in types and "left" in types:
            return self.__inner_left_mutation_constraints()
        elif "inner" in types and "right" in types:
            return self.__inner_right_mutation_constraints()
        elif "left" in types and "right" in types:
            return self.__left_right_mutation_constraints()
        elif "full" in types and "inner" in types:
            return self.__full_inner_mutation_constraints()
        elif "full" in types and "left" in types:
            return self.__full_left_mutation_constraints()
        elif "full" in types and "right" in types:
            return self.__full_right_mutation_constraints()

    def __inner_left_mutation_constraints(self):
        input_table_id1, _ = self.input_schemas[0].get_info()
        input_table_id2, _ = self.input_schemas[1].get_info()
        output_table_id, _ = self.output_schema.get_info()
        input_size_variable1 = vManager.get_variable(input_table_id1, -1, -1)
        input_size_variable2 = vManager.get_variable(input_table_id2, -1, -1)

        input_size_lists = self.gen_size()
        cases = []
        for input_size_list in input_size_lists:
            input_size_constraint1 = Equal_Expression(input_size_variable1, Literal(input_size_list[0]))
            input_size_constraint2 = Equal_Expression(input_size_variable2, Literal(input_size_list[1]))
            case = [input_size_constraint1, input_size_constraint2]
            then = [NOT_Expression([TRUE([])])]
            for table1_index in range(input_size_list[0]):
                args = []
                for table2_index in range(input_size_list[1]):
                    input_tuple_index = {
                        self.input_schemas[0].table_id: table1_index,
                        self.input_schemas[1].table_id: table2_index
                    }
                    colRef2var = self.gen_colRef2var(input_tuple_index)
                    arg = NOT_Expression([parse_predicate(self.raw_predicate, colRef2var)])
                    args.append(arg)
                then.append(AND_Expression(args))
            then = OR_Expression(then)
            case = AND_Expression(case)
            case_then = Implies_Expression([case, then])
            cases.append(case_then)
        constraints = AND_Expression(cases)
        return constraints

    def __inner_right_mutation_constraints(self):
        input_table_id1, _ = self.input_schemas[0].get_info()
        input_table_id2, _ = self.input_schemas[1].get_info()
        output_table_id, _ = self.output_schema.get_info()
        input_size_variable1 = vManager.get_variable(input_table_id1, -1, -1)
        input_size_variable2 = vManager.get_variable(input_table_id2, -1, -1)

        input_size_lists = self.gen_size()
        cases = []
        for input_size_list in input_size_lists:
            input_size_constraint1 = Equal_Expression(input_size_variable1, Literal(input_size_list[0]))
            input_size_constraint2 = Equal_Expression(input_size_variable2, Literal(input_size_list[1]))
            case = [input_size_constraint1, input_size_constraint2]
            then = []
            for table2_index in range(input_size_list[1]):
                args = []
                for table1_index in range(input_size_list[0]):
                    input_tuple_index = {
                        self.input_schemas[0].table_id: table1_index,
                        self.input_schemas[1].table_id: table2_index
                    }
                    colRef2var = self.gen_colRef2var(input_tuple_index)
                    arg = NOT_Expression([parse_predicate(self.raw_predicate, colRef2var)])
                    args.append(arg)
                then.append(AND_Expression(args))
            then = OR_Expression(then)
            case = AND_Expression(case)
            case_then = Implies_Expression([case, then])
            cases.append(case_then)
        constraints = AND_Expression(cases)
        return constraints

    def __left_right_mutation_constraints(self):
        left_inner_constraints = self.__inner_left_mutation_constraints()
        right_inner_constraints = self.__inner_right_mutation_constraints()
        constraints = OR_Expression([left_inner_constraints, right_inner_constraints])
        return constraints

    def __full_inner_mutation_constraints(self):
        return self.__left_right_mutation_constraints()

    def __full_left_mutation_constraints(self):
        return self.__inner_right_mutation_constraints()

    def __full_right_mutation_constraints(self):
        return self.__inner_left_mutation_constraints()

    def gen_colRef2var(self, tuple_index: dict):
        # tuple_index in the index in the output table
        def colRef2var(ColumnRef: pglast.ast.ColumnRef):
            fields = ColumnRef.fields
            if len(fields) == 1:
                column_name = fields[-1].val
                for input_schema in self.input_schemas:
                    table_id, _ = input_schema.get_info()
                    for column in input_schema:
                        c_id, c_name, _, _, _ = column.get_info()
                        if c_name == column_name:
                            return vManager.get_variable(table_id, tuple_index[table_id], c_id)
            elif len(fields) == 2:
                column_name =  fields[-1].val
                table_name = fields[0].val
                for input_schema in self.input_schemas:
                    table_id, _ = input_schema.get_info()
                    for column in input_schema:
                        c_id, c_name, _, rt_name, _ = column.get_info()
                        if c_name == column_name and table_name == rt_name:
                            return vManager.get_variable(table_id, tuple_index[table_id], c_id)
            raise ValueError(f"not found field {fields}")
        return colRef2var

    def gen_size(self):
        combs = (list(range(input_schema.size_bound+1)) for input_schema in self.input_schemas)
        combs = product(*combs)

        outputs = []
        for comb in combs:
            comb = list(comb)
            if math.prod(comb) <= self.output_schema.size_bound:
                outputs.append(comb)
        return outputs


class InnerJoin(Join):
    def semantic_constraints(self, mode: str="optimistic"):
        constraints = TRUE([])

        input_table_id1, _ = self.input_schemas[0].get_info()
        input_table_id2, _ = self.input_schemas[1].get_info()
        output_table_id, _ = self.output_schema.get_info()

        input_size_variable1 = vManager.get_variable(input_table_id1, -1, -1)
        input_size_variable2 = vManager.get_variable(input_table_id2, -1, -1)
        output_size_variable = vManager.get_variable(output_table_id, -1, -1)

        input_size_lists = self.gen_size()
        cases = []
        for input_size_list in input_size_lists:
            output_size = math.prod(input_size_list)
            input_size_constraint1 = Equal_Expression(input_size_variable1, Literal(input_size_list[0]))
            input_size_constraint2 = Equal_Expression(input_size_variable2, Literal(input_size_list[1]))
            for assignment in product([0,1], repeat=output_size):
                assignment = list(assignment)
                args = [input_size_constraint1, input_size_constraint2]
                # construct predicate assignment constraints
                for tuple_index, ass in enumerate(assignment):
                    input_table_index = {input_table_id1: tuple_index // input_size_list[1],
                                         input_table_id2: tuple_index % input_size_list[1]}
                    colRef2var = self.gen_colRef2var(input_table_index)
                    arg = parse_predicate(self.raw_predicate, colRef2var)
                    if ass == 1:
                        args.append(arg)
                    else:
                        args.append(NOT_Expression([arg]))
                case = AND_Expression(args)

                # construct table mapping constraints
                output_size_constraint = Equal_Expression(output_size_variable, Literal(sum(assignment)))
                args = [output_size_constraint]
                output_tuple_index = 0
                for tuple_index, ass in enumerate(assignment):
                    if ass == 0:
                        continue
                    input_table_index = {input_table_id1: tuple_index // input_size_list[1],
                                         input_table_id2: tuple_index % input_size_list[1]}
                    for column in self.output_schema:
                        c_id, _, _, _, _ = column.get_info()
                        output_entry = vManager.get_variable(output_table_id, output_tuple_index, c_id)
                        input_table_id, input_column_id = self.mapping[c_id]
                        input_entry = vManager.get_variable(input_table_id, input_table_index[input_table_id],
                                                            input_column_id)
                        arg = Equal_Expression(input_entry, output_entry)
                        arg_null = Equal_Expression(Is_Null_Expression(input_entry), Is_Null_Expression(output_entry))
                        args += [arg_null, arg]
                    output_tuple_index += 1
                then = AND_Expression(args)

                case_then = Implies_Expression([case, then])

                cases.append(case_then)

        lower_bound1 = Greater_Equal_Expression(input_size_variable1, Literal(0))
        lower_bound2 = Greater_Equal_Expression(input_size_variable2, Literal(0))
        upper_bound1 = Less_Equal_Expression(input_size_variable1, Literal(self.input_schemas[0].size_bound))
        upper_bound2 = Less_Equal_Expression(input_size_variable2, Literal(self.input_schemas[1].size_bound))

        constraints = AND_Expression([constraints, lower_bound1, lower_bound2, upper_bound1, upper_bound2] + cases)

        return constraints

    def preserving_constraints(self):
        return TRUE([])

    def mutation_constraints(self, mutant, mutation_type: str = "predicate"):
        if isinstance(mutant, InnerJoin):
            join_type = "inner"
        elif isinstance(mutant, LeftJoin):
            join_type = "left"
        elif isinstance(mutant, RightJoin):
            join_type = "right"
        elif isinstance(mutant, FullJoin):
            join_type = "full"
        else:
            raise TypeError(f"unsupported join type {mutant}")
        if mutation_type == "predicate":
            return self.predicate_mutation_constraints(mutant.raw_predicate)
        elif mutation_type == "join_type":
            if join_type == "left":
                return self.join_type_mutation_constraints(["inner", "left"])
            elif join_type == "full":
                return self.join_type_mutation_constraints(["inner", "full"])
            elif join_type == "right":
                return self.join_type_mutation_constraints(["inner", "right"])
        else:
            raise TypeError(f"mutation type {mutation_type} is not supported")


    def __str__(self):
        inputs = ",".join([str(schema) for schema in self.input_schemas])
        return f"{self.output_schema} = InnerJoin({inputs})\n"

class LeftJoin(Join):
    def semantic_constraints(self):
        # left table: self.input_schemas[0]
        # right table: self.input_schemas[1]
        input_table_id1, _ = self.input_schemas[0].get_info()
        input_table_id2, _ = self.input_schemas[1].get_info()
        output_table_id, _ = self.output_schema.get_info()
        input_size_variable1 = vManager.get_variable(input_table_id1, -1, -1)
        input_size_variable2 = vManager.get_variable(input_table_id2, -1, -1)
        output_size_variable = vManager.get_variable(output_table_id, -1, -1)

        input_size_lists = self.gen_size()
        cases = []
        for input_size_list in input_size_lists:
            output_size = math.prod(input_size_list)
            input_size_constraint1 = Equal_Expression(input_size_variable1, Literal(input_size_list[0]))
            input_size_constraint2 = Equal_Expression(input_size_variable2, Literal(input_size_list[1]))
            for assignment in product([0,1], repeat=output_size):
                assignment = list(assignment)
                args = [input_size_constraint1, input_size_constraint2]
                # construct predicate assignment constraints
                for tuple_index, ass in enumerate(assignment):
                    input_table_index = {input_table_id1: tuple_index // input_size_list[1],
                                         input_table_id2: tuple_index % input_size_list[1]}
                    colRef2var = self.gen_colRef2var(input_table_index)
                    arg = parse_predicate(self.raw_predicate, colRef2var)
                    if ass == 1:
                        args.append(arg)
                    else:
                        args.append(NOT_Expression([arg]))
                case = AND_Expression(args)

                # construct table mapping constraints
                output_tuple_index = 0
                appeared_index = set()
                args = []
                for table1_index in range(input_size_list[0]):
                    for table2_index in range(input_size_list[1]):
                        if assignment[table1_index * input_size_list[1] + table2_index] == 1:
                            total_tuple_index = table1_index * input_size_list[1] + table2_index
                            input_table_index = {input_table_id1: total_tuple_index // input_size_list[1],
                                                 input_table_id2: total_tuple_index % input_size_list[1]}
                            for column in self.output_schema:
                                c_id, _, _, _, _ = column.get_info()
                                output_entry = vManager.get_variable(output_table_id, output_tuple_index, c_id)
                                input_table_id, input_column_id = self.mapping[c_id]
                                input_entry = vManager.get_variable(input_table_id, input_table_index[input_table_id],
                                                                    input_column_id)
                                arg = Equal_Expression(input_entry, output_entry)
                                arg_null = Equal_Expression(Is_Null_Expression(input_entry), Is_Null_Expression(output_entry))
                                args += [arg, arg_null]
                            output_tuple_index += 1
                            appeared_index.add(table1_index)
                        else:
                            continue
                for table1_index in range(input_size_list[0]):
                    if table1_index not in appeared_index:
                        for column in self.output_schema:
                            c_id, _, _, _, _ = column.get_info()
                            output_entry = vManager.get_variable(output_table_id, output_tuple_index, c_id)
                            input_table_id, input_column_id = self.mapping[c_id]
                            if input_table_id == self.input_schemas[0].table_id:
                                input_entry = vManager.get_variable(input_table_id, table1_index, input_column_id)
                                arg = Equal_Expression(input_entry, output_entry)
                                arg_null = Equal_Expression(Is_Null_Expression(input_entry), Is_Null_Expression(output_entry))
                                args += [arg, arg_null]
                            else:
                                arg = Is_Null_Expression(output_entry)
                                args.append(arg)
                        output_tuple_index += 1
                args.append(Equal_Expression(output_size_variable, Literal(output_tuple_index)))
                then = AND_Expression(args)
                case_then = Implies_Expression([case, then])

                cases.append(case_then)

        lower_bound1 = Greater_Equal_Expression(input_size_variable1, Literal(0))
        lower_bound2 = Greater_Equal_Expression(input_size_variable2, Literal(0))
        upper_bound1 = Less_Equal_Expression(input_size_variable1, Literal(self.input_schemas[0].size_bound))
        upper_bound2 = Less_Equal_Expression(input_size_variable2, Literal(self.input_schemas[1].size_bound))

        constraints = AND_Expression([lower_bound1, lower_bound2, upper_bound1, upper_bound2] + cases)

        return constraints


    def preserving_constraints(self):
        return TRUE([])

    def mutation_constraints(self, mutant, mutation_type: str = "predicate"):
        if isinstance(mutant, InnerJoin):
            join_type = "inner"
        elif isinstance(mutant, LeftJoin):
            join_type = "left"
        elif isinstance(mutant, RightJoin):
            join_type = "right"
        elif isinstance(mutant, FullJoin):
            join_type = "full"
        else:
            raise TypeError(f"unsupported join type {mutant}")
        if mutation_type == "predicate":
            return self.predicate_mutation_constraints(mutant.raw_predicate)
        elif mutation_type == "join_type":
            if join_type == "inner":
                return self.join_type_mutation_constraints(["inner", "left"])
            elif join_type == "full":
                return self.join_type_mutation_constraints(["full", "left"])
            elif join_type == "right":
                return self.join_type_mutation_constraints(["left", "right"])
        else:
            raise TypeError(f"mutation type {join_type} is not supported")

    def __str__(self):
        inputs = ",".join([str(schema) for schema in self.input_schemas])
        return f"{self.output_schema} = LeftJoin({inputs})\n"


class RightJoin(Join):
    def semantic_constraints(self):
        # left table: self.input_schemas[0]
        # right table: self.input_schemas[1]
        input_table_id1, _ = self.input_schemas[0].get_info()
        input_table_id2, _ = self.input_schemas[1].get_info()
        output_table_id, _ = self.output_schema.get_info()
        input_size_variable1 = vManager.get_variable(input_table_id1, -1, -1)
        input_size_variable2 = vManager.get_variable(input_table_id2, -1, -1)
        output_size_variable = vManager.get_variable(output_table_id, -1, -1)

        input_size_lists = self.gen_size()
        cases = []
        for input_size_list in input_size_lists:
            output_size = math.prod(input_size_list)
            input_size_constraint1 = Equal_Expression(input_size_variable1, Literal(input_size_list[0]))
            input_size_constraint2 = Equal_Expression(input_size_variable2, Literal(input_size_list[1]))
            for assignment in product([0, 1], repeat=output_size):
                assignment = list(assignment)
                args = [input_size_constraint1, input_size_constraint2]
                # construct predicate assignment constraints
                for tuple_index, ass in enumerate(assignment):
                    input_table_index = {input_table_id1: tuple_index // input_size_list[1],
                                         input_table_id2: tuple_index % input_size_list[1]}
                    colRef2var = self.gen_colRef2var(input_table_index)
                    arg = parse_predicate(self.raw_predicate, colRef2var)
                    if ass == 1:
                        args.append(arg)
                    else:
                        args.append(NOT_Expression([arg]))
                case = AND_Expression(args)
                args = []
                # construct table mapping constraints
                output_tuple_index = 0
                appeared_index = set()
                for table1_index in range(input_size_list[0]):
                    for table2_index in range(input_size_list[1]):
                        if assignment[table1_index * input_size_list[1] + table2_index] == 1:
                            total_tuple_index = table1_index * input_size_list[1] + table2_index
                            input_table_index = {input_table_id1: total_tuple_index // input_size_list[1],
                                                 input_table_id2: total_tuple_index % input_size_list[1]}
                            for column in self.output_schema:
                                c_id, _, _, _, _ = column.get_info()
                                output_entry = vManager.get_variable(output_table_id, output_tuple_index, c_id)
                                input_table_id, input_column_id = self.mapping[c_id]
                                input_entry = vManager.get_variable(input_table_id, input_table_index[input_table_id],
                                                                    input_column_id)
                                arg = Equal_Expression(input_entry, output_entry)
                                arg_null = Equal_Expression(Is_Null_Expression(input_entry), Is_Null_Expression(output_entry))
                                args += [arg, arg_null]
                            output_tuple_index += 1
                            appeared_index.add(table2_index)
                        else:
                            continue
                for table2_index in range(input_size_list[1]):
                    if table2_index not in appeared_index:
                        for column in self.output_schema:
                            c_id, _, _, _, _ = column.get_info()
                            output_entry = vManager.get_variable(output_table_id, output_tuple_index, c_id)
                            input_table_id, input_column_id = self.mapping[c_id]
                            if input_table_id == self.input_schemas[1].table_id:
                                input_entry = vManager.get_variable(input_table_id, table2_index, input_column_id)
                                arg = Equal_Expression(input_entry, output_entry)
                                arg_null = Equal_Expression(Is_Null_Expression(input_entry), Is_Null_Expression(output_entry))
                                args += [arg_null, arg]
                            else:
                                arg = Is_Null_Expression(output_entry)
                                args.append(arg)
                        output_tuple_index += 1
                args.append(Equal_Expression(output_size_variable, Literal(output_tuple_index)))
                then = AND_Expression(args)
                case_then = Implies_Expression([case, then])

                cases.append(case_then)

        lower_bound1 = Greater_Equal_Expression(input_size_variable1, Literal(0))
        lower_bound2 = Greater_Equal_Expression(input_size_variable2, Literal(0))
        upper_bound1 = Less_Equal_Expression(input_size_variable1, Literal(self.input_schemas[0].size_bound))
        upper_bound2 = Less_Equal_Expression(input_size_variable2, Literal(self.input_schemas[1].size_bound))

        constraints = AND_Expression([lower_bound1, lower_bound2, upper_bound1, upper_bound2] + cases)

        return constraints

    def preserving_constraints(self):
        return TRUE([])

    def mutation_constraints(self, mutant, mutation_type: str = "predicate"):
        if isinstance(mutant, InnerJoin):
            join_type = "inner"
        elif isinstance(mutant, LeftJoin):
            join_type = "left"
        elif isinstance(mutant, RightJoin):
            join_type = "right"
        elif isinstance(mutant, FullJoin):
            join_type = "full"
        else:
            raise TypeError(f"unsupported join type {mutant}")
        if mutation_type == "predicate":
            return self.predicate_mutation_constraints(mutant.raw_predicate)
        elif mutation_type == "jointype":
            if join_type == "inner":
                return self.join_type_mutation_constraints(["inner", "right"])
            elif join_type == "full":
                return self.join_type_mutation_constraints(["right", "full"])
            elif join_type == "left":
                return self.join_type_mutation_constraints(["left", "right"])
        else:
            raise TypeError(f"join type {join_type} is not supported")

    def __str__(self):
        inputs = ",".join([str(schema) for schema in self.input_schemas])
        return f"{self.output_schema} = RightJoin({inputs})\n"

class FullJoin(Join):
    def semantic_constraints(self):
        # left table: self.input_schemas[0]
        # right table: self.input_schemas[1]
        input_table_id1, _ = self.input_schemas[0].get_info()
        input_table_id2, _ = self.input_schemas[1].get_info()
        output_table_id, _ = self.output_schema.get_info()
        input_size_variable1 = vManager.get_variable(input_table_id1, -1, -1)
        input_size_variable2 = vManager.get_variable(input_table_id2, -1, -1)
        output_size_variable = vManager.get_variable(output_table_id, -1, -1)

        input_size_lists = self.gen_size()
        cases = []
        for input_size_list in input_size_lists:
            output_size = math.prod(input_size_list)
            input_size_constraint1 = Equal_Expression(input_size_variable1, Literal(input_size_list[0]))
            input_size_constraint2 = Equal_Expression(input_size_variable2, Literal(input_size_list[1]))
            for assignment in product([0, 1], repeat=output_size):
                assignment = list(assignment)
                args = [input_size_constraint1, input_size_constraint2]
                # construct predicate assignment constraints
                for tuple_index, ass in enumerate(assignment):
                    input_table_index = {input_table_id1: tuple_index // input_size_list[1],
                                         input_table_id2: tuple_index % input_size_list[1]}
                    colRef2var = self.gen_colRef2var(input_table_index)
                    arg = parse_predicate(self.raw_predicate, colRef2var)
                    if ass == 1:
                        args.append(arg)
                    else:
                        args.append(NOT_Expression([arg]))
                case = AND_Expression(args)
                args = []
                # construct table mapping constraints
                output_tuple_index = 0
                appeared_index1 = set()
                appeared_index2 = set()
                for table1_index in range(input_size_list[0]):
                    for table2_index in range(input_size_list[1]):
                        if assignment[table1_index * input_size_list[1] + table2_index] == 1:
                            total_tuple_index = table1_index * input_size_list[1] + table2_index
                            input_table_index = {input_table_id1: total_tuple_index // input_size_list[1],
                                                 input_table_id2: total_tuple_index % input_size_list[1]}
                            for column in self.output_schema:
                                c_id, _, _, _, _ = column.get_info()
                                output_entry = vManager.get_variable(output_table_id, output_tuple_index, c_id)
                                input_table_id, input_column_id = self.mapping[c_id]
                                input_entry = vManager.get_variable(input_table_id, input_table_index[input_table_id],
                                                                    input_column_id)
                                arg = Equal_Expression(input_entry, output_entry)
                                args.append(arg)
                            output_tuple_index += 1
                            appeared_index1.add(table1_index)
                            appeared_index2.add(table2_index)
                        else:
                            continue
                for table1_index in range(input_size_list[0]):
                    if table1_index not in appeared_index1:
                        for column in self.output_schema:
                            c_id, _, _, _, _ = column.get_info()
                            output_entry = vManager.get_variable(output_table_id, output_tuple_index, c_id)
                            input_table_id, input_column_id = self.mapping[c_id]
                            if input_table_id == self.input_schemas[0].table_id:
                                input_entry = vManager.get_variable(input_table_id, table1_index, input_column_id)
                                arg = Equal_Expression(input_entry, output_entry)
                                arg_null = Equal_Expression(Is_Null_Expression(input_entry), Is_Null_Expression(output_entry))
                                args += [arg, arg_null]
                            else:
                                arg = Is_Null_Expression(output_entry)
                                args.append(arg)
                        output_tuple_index += 1
                for table2_index in range(input_size_list[1]):
                    if table2_index not in appeared_index2:
                        for column in self.output_schema:
                            c_id, _, _, _, _ = column.get_info()
                            output_entry = vManager.get_variable(output_table_id, output_tuple_index, c_id)
                            input_table_id, input_column_id = self.mapping[c_id]
                            if input_table_id == self.input_schemas[1].table_id:
                                input_entry = vManager.get_variable(input_table_id, table2_index, input_column_id)
                                arg = Equal_Expression(input_entry, output_entry)
                                arg_null = Equal_Expression(Is_Null_Expression(input_entry), Is_Null_Expression(output_entry))
                                args += [arg, arg_null]
                            else:
                                arg = Is_Null_Expression(output_entry)
                                args.append(arg)
                        output_tuple_index += 1

                args.append(Equal_Expression(output_size_variable, Literal(output_tuple_index)))
                then = AND_Expression(args)
                case_then = Implies_Expression([case, then])

                cases.append(case_then)

        lower_bound1 = Greater_Equal_Expression(input_size_variable1, Literal(0))
        lower_bound2 = Greater_Equal_Expression(input_size_variable2, Literal(0))
        upper_bound1 = Less_Equal_Expression(input_size_variable1, Literal(self.input_schemas[0].size_bound))
        upper_bound2 = Less_Equal_Expression(input_size_variable2, Literal(self.input_schemas[1].size_bound))

        constraints = AND_Expression([lower_bound1, lower_bound2, upper_bound1, upper_bound2] + cases)

        return constraints

    def preserving_constraints(self):
        return TRUE([])

    def mutation_constraints(self, mutant, mutation_type: str = "predicate"):
        if isinstance(mutant, InnerJoin):
            join_type = "inner"
        elif isinstance(mutant, LeftJoin):
            join_type = "left"
        elif isinstance(mutant, RightJoin):
            join_type = "right"
        elif isinstance(mutant, FullJoin):
            join_type = "full"
        else:
            raise TypeError(f"unsupported join type {mutant}")
        if mutation_type == "predicate":
            return self.predicate_mutation_constraints(mutant.raw_predicate)
        elif mutation_type == "jointype":
            if join_type == "left":
                return self.join_type_mutation_constraints(["full", "left"])
            elif join_type == "inner":
                return self.join_type_mutation_constraints(["inner", "full"])
            elif join_type == "right":
                return self.join_type_mutation_constraints(["full", "right"])
        else:
            raise TypeError(f"mutation type {mutation_type} is not supported")

    def __str__(self):
        inputs = ",".join([str(schema) for schema in self.input_schemas])
        return f"{self.output_schema} = FullJoin({inputs})\n"
