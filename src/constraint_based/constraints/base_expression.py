class Expression:
    def accept(self, visitor):
        method_name = f'visit_{self.__class__.__name__.lower()}'
        visit = getattr(visitor, method_name)
        return visit(self)
