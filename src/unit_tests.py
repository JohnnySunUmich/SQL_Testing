import pglast

from constraint_based.encoder import Encoder
from constraint_based.internal_schema import *
from constraint_based.operations.filter import Filter
from constraint_based.operations.project import Project
from constraint_based.commons import get_table_id
from constraint_based.constraints.variables import vManager
from constraint_based.constraints.logic_expressions import AND_Expression
from constraint_based.flatten import Flatten
from constraint_based.constraint_generation import backward_generation
from constraint_based.table_wrapper import gen_database

GT = """
    SELECT T2.y FROM (
        SELECT T1.x, T1.y FROM (
            SELECT T.x, T.y FROM T WHERE T.y < 10
        ) T1
        WHERE T1.x > 10
    ) T2
    WHERE T2.x < 12
"""
mutant = """
    SELECT T2.x FROM (
        SELECT T1.x, T1.y FROM (
            SELECT T.x, T.y FROM T WHERE T.y < 10
        ) T1
        WHERE T1.x >= 10
    ) T2
    WHERE T2.x < 12
"""
ast_gt = pglast.parser.parse_sql(GT)
ast_mutant = pglast.parser.parse_sql(mutant)

predicate1 = ast_gt[0].stmt.fromClause[0].subquery.fromClause[0].subquery.whereClause
predicate2 = ast_gt[0].stmt.fromClause[0].subquery.whereClause
predicate3 = ast_gt[0].stmt.whereClause
predicateM = ast_mutant[0].stmt.fromClause[0].subquery.whereClause

targetList1 = ast_gt[0].stmt.fromClause[0].subquery.fromClause[0].subquery.targetList
targetList2 = ast_gt[0].stmt.fromClause[0].subquery.targetList
targetList3 = ast_gt[0].stmt.targetList

schema = {
        "Tables": [
            {
                "TableName": "T",
                "PKeys": [],
                "FKeys": [],
                "Others": [
                    {
                        "Name": "x",
                        "Type": "int"
                    },
                    {
                        "Name": "y",
                        "Type": "int"
                    }
                ]
            },
            {
                "TableName": "T1",
                "PKeys": [],
                "FKeys": [],
                "Others": [
                    {
                        "Name": "x1",
                        "Type": "int"
                    }
                ]
            }
        ]
    }

def test_filter_constraints():
    vManager.set_bound(2)
    table_id = get_table_id()
    schema = TableSchema(table_id, 'T1')
    schema.append(ColumnSchema(0, 'x', 'int'))
    schema.append(ColumnSchema(1, 'y', 'int'))
    vManager.add_table(schema)

    filter = Filter(schema, predicate2, 2)
    final_cstr = AND_Expression([
        filter.semantic_constraints(),
        filter.mutation_constraints(predicateM),
        # filter.preserving_constraints(),
    ])
    # print(final_cstr)
    encoder = Encoder()
    encoder.encode(final_cstr)
    print(encoder.eval(0, 10))

def test_project_constraints():
    vManager.set_bound(2)
    table_id = get_table_id()
    schema1 = TableSchema(table_id, 'T')
    schema1.append(ColumnSchema(0, 'x', 'int', 't'))
    schema1.append(ColumnSchema(1, 'y', 'int', 't'))
    vManager.add_table(schema1)
    project1 = Project(schema1, targetList1)
    print(project1.semantic_constraints(2))
    vManager.reset()

    table_id = get_table_id()
    schema2 = TableSchema(table_id, 'T2')
    schema2.append(ColumnSchema(0, 'x', 'int', 't2'))
    schema2.append(ColumnSchema(1, 'y', 'int', 't2'))
    vManager.add_table(schema2)
    project2 = Project(schema2, targetList3)
    print(project2.semantic_constraints(2))

def test_flatten():
    fq = Flatten(schema)
    fq.flatten(GT)
    print(fq)

def test_cp_flatten():
    fq = Flatten(schema)
    fq.flatten("""SELECT T1.x1 FROM T1, T WHERE T.x > 0 AND T1.x1 < 0""")
    print(fq)

def test_cp_constraints():
    size_bound = 5
    GT = """SELECT T1.x1 FROM T1, T WHERE T.x > 0 AND T1.x1 < 0"""
    mutant = """SELECT T1.x1 FROM T1, T WHERE T.x > 0 AND T1.x1 <= 0"""
    ast = pglast.parser.parse_sql(mutant)
    predicateM = ast[0].stmt.whereClause
    vManager.reset()
    vManager.set_bound(size_bound)
    constraints = backward_generation(schema, GT, 1, predicateM, size_bound, verbose=True)
    print(constraints)
    return constraints

def test_constraint_generation():
    vManager.reset()
    vManager.set_bound(2)
    constraints = backward_generation(schema, GT, 3, predicateM, 2, verbose=False)
    # print(f"full constraints:\n\t{constraints}")
    return constraints

def test_constraint_solving():
    constraints = test_constraint_generation()
    encoder = Encoder()
    encoder.encode(constraints)

    solution = encoder.eval(0, max_solutions=1)
    database = gen_database(solution)
    # print(database)

def test_solving_cp():
    constraints = test_cp_constraints()
    encodings = Encoder()
    encodings.encode(constraints)

    solution0 = encodings.eval(0, max_solutions=1)
    solution1 = encodings.eval(1, max_solutions=1)
    print(solution0, solution1)
    database = gen_database(solution0+solution1)
    print(database)



if __name__ == '__main__':
    import sys
    mode = sys.argv[1]
    if mode == 'filter':
        test_filter_constraints()
    elif mode == 'project':
        test_project_constraints()
    elif mode == 'flatten':
        test_flatten()
    elif mode == 'constraints':
        test_constraint_generation()
    elif mode == 'solving':
        test_constraint_solving()
    elif mode == 'flatten_cp':
        test_cp_flatten()
    elif mode == 'constraint_cp':
        test_cp_constraints()
    elif mode == 'solving_cp':
        test_solving_cp()

