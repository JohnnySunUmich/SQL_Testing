import pglast.parser
import pglast.ast
from typing import List, Union

def generate_mutants(psql_query: str) -> List[Union[None, pglast.ast.SelectStmt]]:
    # TODO: impl mutation function
    ast = pglast.parser.parse_sql(psql_query)
    return [ast[0].stmt]