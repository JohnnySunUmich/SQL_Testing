from pglast import enums
from pglast.visitors import Delete
from pglast import parser
from pglast.visitors import Visitor
from pglast.stream import IndentedStream, RawStream
from pglast import ast
from copy import deepcopy

# potential mutant operator
class OrderMutant(Visitor):
    def __init__(self):
        super().__init__()
        self.mutant_list = []
    
    def visit(self, ancestors, node):
        pass

# current support operater
class OnMutant(Visitor):
    def __init__(self):
        super().__init__()
        self.mutant_list = []
    
    def visit(self, ancestors, node):
        if hasattr(node, 'quals'):
            # keep record of previous quals
            prev_quals = deepcopy(node.quals)
            # generate mutant for onClause
            # case 1: drop all onClause
            if node.quals != None and node.isNatural:
                node.quals= None
                mutant = deepcopy(self.root)
                self.mutant_list.append(mutant)
                node.quals = prev_quals

            # case 2: drop one predicate of quals
            sub_clause = [node.quals]
            while len(sub_clause) > 0:
                if not isinstance(sub_clause[0], ast.BoolExpr):
                    sub_clause.pop(0)
                    continue
                
                prev_args = deepcopy(sub_clause[0].args)
                prev_args_list = list(prev_args)
                # print("Current sub_clause: ", RawStream()(sub_clause[0]))
                if len(prev_args) > 0:
                    for i in range(len(prev_args)):
                        if isinstance(prev_args_list[i], ast.BoolExpr):
                            continue
                        new_args_list = deepcopy(prev_args_list)
                        new_args_list.pop(i)
                        new_args = tuple(new_args_list)
                        sub_clause[0].args = new_args
                        mutant = deepcopy(self.root)
                        self.mutant_list.append(mutant)
                        sub_clause[0].args = prev_args
                
                for arg in sub_clause[0].args:
                    sub_clause.append(arg)

                sub_clause.pop(0)

            # # case 3: change comparison operator
            sub_clause = [node.quals]
            op_list = ['=', '>', '<', '>=', '<=', '!=']
            while len(sub_clause) > 0:
                if isinstance(sub_clause[0], ast.BoolExpr):
                    for arg in sub_clause[0].args:
                        sub_clause.append(arg)
                    sub_clause.pop(0)
                    continue
                
                if not isinstance(sub_clause[0], ast.A_Expr):
                    sub_clause.pop(0)
                    continue
                
                sub_clause.append(sub_clause[0].lexpr)
                sub_clause.append(sub_clause[0].rexpr)

                prev_op = deepcopy(sub_clause[0].name)
                for op in op_list:
                    if ast.String(op) == sub_clause[0].name[0]:
                        continue

                    sub_clause[0].name = (ast.String(op),)
                    mutant = deepcopy(self.root)
                    self.mutant_list.append(mutant)
                    sub_clause[0].name = prev_op
                
                sub_clause.pop(0)

            # # case 4: change logic operator
            sub_clause = [node.quals]
            while len(sub_clause) > 0:
                if not isinstance(sub_clause[0], ast.BoolExpr):
                    sub_clause.pop(0)
                    continue
                
                prev_op = deepcopy(sub_clause[0].boolop)
                prev_args = deepcopy(sub_clause[0].args)
                if len(sub_clause[0].args) > 2:
                    for i in range(1,len(sub_clause[0].args)):
                        left_args = sub_clause[0].args[:i]
                        right_args = sub_clause[0].args[i:]
                        new_lexpr = ast.BoolExpr(prev_op, left_args)
                        new_rexpr = ast.BoolExpr(prev_op, right_args)
                        if prev_op == enums.BoolExprType.AND_EXPR:
                            sub_clause[0].boolop = enums.BoolExprType.OR_EXPR
                        else:
                            sub_clause[0].boolop = enums.BoolExprType.AND_EXPR
                        sub_clause[0].args = [new_lexpr, new_rexpr]
                        mutant = deepcopy(self.root)
                        self.mutant_list.append(mutant)
                        sub_clause[0].boolop = prev_op
                        sub_clause[0].args = prev_args
                else:
                    if sub_clause[0].boolop == enums.BoolExprType.AND_EXPR:
                        sub_clause[0].boolop = enums.BoolExprType.OR_EXPR
                        mutant = deepcopy(self.root)
                        self.mutant_list.append(mutant)
                        sub_clause[0].boolop = enums.BoolExprType.AND_EXPR
                    elif sub_clause[0].boolop == enums.BoolExprType.OR_EXPR:
                        sub_clause[0].boolop = enums.BoolExprType.AND_EXPR
                        mutant = deepcopy(self.root)
                        self.mutant_list.append(mutant)
                        sub_clause[0].boolop = enums.BoolExprType.OR_EXPR
                
                for arg in sub_clause[0].args:
                    sub_clause.append(arg)

                sub_clause.pop(0)

class HavingMutant(Visitor):
    def __init__(self):
        super().__init__()
        self.mutant_list = []
    
    def visit(self, ancestors, node):
        if hasattr(node, 'havingClause'):
            # keep record of previous havingClause
            prev_havingClause = deepcopy(node.havingClause)
            # generate mutant for havingClause
            # case 1: drop all havingClause
            if node.havingClause != None:
                node.havingClause = None
                mutant = deepcopy(self.root)
                self.mutant_list.append(mutant)
                node.havingClause = prev_havingClause

            # case 2: drop one predicate of havingClause
            sub_clause = [node.havingClause]
            while len(sub_clause) > 0:
                if not isinstance(sub_clause[0], ast.BoolExpr):
                    sub_clause.pop(0)
                    continue
                
                prev_args = deepcopy(sub_clause[0].args)
                prev_args_list = list(prev_args)
                # print("Current sub_clause: ", RawStream()(sub_clause[0]))
                if len(prev_args) > 0:
                    for i in range(len(prev_args)):
                        if isinstance(prev_args_list[i], ast.BoolExpr):
                            continue
                        new_args_list = deepcopy(prev_args_list)
                        new_args_list.pop(i)
                        new_args = tuple(new_args_list)
                        sub_clause[0].args = new_args
                        mutant = deepcopy(self.root)
                        self.mutant_list.append(mutant)
                        sub_clause[0].args = prev_args
                
                for arg in sub_clause[0].args:
                    sub_clause.append(arg)

                sub_clause.pop(0)

            # # case 3: change comparison operator
            sub_clause = [node.havingClause]
            op_list = ['=', '>', '<', '>=', '<=', '!=']
            while len(sub_clause) > 0:
                if isinstance(sub_clause[0], ast.BoolExpr):
                    for arg in sub_clause[0].args:
                        sub_clause.append(arg)
                    sub_clause.pop(0)
                    continue
                
                if not isinstance(sub_clause[0], ast.A_Expr):
                    sub_clause.pop(0)
                    continue
                
                sub_clause.append(sub_clause[0].lexpr)
                sub_clause.append(sub_clause[0].rexpr)

                prev_op = deepcopy(sub_clause[0].name)
                for op in op_list:
                    if ast.String(op) == sub_clause[0].name[0]:
                        continue

                    sub_clause[0].name = (ast.String(op),)
                    mutant = deepcopy(self.root)
                    self.mutant_list.append(mutant)
                    sub_clause[0].name = prev_op
                
                sub_clause.pop(0)

            # # case 4: change logic operator
            sub_clause = [node.havingClause]
            while len(sub_clause) > 0:
                if not isinstance(sub_clause[0], ast.BoolExpr):
                    sub_clause.pop(0)
                    continue
                
                prev_op = deepcopy(sub_clause[0].boolop)
                prev_args = deepcopy(sub_clause[0].args)
                if len(sub_clause[0].args) > 2:
                    for i in range(1,len(sub_clause[0].args)):
                        left_args = sub_clause[0].args[:i]
                        right_args = sub_clause[0].args[i:]
                        new_lexpr = ast.BoolExpr(prev_op, left_args)
                        new_rexpr = ast.BoolExpr(prev_op, right_args)
                        if prev_op == enums.BoolExprType.AND_EXPR:
                            sub_clause[0].boolop = enums.BoolExprType.OR_EXPR
                        else:
                            sub_clause[0].boolop = enums.BoolExprType.AND_EXPR
                        sub_clause[0].args = [new_lexpr, new_rexpr]
                        mutant = deepcopy(self.root)
                        self.mutant_list.append(mutant)
                        sub_clause[0].boolop = prev_op
                        sub_clause[0].args = prev_args
                else:
                    if sub_clause[0].boolop == enums.BoolExprType.AND_EXPR:
                        sub_clause[0].boolop = enums.BoolExprType.OR_EXPR
                        mutant = deepcopy(self.root)
                        self.mutant_list.append(mutant)
                        sub_clause[0].boolop = enums.BoolExprType.AND_EXPR
                    elif sub_clause[0].boolop == enums.BoolExprType.OR_EXPR:
                        sub_clause[0].boolop = enums.BoolExprType.AND_EXPR
                        mutant = deepcopy(self.root)
                        self.mutant_list.append(mutant)
                        sub_clause[0].boolop = enums.BoolExprType.OR_EXPR
                
                for arg in sub_clause[0].args:
                    sub_clause.append(arg)

                sub_clause.pop(0)

class DistinctMutant(Visitor):
    def __init__(self):
        super().__init__()
        self.mutant_list = []
    
    def visit(self, ancestors, node):
        if isinstance(node, ast.SelectStmt):
            prev_distinctClause = deepcopy(node.distinctClause)
            if node.distinctClause == None:
                node.distinctClause = [None]
                mutant = deepcopy(self.root)
                self.mutant_list.append(mutant)
                node.distinctClause = prev_distinctClause
            else: 
                node.distinctClause = None
                mutant = deepcopy(self.root)
                self.mutant_list.append(mutant)
                node.distinctClause = prev_distinctClause
        elif isinstance(node, ast.FuncCall):
            if node.agg_distinct:
                node.agg_distinct = False
                mutant = deepcopy(self.root)
                self.mutant_list.append(mutant)
                node.agg_distinct = True
            else:
                if node.args != None:
                    node.agg_distinct = True
                    mutant = deepcopy(self.root)
                    self.mutant_list.append(mutant)
                    node.agg_distinct = False


class JoinMutant(Visitor):
    def __init__(self):
        super().__init__()
        self.mutant_list = []
    
    def visit(self, ancestors, node):
        # case 1: natural join or not
        if hasattr(node, "isNatural"):
            prev_isNatural = deepcopy(node.isNatural)
            prev_quals = deepcopy(node.quals)
            node.isNatural= ~prev_isNatural
            if node.isNatural:
                node.quals = None
            mutant = deepcopy(self.root)
            self.mutant_list.append(mutant)
            node.isNatural = prev_isNatural
            node.quals = prev_quals
        
        # case 2: join types
        if hasattr(node, 'jointype'):
            jointype_list = [enums.JoinType.JOIN_FULL, enums.JoinType.JOIN_INNER, enums.JoinType.JOIN_LEFT,
                             enums.JoinType.JOIN_RIGHT]
            # jointype_list = [enums.JoinType.JOIN_ANTI, enums.JoinType.JOIN_FULL, enums.JoinType.JOIN_INNER, enums.JoinType.JOIN_LEFT,
            #                  enums.JoinType.JOIN_RIGHT, enums.JoinType.JOIN_SEMI, enums.JoinType.JOIN_UNIQUE_INNER, 
            #                  enums.JoinType.JOIN_UNIQUE_OUTER]
            prev_jointype = deepcopy(node.jointype)
            for join_type in jointype_list:
                if join_type == node.jointype:
                    continue
                else:
                    node.jointype = join_type
                    mutant = deepcopy(self.root)
                    self.mutant_list.append(mutant)
                    node.jointype = prev_jointype


class WhereMutant(Visitor):
    def __init__(self):
        super().__init__()
        self.mutant_list = []
    
    def visit(self, ancestors, node):
        if hasattr(node, 'whereClause'):
            # keep record of previous whereClause
            prev_whereClause = deepcopy(node.whereClause)

            # generate mutant for whereClause
            # case 1: drop all whereClause
            if node.whereClause != None:
                # node.whereClause = None
                new_whereClause = ast.A_Expr()
                new_whereClause.lexpr = ast.A_Const(1)
                new_whereClause.rexpr = ast.A_Const(1)
                new_whereClause.kind = enums.A_Expr_Kind.AEXPR_OP
                new_whereClause.name = ["=",]
                node.whereClause = new_whereClause
                mutant = deepcopy(self.root)
                self.mutant_list.append(mutant)
                node.whereClause = prev_whereClause

            # case 2: drop one predicate of whereClause
            # print(node.whereClause.args)
            # mutant = deepcopy(self.root)
            # self.mutant_list.append(mutant)
            sub_clause = [node.whereClause]
            # cnt = 0
            while len(sub_clause) > 0:
                # print(cnt, ": ")
                # cnt = cnt + 1
                # print(isinstance(sub_clause[0], ast.BoolExpr))
                # print(sub_clause[0])
                if not isinstance(sub_clause[0], ast.BoolExpr):
                    sub_clause.pop(0)
                    continue
                
                # print(type(sub_clause[0]))
                prev_args = deepcopy(sub_clause[0].args)
                prev_args_list = list(prev_args)
                # print(type(prev_args))
                # print("Current sub_clause: ", RawStream()(sub_clause[0]))
                if len(prev_args) > 0:
                    for i in range(len(prev_args)):
                        if isinstance(prev_args_list[i], ast.BoolExpr):
                            continue
                        new_args_list = deepcopy(prev_args_list)
                        new_args_list.pop(i)
                        new_args = tuple(new_args_list)
                        sub_clause[0].args = new_args
                        mutant = deepcopy(self.root)
                        self.mutant_list.append(mutant)
                        sub_clause[0].args = prev_args
                
                for arg in sub_clause[0].args:
                    sub_clause.append(arg)
                # else:
                #     # sub_clause = ast.Node()
                #     prev_args = deepcopy(sub_clause[0].args)
                #     prev_lexp = deepcopy(sub_clause[0].args[0])
                #     prev_rexp = deepcopy(sub_clause[0].args[1])
                #     # sub_clause[0] = deepcopy(prev_lexp)
                #     # print("Current sub_clause_args: ", RawStream()(prev_lexp), RawStream()(prev_rexp))
                #     if not isinstance(prev_lexp, ast.BoolExpr):
                #         sub_clause[0].args = [prev_lexp]
                #     # print("Current mutant sub_clause: ", RawStream()(sub_clause[0]))
                #         mutant = deepcopy(self.root)
                #     # print("Current mutant: ", RawStream()(mutant))
                #         self.mutant_list.append(mutant)
                #     if not isinstance(prev_rexp, ast.BoolExpr):
                #         sub_clause[0].args = [prev_rexp]
                #     # print("Current mutant sub_clause: ", RawStream()(sub_clause[0]))
                #         mutant = deepcopy(self.root)
                #         self.mutant_list.append(mutant)
                #     sub_clause[0].args = prev_args

                sub_clause.pop(0)
                # print("sub_clause: ", sub_clause)

            # case 3: change comparison operator
            sub_clause = [node.whereClause]
            op_list = ['=', '>', '<', '>=', '<=', '!=']
            # cnt = 0
            while len(sub_clause) > 0:
                # print(cnt, ": ")
                # cnt = cnt + 1
                # print(isinstance(sub_clause[0], ast.BoolExpr))
                # print(sub_clause[0])
                if isinstance(sub_clause[0], ast.BoolExpr):
                    for arg in sub_clause[0].args:
                        sub_clause.append(arg)
                    sub_clause.pop(0)
                    continue
                
                if not isinstance(sub_clause[0], ast.A_Expr):
                    sub_clause.pop(0)
                    continue
                
                sub_clause.append(sub_clause[0].lexpr)
                sub_clause.append(sub_clause[0].rexpr)

                # print(sub_clause[0].name)
                # print(sub_clause[0])
                prev_op = deepcopy(sub_clause[0].name)
                for op in op_list:
                    if ast.String(op) == sub_clause[0].name[0]:
                        # print(op, sub_clause[0].name, "same")
                        continue
                    # print(ast.String(op), sub_clause[0].name, "different", type(op[0]), type(sub_clause[0].name[0]))
                    sub_clause[0].name = (ast.String(op),)
                    mutant = deepcopy(self.root)
                    self.mutant_list.append(mutant)
                    sub_clause[0].name = prev_op
                
                sub_clause.pop(0)
                # print("sub_clause: ", sub_clause)

            # case 4: change logic operator
            # print(node.whereClause.boolop)
            sub_clause = [node.whereClause]
            # cnt = 0
            while len(sub_clause) > 0:
                # print(cnt, ": ")
                # cnt = cnt + 1
                # print(isinstance(sub_clause[0], ast.BoolExpr))
                # print(sub_clause[0])
                if not isinstance(sub_clause[0], ast.BoolExpr):
                    sub_clause.pop(0)
                    continue
                
                prev_op = deepcopy(sub_clause[0].boolop)
                prev_args = deepcopy(sub_clause[0].args)
                if len(sub_clause[0].args) > 2:
                    for i in range(1,len(sub_clause[0].args)):
                        left_args = sub_clause[0].args[:i]
                        right_args = sub_clause[0].args[i:]
                        new_lexpr = ast.BoolExpr(prev_op, left_args)
                        new_rexpr = ast.BoolExpr(prev_op, right_args)
                        if prev_op == enums.BoolExprType.AND_EXPR:
                            sub_clause[0].boolop = enums.BoolExprType.OR_EXPR
                        else:
                            sub_clause[0].boolop = enums.BoolExprType.AND_EXPR
                        sub_clause[0].args = [new_lexpr, new_rexpr]
                        mutant = deepcopy(self.root)
                        self.mutant_list.append(mutant)
                        sub_clause[0].boolop = prev_op
                        sub_clause[0].args = prev_args
                else:
                    if sub_clause[0].boolop == enums.BoolExprType.AND_EXPR:
                        sub_clause[0].boolop = enums.BoolExprType.OR_EXPR
                        mutant = deepcopy(self.root)
                        self.mutant_list.append(mutant)
                        sub_clause[0].boolop = enums.BoolExprType.AND_EXPR
                    elif sub_clause[0].boolop == enums.BoolExprType.OR_EXPR:
                        sub_clause[0].boolop = enums.BoolExprType.AND_EXPR
                        mutant = deepcopy(self.root)
                        self.mutant_list.append(mutant)
                        sub_clause[0].boolop = enums.BoolExprType.OR_EXPR
                
                for arg in sub_clause[0].args:
                    sub_clause.append(arg)

                sub_clause.pop(0)
                # print("sub_clause: ", sub_clause)

# def generate_mutants(psql_query: str) -> List[Union[None, pglast.ast.SelectStmt]]:
def generate_mutants(psql_query: str):
    mutants = dict()
    # print("Query(String) before whereClause mutant processing:")
    # print(psql_query)
    rawstmt = parser.parse_sql(psql_query)
    # print("Query(stmt) before whereClause mutant processing:")
    # print(RawStream()(rawstmt))

    where_mutant_generator = WhereMutant()
    where_mutant_generator(rawstmt)
    mutants["predicate"] = where_mutant_generator.mutant_list
    # print("whereClause mutants:")
    # for mutant in where_mutant_generator.mutant_list:
        # print(RawStream()(mutant))
    # print("Query after whereClause mutant processing:")
    # print(RawStream()(rawstmt))

    jointype_mutant_generator = JoinMutant()
    jointype_mutant_generator(rawstmt)
    mutants["join_type"] = jointype_mutant_generator.mutant_list
    # print("jointype mutants:")
    # for mutant in jointype_mutant_generator.mutant_list:
    #     print(RawStream()(mutant))
    # print("Query after jointype mutant processing:")
    # print(RawStream()(rawstmt))

    distinct_mutant_generator = DistinctMutant()
    distinct_mutant_generator(rawstmt)
    mutants["distinct"] = distinct_mutant_generator.mutant_list
    # print("distinct mutants:")
    # for mutant in distinct_mutant_generator.mutant_list:
        # print(RawStream()(mutant))
    # print("Query after distinct mutant processing:")
    # print(RawStream()(rawstmt))

    havingClause_mutant_generator = HavingMutant()
    havingClause_mutant_generator(rawstmt)
    mutants["predicate"] += havingClause_mutant_generator.mutant_list
    # print("havingClause mutants:")
    # for mutant in havingClause_mutant_generator.mutant_list:
        # print(RawStream()(mutant))
    # print("Query after havingClause mutant processing:")
    # print(RawStream()(rawstmt))

    onClause_mutant_generator = OnMutant()
    onClause_mutant_generator(rawstmt)
    mutants["predicate"] += onClause_mutant_generator.mutant_list
    # print("onClause mutants:")
    # for mutant in onClause_mutant_generator.mutant_list:
    #     print(RawStream()(mutant))
    # print("Query after onClause mutant processing:")
    # print(RawStream()(rawstmt))
    return mutants
    # print(rawstmt)

def main():
    # example for where-clause mutants
    # query = "select a.x, b.y from a join b on a.bid = b.id where a.x = 1 and b.y = 0 or b.y > 1 or b.y < 3"
    query = "select product_id, year as first_year, quantity, price from sales where (product_id, year) in (select product_id, min(year) from sales group by product_id)"
    # example for on-clause mutants
    # query = "SELECT x1, x2 FROM T1 JOIN T2 ON T1.x1 > 0 AND T1.y1 = T2.y2"
    # example for having-clause mutants
    # query = "SELECT sum(x) FROM T GROUP BY y HAVING (min(x) > 0 AND max(x) < 10) OR (min(x) > 20 AND max(x) < 30)"
    # query = "SELECT sum(x) FROM T GROUP BY y HAVING min(x) > 0 AND max(x) < 10"
    # example for keyword distinct mutants
    # query = "SELECT x, y FROM T WHERE T.x >=0 and T.y < 0"
    # example for join type mutants
    # query = "SELECT x1, x2 FROM T1 JOIN T2 ON T1.x1 = T2.x1 and T1.x2 > T2.x2"

    # queries from groundtruth
    # query = "SELECT actor_id,director_id FROM ActorDirector GROUP BY actor_id,director_id HAVING COUNT(*)>=3"
    # print(parser.parse_sql(query))
    mutants = generate_mutants(query)

if __name__ == "__main__":
    main()