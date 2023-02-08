query = "SELECT T1.y, T2.y FROM T1 JOIN T2 ON T1.x = 10 AND T1.x = T2.x"

mutants = {
        # "SELECT T1.y, T2.y FROM T1 JOIN T2 ON T1.x >= 10 AND T1.x = T2.x",
        # "SELECT T1.y, T2.y FROM T1 JOIN T2 ON T1.x >= 10",
        "join_type": "SELECT T1.y, T2.y FROM T1 LEFT JOIN T2 ON T1.x = 10 AND T1.x = T2.x"
}

schema = {
        "Tables": [
            {
                "TableName": "T1",
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
                "TableName": "T2",
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
            }
        ]
}

from constraint_based.constraint_generation import Constraint_Generator
from constraint_based.constraints.logic_expressions import TRUE
from constraint_based.constraints.variables import vManager
from constraint_based.encoder import Encoder

vManager.reset()

generator = Constraint_Generator(schema, query, TRUE([]), 2, verbose=True, mode="pessimistic")

encoder = Encoder()

for mutation_type in mutants:
    generator.load_mutant(mutants[mutation_type], mutation_type=mutation_type)
    constraints = generator.generate_constraints()
    encoder.encode(constraints, verbose=True)
    T0 = encoder.eval(0, max_solutions=1)
    T1 = encoder.eval(1, max_solutions=1)
    print(T0, T1)

