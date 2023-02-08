from .base_expression import Expression


class Literal(Expression):
    def __init__(self, value) -> None:
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"Literal({str(self.value)})"
