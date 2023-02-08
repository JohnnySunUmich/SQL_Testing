from typing import List, Dict, Any

from z3 import *
from z3 import PatternRef, QuantifierRef, BoolRef, IntNumRef, ArithRef, RatNumRef, AlgebraicNumRef, BitVecNumRef, \
    BitVecRef, ArrayRef, DatatypeRef, FPNumRef, FPRef, FiniteDomainNumRef, FiniteDomainRef, FPRMRef, SeqRef, CharRef, \
    ReRef, ExprRef

from .scope import Scope
from .visitor import Visitor
from .constraints.logic_expressions import Logic_Expression


class Encoder:
    def __init__(self, scope=None):
        if scope is None:
            self.scope = Scope()
        else:
            self.scope = scope
        self.formulas = []
        self.tuples = []

    @staticmethod
    def all_smt(s, initial_terms):
        def block_term(s, m, t):
            s.add(t != m.eval(t, model_completion=True))

        def fix_term(s, m, t):
            s.add(t == m.eval(t, model_completion=True))

        def all_smt_rec(terms):
            if sat == s.check():
                m = s.model()
                yield m
                for i in range(len(terms)):
                    s.push()
                    block_term(s, m, terms[i])
                    for j in range(i):
                        fix_term(s, m, terms[j])
                    yield from all_smt_rec(terms[i:])
                    s.pop()

        yield from all_smt_rec(list(initial_terms))

    def eval(self, table_ids, verbose=False) -> dict[Any, list[Any]]:
        solver = Solver()
        solver.add(And(*self.formulas))
        if solver.check() == unsat:
            raise AssertionError("Formula unsatisfiable")
        model = solver.model()
        if verbose:
            print(model)

        sizes = {table_id: model.eval(
            self.scope.functions['SIZE'](table_id),
            model_completion=True).as_long() for table_id in table_ids}

        db = {}
        for table_id in table_ids:
            columns = []
            for table_column in self.scope.table_columns:
                if table_column[0] == table_id:
                    columns.append(table_column[1])

            table = []
            for i in range(sizes[table_id]):
                row = {}
                for column in columns:
                    if model.eval(self.scope.functions['NULL'](table_id, column, i), model_completion=True):
                        row[column] = None
                    else:
                        row[column] = model.eval(self.scope.table_columns[(table_id, column)](i), model_completion=True)
                table.append(row)

            db[table_id] = table

        return db

    # def eval(self, table_ids, max_solutions=1, verbose=False) -> List[List[Dict[str, Dict | Any]]]:
    #     solver = Solver()
    #     solver.add(And(*self.formulas))
    #     if solver.check() == unsat:
    #         raise AssertionError("Formula unsatisfiable")
    #     if verbose:
    #         print(solver.model())
    #
    #     # evaluate all possible input table sizes
    #     sizes = []
    #     for model in self.all_smt(solver, [self.scope.functions['SIZE'](table_id)]):
    #         sizes.append(model.eval(
    #             self.scope.functions['SIZE'](table_id),
    #             model_completion=True).as_long())
    #
    #     results = []
    #
    #     # prefer small table sizes
    #     sizes.sort()
    #     for size in sizes:
    #         terms = []
    #         columns = []
    #         for table_column in self.scope.table_columns:
    #             if table_column[0] == table_id:
    #                 columns.append(table_column[1])
    #                 for i in range(size):
    #                     terms.append(self.scope.table_columns[table_column](i))
    #                     terms.append(self.scope.functions['NULL'](table_id, table_column[1], i))
    #
    #         for model in self.all_smt(solver, terms):
    #             if max_solutions <= 0:
    #                 return results
    #
    #             output = []
    #             for i in range(size):
    #                 row = {}
    #                 for column in columns:
    #                     if model.eval(self.scope.functions['NULL'](table_id, column, i), model_completion=True):
    #                         row[column] = None
    #                     else:
    #                         row[column] = model.eval(self.scope.table_columns[(table_id, column)](i), model_completion=True)
    #                 output.append(row)
    #
    #             results.append(output)
    #             max_solutions -= 1
    #
    #     return results

    def encode(self, constraints: Logic_Expression, verbose=False) -> None:
        visitor = Visitor(self.scope)
        self.formulas.append(constraints.accept(visitor))
        if verbose:
            print(self.formulas)
