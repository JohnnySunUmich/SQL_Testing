from copy import deepcopy

from .flatten import Flatten
from .constraints.logic_expressions import AND_Expression, TRUE
from .constraints.variables import vManager


class Constraint_Generator:
    def __init__(self, schema: dict, groundtruth: str,
                 initial_size_bound: int = 2, mode: str = "optimistic", verbose: bool = False):
        self.flattened_mutant = None
        self.mutation_type = None
        self.schema = schema
        self.flattner = Flatten(schema, initial_size_bound, mode)
        self.flattner.flatten(groundtruth)
        self.flattened_groundtruth = self.flattner.operations
        self.mutation_point = -1
        self.integrity_constraints = self.flattner.integrity_constraints(initial_size_bound)
        self.verbose = verbose
        if self.verbose:
            print(f"operations of flattened groundtruth:\n{self.flattner}")

    def load_mutant(self, mutant: str, mutation_type: str = "predicate"):
        self.mutation_point = -1
        if self.verbose:
            print(f"loading mutant {mutant}")
        self.mutation_type = mutation_type
        try:
            self.flattner.flatten(mutant)
        except Exception:
            print(f"syntax error in the mutant")
            return False
        self.flattened_mutant = self.flattner.operations
        if self.verbose:
            print(f"operations of flattened mutant:\n{self.flattner}")
        index = 0
        for m_op, op in zip(self.flattened_mutant, self.flattened_groundtruth):
            if m_op != op:
                self.mutation_point = index
                m_op.copy_input_schema(op)
                if self.verbose:
                    print(f"identified mutation point at op{self.mutation_point}:\n{m_op}")
                break
            index += 1
        if self.mutation_point == -1:
            print(f"skip mutant because no mutation operator is identified")
            return False
        return True

    def generate_constraints(self):
        if self.verbose:
            print(f"parsing integrity constraints:\n{self.integrity_constraints}")
        constraints = [self.integrity_constraints]
        for idx, operation in enumerate(self.flattened_groundtruth):
            if idx < self.mutation_point:
                semantic = operation.semantic_constraints()
                constraints.append(semantic)
                if self.verbose:
                    print(f"semantic of {operation}\n{semantic}\n\n")
            elif idx == self.mutation_point:
                semantic = operation.semantic_constraints()
                GMC = operation.mutation_constraints(mutant=self.flattened_mutant[idx],
                                                     mutation_type=self.mutation_type)
                mutant_semantic = self.flattened_mutant[idx].semantic_constraints()
                constraints += [semantic, GMC, mutant_semantic]
                if self.verbose:
                    print(f"semantic of {operation}\n{semantic}\n\n")
                    print(f"semantic of mutant {self.flattened_mutant[idx]}\n{mutant_semantic}\n\n")
                    print(f"GMC\n\n{GMC}\n\n")
            else:
                semantic = operation.semantic_constraints()
                GPC = operation.preserving_constraints()
                mutant_semantic = self.flattened_mutant[idx].semantic_constraints()
                mutant_GPC = self.flattened_mutant[idx].preserving_constraints()
                if self.verbose:
                    print(f"semantic of {operation}\n{semantic}\n\n")
                    print(f"semantic of mutant {self.flattened_mutant[idx]}\n{mutant_semantic}\n\n")
                    print(f"GPC of {operation}\n{GPC}\n\n")
                    print(f"GPC of mutant {operation}\n{mutant_GPC}\n\n")
                constraints += [semantic, GPC, mutant_semantic, mutant_GPC]
        constraints.append(self.integrity_constraints)
        return AND_Expression(constraints)
