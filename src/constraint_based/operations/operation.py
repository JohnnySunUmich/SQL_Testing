class Operation:
    def __init__(self):
        self.input_schema = None
        self.output_schema = None

    def semantic_constraints(self):
        pass

    def mutation_constraints(self, mutant, mutation_type: str="predicate"):
        pass

    def preserving_constraints(self):
        pass

    def mutated_semantic_constraint(self, mutant):
        pass

    def __str__(self):
        return ""
