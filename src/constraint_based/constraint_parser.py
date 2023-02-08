import yaml
from lark import (
    Lark,
    Transformer,
)


def remove(string):
    return string.replace(" ", "")


class Debug():
    def check(self, list):
        ret = True
        for y in list:
            for key in y.keys():
                if (Debug.readYML(key, y[key]) == False):
                    ret = False
                    break
        if (ret):
            print('Success')
        else:
            print('Error')

    def readYML(key, value):
        with open('data/constraints/1789.yml', 'r') as file:
            constraints = yaml.safe_load(file)

        comparison = {"gt": ">", "gte": ">=", "lt": "<",
                      "lte": "<=", "neq": "!=", "join": "^", "equal": "="}
        # ROW DEPENDENCE
        if (key == 'distinct' or key == 'inc' or key == 'dec' or key == 'consec'):
            row_dep = constraints['row_dep']
            if (key == 'distinct'):
                constraintc = 'unique('
                for i in range(0, len(value)-1):
                    constraintc += value[i]+','
                constraintc += value[len(value)-1]+')'
                return constraintc in remove(row_dep)

            else:
                constraintc = key+'('+value[0]+')'
                return constraintc in row_dep

        # comparisons
        elif (key == 'gt' or key == 'gte' or key == 'lt' or key == 'lte' or key == 'neq' or key == 'join' or key == 'equal'):
            col_dep = ''
            col_val = ''
            if 'col_dep' in constraints:
                col_dep = constraints['col_dep']

            if 'col_val' in constraints:
                col_val = constraints['col_val']

            constraintc = value[0]+comparison[key]+str(value[1])
            return bool(constraintc in remove(col_dep) or constraintc in remove(col_val))

        elif (key == 'eq' or key == 'and' or key == 'inclusion' or key == 'inclusion1' or key == 'override' or key == 'or'):
            col_dep = ''
            col_val = ''
            if 'col_dep' in constraints:
                col_dep = constraints['col_dep']
            if 'col_val' in constraints:
                col_val = constraints['col_val']

            if (key == 'override'):
                constraintc = value+'|'
                return constraintc in remove(col_val)
            if (key == 'eq'):
                constraintc = value[0]+'<-'+value[1]
                return constraintc in remove(col_dep)
            if (key == 'and'):
                constraintc = str(value[0]['gte'][1])+'<-'+'['
                for i in range(0, len(value)):
                    y = value[i]
                    for key in value[i].keys():
                        constraintc += str(value[i][key][0])+','
                constraintc = constraintc[:len(constraintc)-1]
                constraintc += ']'
                return constraintc in remove(col_val)

            if (key == 'or'):
                constraintc = value[0]['eq'][0]+'<-'+'{'
                for i in range(0, len(value)-1):
                    constraintc += "'" + \
                        (value[i]['eq'][1])+"'"+','

                constraintc += "'" + \
                    value[len(value)-1]['eq'][1]+"'"+'}'
                return bool(constraintc in remove(col_val))

            if (key == 'inclusion' or key == 'inclusion1'):
                constraintc = ''
                if (key == 'inclusion'):
                    constraintc += value[0]['from'][0] + \
                        '->['+value[0]['from'][1]+','+value[1]['to'][1]+']'
                    return (constraintc in remove(col_val))

                if (key == 'inclusion1'):
                    constraintc += value[0]['val'][0] + \
                        '->{'+"'"+value[0]['val'][1]+"'"
                    for i in range(1, len(value)):
                        constraintc += ','+"'"+value[1]['val'][1]+"'"
                    constraintc += '}'
                    return (constraintc in remove(col_val))

        elif (key == 'if'):
            constraintc = value[0]['col1a']+comparison[value[1]['comp1']]+value[2]['col1b'] + \
                "=>"+value[3]['col2a'] + \
                comparison[value[4]['comp2']]+value[5]['col2b']
            return constraintc in remove(constraints['col_dep'])

        else:
            print('invalid constraint detected')
            print(key)
            return False


class ConstraintVisitor(Transformer):
    def constraints(self, tree):
        return [node for node in tree if node is not None]

    def membership(self, tree):
        # Column dependence
        # Example: Employee.departmentId <- Department.id
        if isinstance(tree[1], str):
            return {'eq': tree}
        # Column value membership
        # Example: X.Y <- [0,10]
        elif isinstance(tree[1], tuple):
            lower_bound = tree[1][0]
            upper_bound = tree[1][1]
            return {'and': [{'gte': [lower_bound, tree[0]]}, {'lte': [upper_bound, tree[0]]}]}
        # Column value membership
        # Example: SurveyLog.action <- {'show', 'answer', 'skip'}
        elif isinstance(tree[1], list):
            disjunction = []
            for value in tree[1]:
                disjunction.append({'eq': [str(tree[0]),  value]})
            if len(disjunction) == 1:
                return disjunction[0]
            else:
                return {'or': disjunction}
        else:
            raise NotImplementedError

    def inclusion(self, tree):
        # Column value membership
        # Example: X.Y -> [0,10]
        if isinstance(tree[1], tuple):
            lower_bound = tree[1][0]
            upper_bound = tree[1][1]
            return {'inclusion': [{'from': [tree[0], lower_bound]}, {'to': [tree[0], upper_bound]}]}
        # Column value membership
        # Example: SurveyLog.action -> {'show', 'answer', 'skip'}
        elif isinstance(tree[1], list):
            disjunction = []
            for value in tree[1]:
                disjunction.append({'val': [tree[0], value]})
            return {'inclusion1': disjunction}
        else:
            raise NotImplementedError

    def not_null(self, tree):
        # {'exists': 'AGE'}
        attr = tree[0]
        if isinstance(attr, dict):
            attr = attr['value']
        return {'exists': attr}

    def if_then(self, tree):
        attr = tree[0]
        comp = tree[1]
        attr2 = tree[2]
        attr3 = tree[3]
        comp2 = tree[4]
        attr4 = tree[5]
        return {'if': [{'col1a': attr}, {'comp1': comp}, {'col1b': attr2}, {'col2a': attr3}, {'comp2': comp2}, {'col2b': attr4}]}

    def comparison(self, tree):
        operands = [tree[0], tree[2]]
        operator = tree[1]
        return {operator: operands}

    def unique(self, tree):
        return {'distinct': [node for node in tree]}

    def increment(self, tree):
        return {'inc': [node for node in tree]}

    def dec(self, tree):
        return {'dec': [node for node in tree]}

    def consec(self, tree):
        return {'consec': [node for node in tree]}

    def override(self, tree):
        return {'override': tree[0]}

    def op(self, tree):
        operator = str(tree[0])
        if operator == '>':
            return 'gt'
        elif operator == '>=':
            return 'gte'
        elif operator == '<':
            return 'lt'
        elif operator == '<=':
            return 'lte'
        elif operator == '!=':
            return 'neq'
        elif operator == '^':
            return 'join'
        elif operator == '=':
            return 'equal'
        else:
            raise NotImplementedError(operator)

    def attribute(self, tree):
        return f"{tree[0]}.{tree[1]}"

    def NUMBER(self, tree):
        return eval(tree)

    def null(self, tree):
        return None

    def value_range(self, tree):
        return tree[0], tree[1]

    def value_items(self, tree):
        return tree

    def DATE(self, tree):
        return {'date': str(tree)}

    def STRING(self, tree):
        return str(tree.value[1:-1])


class ConstraintParser:
    def __init__(self):
        self._visitor = ConstraintVisitor()
        self._parser = Lark(
            r'''
            constraints: constraint (";" constraint)* [";"]
            ?constraint : membership | inclusion | not_null | comparison | unique | increment | consec | dec | override | if_then
            membership : attribute "<-" attribute
                       | attribute "<-" value_range
                       | attribute "<-" value_items

            inclusion :  attribute "->" value_items
                       | attribute "->" value_range

            if_then:  value op value  "=>"  value op value

            not_null : attribute "!=" NULL
            comparison : value op value
            override: attribute "|" "int+" NULL
            unique : "unique" "(" [attribute ("," attribute)*] ")"
            increment: "inc" "(" [attribute ("," attribute)*] ")"
            dec: "dec" "(" [attribute ("," attribute)*] ")"
            consec: "consec" "(" [attribute ("," attribute)*] ")"
            ?value : attribute | NUMBER | DATE
            !op : ">" | "<" | "!=" | ">=" | "<=" | "^" | "="
            attribute : /[^\W\d]\w*/ "." /[^\W\d]\w*/

            value_range : "[" NUMBER "," NUMBER "]"
                        | "[" DATE "," DATE "]"
            value_items : "{" [value_item ("," value_item)*] "}"
            ?value_item : STRING | NUMBER

            NULL: "null" | "NULL"
            DATE: NUMBER "-" NUMBER "-" NUMBER
            STRING : "'" /[^']+/ "'" | ESCAPED_STRING

            %import common.ESCAPED_STRING
            %import common.SIGNED_NUMBER -> NUMBER
            %import common.WS
            %ignore WS
            ''',
            start='constraints')

    def parse(self, constraints):
        return self._visitor.transform(self._parser.parse(constraints))

    def parse_from_file(self, file) -> list:
        out = []
        with open(file, 'r') as reader:
            try:
                constraints = yaml.safe_load(reader)
                if not isinstance(constraints, dict):
                    return out
                for constraint in constraints.values():
                    try:
                        out.extend(self.parse(constraint))
                    except:
                        print(f"Unknown constraint {constraint} from {file}")
            except:
                print(SyntaxError(file))
        return out


if __name__ == '__main__':
    parser = ConstraintParser()

    # constraint = "Employees.manager_id <- Employees.employee_id; Employees.manager_id != NULL"
    # out = parser.parse(constraint)
    out = parser.parse_from_file('data/constraints/1789.yml')
    debug = Debug()
    debug.check(out)
