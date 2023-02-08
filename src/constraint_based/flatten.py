import pglast.ast
from collections import defaultdict
from .operations.filter import Filter
from .operations.project import Project
from .operations.rename import Rename
from .operations.cross_product import CrossProduct
from .operations.join import *
from .internal_schema import TableSchema, ColumnSchema
from .commons import get_table_id
from .operations.operation import Operation
from .constraints.logic_expressions import *
from .constraints.comparison_expressions import *


class Flatten:
    def __init__(self, schema, initial_size_bound: int, mode: str = "optimistic"):
        self.schema = schema
        self.raw_integrity_constraint = defaultdict(list)
        self.operations = []
        self.intermediate_table_schemas = []
        self.initial_size_bound = initial_size_bound
        self.mode = mode

    def __parse_schema(self):
        schema = self.schema['Tables']
        self.init_schemas = {}
        track_enum = []
        for idx, tab_schema in enumerate(schema):
            table_id = get_table_id()
            table_name = tab_schema["TableName"].lower()
            table_schema = TableSchema(table_id, table_name, self.initial_size_bound)
            column_id = 0
            for col in tab_schema['PKeys']:
                column_name = col['Name'].lower()
                data_type = col['Type'].split(',')[0]
                if data_type == 'enum':
                    data_type = 'varchar'
                    self.raw_integrity_constraint[f"{table_id}.{column_id}"].append(col['Type'])
                column_schema = ColumnSchema(column_id, column_name, data_type, referred_table_name=table_name)
                column_id += 1
                table_schema.append(column_schema)
            for col in tab_schema['FKeys']:
                column_name = col['FName'].lower()
                p_table = int(col["PTable"])
                p_name = col["PName"]
                p_cols = schema[p_table]["PKeys"]
                data_type = None
                for p_col in p_cols:
                    if p_col["Name"] == p_name:
                        data_type = p_col["Type"].split(',')[0]
                        break
                if data_type == 'enum':
                    data_type = 'varchar'
                    self.raw_integrity_constraint[f"{table_id}.{column_id}"].append(col['Type'])
                column_schema = ColumnSchema(column_id, column_name, data_type, referred_table_name=table_name)
                column_id += 1
                table_schema.append(column_schema)
            for col in tab_schema['Others']:
                column_name = col['Name'].lower()
                data_type = col['Type'].split(',')[0]
                if data_type == 'enum':
                    data_type = 'varchar'
                    self.raw_integrity_constraint[f"{table_id}.{column_id}"].append(col['Type'])
                column_schema = ColumnSchema(column_id, column_name, data_type, referred_table_name=table_name)
                column_id += 1
                table_schema.append(column_schema)
            self.init_schemas[table_name] = table_schema
            vManager.add_table(table_schema)


    def __add_operation(self, operation: Operation):
        self.operations.append(operation)

    def flatten_where(self, where_clause, input_schema):
        # operation = Filter(len(self.operations), self.last_state, where_clause)
        operation = Filter(input_schema, where_clause)
        self.operations.append(operation)
        return operation.output_schema

    def flatten_join(self, join_expr):
        assert isinstance(join_expr, pglast.ast.JoinExpr)
        # deal with left table
        input_schemas = [None, None]
        if isinstance(join_expr.larg, pglast.ast.RangeVar):
            table_name = join_expr.larg.relname
            input_schemas[0] = self.init_schemas[table_name]
            table_alias = join_expr.larg.alias.aliasname if join_expr.larg.alias else None
            if table_alias:
                rename = Rename(input_schemas[0], table_alias)
                self.__add_operation(rename)
                input_schemas[0] = rename.output_schema
        else:
            raise NotImplementedError(
                f"expression type {join_expr.larg} is not implemented for the left table of join")
        if isinstance(join_expr.rarg, pglast.ast.RangeVar):
            table_name = join_expr.rarg.relname
            input_schemas[1] = self.init_schemas[table_name]
            table_alias = join_expr.rarg.alias.aliasname if join_expr.rarg.alias else None
            if table_alias:
                rename = Rename(input_schemas[1], table_alias)
                self.__add_operation(rename)
                input_schemas[1] = rename.output_schema
        else:
            raise NotImplementedError(
                f"expression type {join_expr.rarg} is not implemented for the right table of join")

        join_type = join_expr.jointype
        if join_type == 0:
            join = InnerJoin(input_schemas, join_expr.quals, mode=self.mode)
        elif join_type == 1:
            join = LeftJoin(input_schemas, join_expr.quals, mode=self.mode)
        elif join_type == 2:
            join = FullJoin(input_schemas, join_expr.quals, mode=self.mode)
        elif join_type == 3:
            join = RightJoin(input_schemas, join_expr.quals, mode=self.mode)
        else:
            raise NotImplementedError(f"join type {join_type} is not supported")
        self.__add_operation(join)
        return join.output_schema

    def flatten_from(self, from_clause):
        input_schemas = []
        for table_clause in from_clause:
            if isinstance(table_clause, pglast.ast.RangeVar):
                table_name = table_clause.relname
                input_schema = self.init_schemas[table_name]
                table_alias = table_clause.alias.aliasname if table_clause.alias else None
                if table_alias:
                    rename = Rename(input_schema, table_alias)
                    self.__add_operation(rename)
                    input_schemas.append(rename.output_schema)
                else:
                    input_schemas.append(input_schema)
            elif isinstance(table_clause, pglast.ast.RangeSubselect):
                output_schema = self.flatten_select(from_clause.subquery)
                table_alias = table_clause.alias.aliasname if table_clause.alias else None
                assert table_alias # subquery must be renamed
                rename = Rename(output_schema, table_alias)
                self.__add_operation(rename)
                input_schemas.append(rename.output_schema)
            elif isinstance(table_clause, pglast.ast.JoinExpr):
                output_schema = self.flatten_join(table_clause)
                input_schemas.append(output_schema)
            else:
                raise NotImplementedError(
                    f"expression type {from_clause} in FROM clause is not implementedz A")
        # deal with cross product
        if len(input_schemas) > 1:
            cross_product = CrossProduct(input_schemas, mode=self.mode)
            self.__add_operation(cross_product)
            return cross_product.output_schema
        else:
            return input_schemas[0]

    def flatten_groupby_having_select(self,
                                      distinct_clause,
                                      group_clause,
                                      having_clause,
                                      target_list,
                                      input_schema):
        # ignore group and having for now
        # parse select
        if distinct_clause is not None:
            if len(distinct_clause) == 1 and distinct_clause[0] is None:
                project = Project(input_schema, target_list, distinct_columns=[])
            else:
                project = Project(input_schema, target_list, distinct_columns=list(distinct_clause))
        else:
            project = Project(input_schema, target_list)
        self.__add_operation(project)
        return project.output_schema

    def flatten_select(self, select_stmt):
        # current only support select-from-where-groupby
        # from -> where -> groupby -> having -> select
        assert isinstance(select_stmt, pglast.ast.SelectStmt)
        distinct_clause = select_stmt.distinctClause
        target_list = select_stmt.targetList
        from_clause = select_stmt.fromClause
        where_clause = select_stmt.whereClause
        group_clause = select_stmt.groupClause
        having_clause = select_stmt.havingClause

        table_schema = None
        if from_clause is not None:
            table_schema = self.flatten_from(from_clause)

            if where_clause:
                table_schema = self.flatten_where(where_clause, table_schema)

        table_schema = self.flatten_groupby_having_select(distinct_clause, group_clause, having_clause, target_list, table_schema)
        return table_schema


    def flatten(self, query):
        """
        current support:
        select target_list from_clause where_clause
        """
        self.__parse_schema()
        self.operations = []
        ast = pglast.parser.parse_sql(query)
        select_stmt = ast[0].stmt
        self.flatten_select(select_stmt)


    def __enum_constraints(self, variable: Variable, enum_types: str):
        data_types = enum_types.split(',')[1:]
        args = []
        for data_type in data_types:
            arg = Equal_Expression(variable, Literal(data_type))
            args.append(arg)
        return OR_Expression(args)

    def integrity_constraints(self, size_bound):
        constraints = [TRUE([])]
        for tab_col in self.raw_integrity_constraint:
            i_constraint = self.raw_integrity_constraint[tab_col][0]
            table_id, column_id = tab_col.split('.')
            table_id = int(table_id)
            column_id = int(column_id)
            size_variable = vManager.get_variable(table_id, -1, -1)
            cases = []
            for table_size in range(size_bound + 1):
                size_constraint = Equal_Expression(size_variable, Literal(table_size))
                args = [TRUE([])]
                for tuple_index in range(table_size):
                    variable = vManager.get_variable(table_id, tuple_index, column_id)
                    if i_constraint.split(',')[0] == 'enum':
                        arg = self.__enum_constraints(variable, i_constraint)
                        args.append(arg)
                if len(args) == 1:
                    then = args[0]
                else:
                    then = AND_Expression(args)
                case_then = Implies_Expression([size_constraint, then])
                cases.append(case_then)
            constraints += cases
            # size-free
            # args = []
            # for tuple_index in range(size_bound):
            #     variable = vManager.get_variable(table_id, tuple_index, column_id)
            #     if i_constraint.split(',')[0] == 'enum':
            #         arg = self.__enum_constraints(variable, i_constraint)
            #         args.append(arg)
            # constraints = args
        return AND_Expression(constraints)

    def __str__(self):
        output_str = "input tables:\n"
        for input_schema in self.init_schemas:
            output_str += str(self.init_schemas[input_schema]) + '\n'
        output_str += '\noperations:\n'
        for idx, operation in enumerate(self.operations):
            output_str += f"op{idx}: " + str(operation) + '\n'
        return output_str
