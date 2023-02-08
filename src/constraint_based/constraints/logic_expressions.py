from .base_expression import Expression
from .comparison_expressions import *


class Logic_Expression(Expression):
    def __init__(self, args) -> None:
        if not isinstance(args, list):
            raise Exception("not a list")
        self.args = args

    def __str__(self) -> str:
        args_str = ""
        for i, arg in enumerate(self.args):
            args_str += str(arg)
            if i != len(self.args) - 1:
                args_str += ', '
        return args_str

    def __repr__(self) -> str:
        args_str = ""
        for i, arg in enumerate(self.args):
            args_str += str(arg)
            if i != len(self.args) - 1:
                args_str += ', '
        return args_str

    def change_table_id(self, table_id, new_table_id):
        for arg in self.args:
            arg.change_table_id(table_id, new_table_id)


class AND_Expression(Logic_Expression):
    def __str__(self):
        if len(self.args) >= 5:
            return '\n∧ '.join([str(arg) for arg in self.args])
        return ' ∧ '.join([str(arg) for arg in self.args])

    def __repr__(self):
        args_str = super().__str__()
        return f"AND({args_str})"


class OR_Expression(Logic_Expression):
    def __str__(self):
        return ' ∨ '.join([str(arg) for arg in self.args])

    def __repr__(self):
        args_str = super().__str__()
        return f"OR({args_str})"


class NOT_Expression(Logic_Expression):
    def __str__(self):
        return f'¬({self.args[0]})'

    def __repr__(self):
        args_str = super().__str__()
        return f"NOT({args_str})"


class Implies_Expression(Logic_Expression):
    def __str__(self):
        return f'\n({self.args[0]}) -> ({self.args[1]})'

    def __repr__(self):
        args_str = super().__str__()
        return f"\nIMPLIES({args_str})"


class Id_Expression(Logic_Expression):
    def __str__(self):
        return f'{self.args[0]}'

    def __repr__(self):
        args_str = super().__str__()
        return f"{args_str}"


class TRUE(Logic_Expression):
    def __str__(self) -> str:
        return "TRUE"

    def __repr__(self):
        return "TRUE"
