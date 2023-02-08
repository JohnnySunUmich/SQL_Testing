import itertools
import logging
from faker import Faker
from collections import defaultdict
from util import topo_sort_cols
from testing_parser import Parser
import random
import math
import datetime

class Constrained_Random_Table_Generation():
    def __init__(self, schema: dict, sizes, raw_cstr: dict={}, seed=2333) -> None:
        # init random_dep seeds
        random.seed(seed)
        self.fake = Faker()
        Faker.seed(seed)

        # init parser
        self.parser = Parser(schema, raw_cstr)
        self.id2col, self.col2id = self.parser.gen_col_dicts(sizes)
        self.cstr_d = self.parser.parse_constraints()
        for i in range(len(self.id2col)):
            if i not in self.cstr_d.keys():
                self.cstr_d[i] = {}

        # init tables
        self.tables = []
        self.columns = [[] for _ in range(len(self.col2id))]
        self.col_order = topo_sort_cols(len(self.col2id), self.cstr_d)

        # construct table translation
        self.tab2id = {}
        tableId = 0
        for table in schema['Tables']:
            self.tab2id[table['TableName'].lower()] = tableId
            self.tables.append(defaultdict(list))
            tableId += 1
        
        # construct col-tab translation
        self.colId2tabId = {}
        for col_id in self.id2col.keys():
            self.colId2tabId[col_id] \
                = self.tab2id[self.id2col[col_id]['table_name']]

        # init generators
        self.generators = {}


    def generate(self):
        # generate col by col
        for col_id in self.col_order:
            if self.columns[col_id] == []:
                # not yet generated
                if col_id in self.cstr_d.keys():
                    to_remove = []
                    parent_cols = {}
                    for i, col_cstr in enumerate(self.cstr_d[col_id]):
                        parent_col_id = col_cstr['parent_col_id']
                        if parent_col_id != -1:
                            parent_cols[parent_col_id] = self.columns[parent_col_id]
                            if self.columns[parent_col_id] == []:
                                if col_cstr['operator'] in ['<', '>', '=', '!=']:
                                    to_remove.append(i)
                                else:
                                    logging.info(f"Fail to generate due to bad dependency.")
                                    raise Exception
                    to_remove.sort()
                    count_rm = 0
                    for trm in to_remove:
                        self.cstr_d[col_id].pop(trm-count_rm)
                        count_rm += 1
                    # print(f"generating col {self.id2col[col_id]} with constraints\
                        # {self.cstr_d[col_id]}")
                    self.generate_col(col_id, self.cstr_d[col_id])
                else:
                    # print(f"generating col {self.id2col[col_id]}")
                    self.generate_col(col_id)
            else:
                logging.info("Warning: column {col_id} already generated")
        # solve join relationship
        if 'join' in self.cstr_d.keys():
            for join_pairs in self.cstr_d['join']:
                # print(f"resolving join relationship between {self.id2col[join_pairs[0]]} \nand {self.id2col[join_pairs[1]]}")
                col1, col2 = join_pairs[0], join_pairs[1]
                gen1, gen2 = self.generators[col1], self.generators[col2]
                size1, size2 = self.id2col[col1]['size'], self.id2col[col2]['size']
                replace = []
                replace_num = random.choice(len(1,min(size1, size2)))
                while replace_num > 0:
                    values1 = set(gen1(size1))
                    values2 = set(gen2(size2))
                    intersec =  list(values1.intersection(values2))
                    if len(intersec) > replace_num:
                        replace += intersec[:replace_num]
                    else:
                        replace += intersec
                    replace_num -= len(intersec)
                for i in range(len(replace)):
                    self.columns[col1][i] = replace[i]
                    self.columns[col2][i] = replace[i]
                    random.shuffle(self.columns[col1])
                    random.shuffle(self.columns[col2])

        # reformat columns to tables
        for col_id, col in enumerate(self.columns):
            col_name = self.id2col[col_id]['column_name']
            table_id = self.colId2tabId[col_id]
            self.tables[table_id][col_name] = col

        return self.tables

    def row_dep_generator(self, _type, size, operator):
        if operator == 'inc':
            # only support int for inc operator
            if _type == 'int':
                return list(range(1,size+1))
            else:
                logging.info(f"not support type {_type} for inc operator")
                raise Exception
        elif operator == 'consec':
            # only support int for consec operator
            if _type == 'int':
                output = [0]
                for _ in range(size-1):
                    decision = random.uniform(0,1)
                    if decision > 0.5:
                        output.append(output[-1] + 1)
                    else:
                        output.append(output[-1])
                return output
            else:
                logging.info(f"not support type {_type} for consec operator")
                raise Exception
        elif operator == 'bound':
            if _type == 'int':
                return random.sample(list(range(1, size+1)), k=size)
            else:
                # print(f"not support type {_type} for consec operator")
                logging.info(f"not support type {_type} for consec operator")
                raise Exception
        else:
            # print(f"not support row dep {operator}")
            logging.info(f"not support row dep {operator}")
            raise Exception

    def check_value(self, _type, operator, value, reference):
        # convert type if string
        if isinstance(value, str):
            value = self.typing_string(_type, value)
        if isinstance(reference, str):
            reference = self.typing_string(_type, reference)
        if operator == '>':
            if value >= reference:
                return True
            else:
                return False
        elif operator == '<':
            if value <= reference:
                return True
            else:
                return False
        elif operator == '!=':
            if value != reference:
                return True
            else:
                return False
        elif operator == '=':
            if value == reference:
                return True
            else:
                logging.info(f"Not support operator {operator}")
                return False
        else:
            raise ValueError

    def check_col_val_cstr(self, _type, cstr, val):
        if cstr['operator'] == '=':
            ref = cstr['info']['value']
            val = str(val)
            if val == ref:
                return True
            else:
                return False
        elif cstr['operator'] == '!=':
            val = str(val)
            ref = cstr['info']['value']
            if val != ref:
                return True
            else:
                return False
        if isinstance(val, str):
            val = self.typing_string(_type, val)
        if cstr['operator'] == 'range':
            lower, upper = cstr['info']['lower'], cstr['info']['upper']
            lower, upper = self.get_bound(_type, lower, upper)
            if val >= lower and val <= upper:
                return True
            else:
                return False
        else:
            logging.info(f"not support {cstr} in checking col val constraints")
    
    def unique_gen(self, types, sizes, cols_cstr: list=[]):
        # types and sizes must have the same length
        assert(len(types) == len(sizes))
        # so is cstr
        assert(len(types) == len(cols_cstr))
        # no more that two cols
        assert(len(types) <= 2)
        if len(types) == 2:
            # sizes must be consistent
            assert(sizes[1] == sizes[0])
        # calculate random_dep generation size
        gen_sizes = []
        max_lens = [self.get_max_len(t, c) for t, c in zip(types, cols_cstr)]
        if math.prod(max_lens) < sizes[0]:
            logging.info("fail to generate unique relationship because of length is not enough given type and constraints")
            raise Exception
        max_prod = math.prod(max_lens)
        prod = min(random.choice(range(sizes[0], max_prod+1)), 2*sizes[0])
        if len(types) == 1:
            gen_sizes.append(prod)
        else:
            # two cols, two sizes
            size1 = min(random.choice(range(math.ceil(prod / max_lens[1]), max_lens[0])), sizes[0]*2)
            size2 = math.ceil(prod / size1)
            gen_sizes = [size1, size2]
        # generate col by col
        output = []
        for i in range(len(types)):
            if len(cols_cstr[i]) == 0:
                output.append(self.unique_gen_helper(types[i], gen_sizes[i]))
            else:
                # support range, subset, superset, exclusion, inc, consec
                if cols_cstr[i]['operator'] == 'range':
                    if cols_cstr[i]['info']['discrete']:
                        output.append(self.unique_gen_helper(
                            types[i], gen_sizes[i], 
                            subset = cols_cstr[i]['info']['set']
                        ))
                    else:
                        output.append(self.unique_gen_helper(
                            types[i], gen_sizes[i],
                            _range=[
                                cols_cstr[i]['info']['lower'],
                                cols_cstr[i]['info']['upper']
                            ]
                        ))
                elif cols_cstr[i]['operator'] == 'subset':
                    output.append(self.unique_gen_helper(
                        types[i], gen_sizes[i],
                        subset=self.columns[cols_cstr[i]['parent_col_id']]
                    ))
                elif cols_cstr[i]['operator'] == 'superset':
                    output.append(self.unique_gen_helper(
                        types[i], gen_sizes[i],
                        superset=cols_cstr[i]['info']['set']
                    ))
                elif cols_cstr[i]['operator'] == '!=':
                    output.append(self.unique_gen_helper(
                        types[i], gen_sizes[i],
                        exclusion=cols_cstr[i]['info']['value']
                    ))
                elif cols_cstr[i]['operator'] == 'inc':
                    output.append(self.unique_gen_helper(
                        types[i], gen_sizes[i],
                        is_inc=True
                    ))
                elif cols_cstr[i]['operator'] == 'consec':
                    output.append(self.unique_gen_helper(
                        types[i], gen_sizes[i],
                        is_consec=True
                    ))
                else:
                    # print(f"Not support operator {cols_cstr[i]['operator']}\
                        # in unique generation yet.")
                    logging.info(f"Not support operator {cols_cstr[i]['operator']}\
                        in unique generation yet.")
                    raise Exception
        if len(output) == 2:
            cart_prod = list(itertools.product(output[0], output[1]))
            output = random.sample(cart_prod, k=sizes[0])
            output = list(zip(*output))
        else:
            output[0] = output[0][:sizes[0]]
        return output

    def unique_gen_helper(self, _type, size, _range: list=[], is_inc: bool=False, \
        is_consec: bool=False, superset: list=[], subset: list=[], exclusion: list=[]):
        output = []
        # special cases: is_inc, is_consec, subset
        if is_inc:
            return self.row_dep_generator(_type, size, 'inc')
        elif is_consec:
            return self.row_dep_generator(_type, size, 'consec')
        elif len(subset) != 0:
            assert(len(subset) >= size)
            return random.sample(subset, k=size)
        # general cases: range
        lower, upper = self.get_bound(_type, _range)
        # generate
        gen_functor = self.type2values(_type, lower, upper, True)
        output = gen_functor(size)
        # post generation check
        if len(superset) != 0:
            for i, spst in enumerate(superset):
                if spst not in output:
                    output[i] = spst
            random.shuffle(output)
        elif len(exclusion) != 0:
            for exclu in exclusion:
                idxs = [i for i, val in enumerate(output) if val == exclu]
                for idx in idxs:
                    success = False
                    for i in range(10000):
                        new_val = gen_functor(1)[0]
                        if new_val not in output:
                            output[idx] = new_val
                            success = True
                            break
                    if not success:
                        logging.info(f"fail to exclude value {exclu} after 10000 trials")
        self.fake.unique.clear()
        return output
                        
    def typing_string(self, _type: str, string: str):
        if _type == 'int':
            return int(string)
        elif _type == 'date':
            return datetime.datetime.strptime(string, "%Y-%m-%d")
        elif _type == 'time':
            return datetime.datetime.strptime(string, "%Y-%m-%d-%H-%M-%S")
        elif _type == 'numeric':
            return float(string)
        return None

    def get_bound(self, _type, _range:list=[]):
        lower, upper = None, None
        if _type == 'int':
            lower = 0
            upper = 2147483647
        elif _type == 'date':
            lower = datetime.date(1,1,1)
            upper = datetime.date(9999,12,30)
        elif _type == 'time':
            lower = datetime.datetime(1,1,1,0,0,0)
            upper = datetime.datetime(9999,12,31,23,59,59)
        elif _type == 'numeric':
            lower = 0.0
            upper = 2147483647.0
        if len(_range) != 0:
            lower = self.typing_string(_type, _range[0]) if _range[0] is not None else lower
            upper = self.typing_string(_type, _range[1]) if _range[1] is not None else upper
        return lower, upper
    
    def type2values(self, _type, lower, upper, unique):
        if _type == 'int':
            if unique:
                return lambda k: random.sample(range(lower, upper+1), k)
            else:
                return lambda k: random.choices(range(lower, upper+1), k=k)
        elif _type == 'date':
            if unique:
                return lambda k: [self.fake.unique.date_between(lower, upper) for _ in range(k)]
            else:
                return lambda k: [self.fake.date_between(lower, upper) for _ in range(k)]
        elif _type == 'time':
            if unique:
                return lambda k: [self.fake.unique.date_time_between(lower, upper) for _ in range(k)]
            else:
                return lambda k: [self.fake.date_time_between(lower, upper) for _ in range(k)]
        elif _type == 'varchar':
            if unique:
                return lambda k: [self.fake.unique.name() for _ in range(k)]
            else:
                return lambda k: [self.fake.unique.name() for _ in range(k)]
        elif _type == 'numeric':
            assert(not unique)
            return lambda k: [random.uniform(lower, upper) for _ in range(k)]
        elif _type[0:4] == 'enum':
            enums = _type.split(',')[1:]
            if unique:
                return lambda k: random.sample(enums, k)
            else:
                return lambda k: random.choices(enums, k=k)
        elif _type == 'null':
            return lambda k: ['null'] * k
        elif _type == 'bool':
            return lambda k: random.choices([True, False], k=k)
        else:
            # print(f"type {_type} not support yet")
            logging.info(f"type {_type} not support yet")
            raise Exception

    def get_col_generator(self, _type: list=[], _range: list=[], subset: list=[]):
        if _range != [] and subset != [] and len(_type) == 1:
            _range = _range[0]
            subset = subset[0]
            def generator(k):
                output = []
                lower, upper = self.get_bound(_type[0], _range)
                subset_generator = lambda k: random.choices(subset, k=k)
                for _ in range(k):
                    val = subset_generator(1)[0]
                    while val < lower or val > upper:
                        val = subset_generator
                    output.append(val)
                return output
            return generator
        elif subset != [] and len(_type) == 1:
            subset = subset[0]
            return lambda k: random.choices(subset, k=k)
        elif _range != [] and len(_type) == 1:
            _range = _range[0]
            lower, upper = self.get_bound(_type[0], _range)
            return self.type2values(_type[0], lower, upper, unique=False)
        elif len(_type) == 2 and _range == [] and subset == []:
            def gen_type_override(k):
                output = []
                lower1, upper1 = self.get_bound(_type[0], [None, None])
                lower2, upper2 = self.get_bound(_type[1], [None, None])
                generator1 = self.type2values(_type[0], lower1, upper1, unique=False)
                generator2 = self.type2values(_type[1], lower2, upper2, unique=False)
                for _ in range(k):
                    if random.uniform(0,1) < 0.5:
                        output += generator1(1)
                    else:
                        output += generator2(1)
                return output
            return gen_type_override
        elif len(_type) == 2 and subset == []:
            def generator(k):
                output = []
                lower1, upper1 = self.get_bound(_type[0], _range[0])
                lower2, upper2 = self.get_bound(_type[1], _range[1])
                generator1 = self.type2values(_type[0], lower1, upper1, unique=False)
                generator2 = self.type2values(_type[1], lower2, upper2, unique=False)
                for _ in range(k):
                    if random.uniform(0,1) < 0.5:
                        output += generator1(1)
                    else:
                        output += generator2(1)
                return output
            return generator
        elif len(_type) == 2 and _range == [] and subset != []:
            def generator(k):
                output = []
                if len(subset) == 1:
                    generator1 = lambda k: random.choices(subset[0], k=k)
                    generator2 = self.type2values(_type[1], None, None, unique=False)
                else:
                    generator1 = lambda k: random.choices(subset[0], k=k)
                    generator2 = lambda k: random.choices(subset[1], k=k)
                for _ in range(k):
                    if random.uniform(0,1) < 0.5:
                        output += generator1(1)
                    else:
                        output += generator2(1)
                return output
            return generator

        else:
            lower, upper = self.get_bound(_type[0])
            return self.type2values(_type[0], lower, upper, unique=False)
            

    def get_max_len(self, _type:str, cstr:dict={}):
        max_len = 0
        if _type == 'int':
            max_len = 2147483647
        elif _type == 'date':
            max_len = 3649635
        elif _type == 'bool':
            max_len = 2
        elif _type[:4] == 'enum':
            max_len = _type.count(',')
        else:
            max_len = 2147483647
        if len(cstr) != 0:
            # only support estimate max len for subset or range
            if cstr['operator'] == 'range':
                if cstr['info']['discrete']:
                    max_len = len(cstr['info']['set'])
                else:
                    if _type == 'int':
                        upper = int(cstr['info']['upper']) if cstr['info']['upper'] is not None else 2147483647
                        lower = int(cstr['info']['lower']) if cstr['info']['lower'] is not None else 0
                        max_len = upper - lower + 1
                    elif _type == 'date':
                        upper = cstr['info']['upper'] if cstr['info']['upper'] is not None else '9999-12-31'
                        lower = cstr['info']['lower'] if cstr['info']['lower'] is not None else '1-1-1'
                        upper_date = datetime.datetime.strptime(cstr['info']['upper'], "%Y-%m-%d")
                        lower_date = datetime.datetime.strptime(cstr['info']['lower'], "%Y-%m-%d")
                        diff = upper_date.date() - lower_date.date()
                        max_len = int(diff.days) + 1
            elif cstr['operator'] == 'subset':
                max_len = len(self.columns[cstr['parent_col_id']])
        return max_len

    def generate_col(self, col_id, col_cstr: list=[]):
        _type = [self.id2col[col_id]['type']]
        size = self.id2col[col_id]['size']
        if col_cstr == []:
            is_unique = False
            if 'unique' in self.cstr_d.keys():
                for unique_cols in self.cstr_d['unique']:
                    if col_id in unique_cols:
                        types = [self.id2col[i]['type'] for i in unique_cols]
                        sizes = [self.id2col[i]['size'] for i in unique_cols]
                        cstrs = [self.cstr_d[i] for i in unique_cols]
                        output = self.unique_gen(types, sizes, cstrs)
                        for i, col in enumerate(unique_cols):
                            self.columns[col] = output[i]
                        is_unique = True
            if not is_unique:
                generator = self.get_col_generator(_type)
                self.columns[col_id] = generator(size)
                self.generators[col_id] = generator
                return
        else:
            is_unique = False
            if 'unique' in self.cstr_d.keys():
                for unique_cols in self.cstr_d['unique']:
                    if col_id in unique_cols:
                        types = [self.id2col[i]['type'] for i in unique_cols]
                        sizes = [self.id2col[i]['size'] for i in unique_cols]
                        is_unique = True
                        break
            if is_unique:
                cols_cstr = []
                for col_id in unique_cols:
                    # only support no more than one constraint for unique cols
                    assert(len(self.cstr_d[col_id]) <= 1)
                    if self.cstr_d[col_id] != {}:
                        # support subset <-, superset ->, !=, inc, consec
                        cols_cstr.append(self.cstr_d[col_id][0])
                    else:
                        cols_cstr.append({})
                output = self.unique_gen(types, sizes, cols_cstr=cols_cstr)
                for i, col_id in enumerate(unique_cols):
                    self.columns[col_id] = output[i]
            else:
                # special cases: row dep
                _type = [self.id2col[col_id]['type']]
                size = self.id2col[col_id]['size']
                for cstr in col_cstr:
                    if cstr['operator'] in ['inc', 'consec', 'bound']:
                        if len(col_cstr) > 1:
                            logging.info(f"not support row dep with other constraints")
                            raise Exception
                        self.columns[col_id] = self.row_dep_generator(_type[0], size, cstr['operator'])
                        return
                # general cases: no row dep
                to_solve_cstr = []
                # get column generator to 
                # satisfy subset, range, and type override constraints
                types, subset, ranges = [], [], []
                for i, cstr in enumerate(col_cstr):
                    if cstr['operator'] == 'subset':
                        subset.append(self.columns[cstr['parent_col_id']])
                    elif cstr['operator'] == 'range':
                        ranges.append([cstr['info']['lower'], cstr['info']['upper']])
                    elif cstr['operator'] == '|':
                        types = cstr['info']['types']
                    else:
                        to_solve_cstr.append(cstr)
                _type = types if types != [] else _type
                generator = self.get_col_generator(_type, ranges, subset)
                self.generators[col_id] = generator
                # row by row / batch generation using generator to
                # satisfy col dep (<,>,=,!=,=>)
                if len(to_solve_cstr) == 0:
                    self.columns[col_id] = generator(size)
                elif len(to_solve_cstr) == 1:
                    cstr = to_solve_cstr[0]
                    parent_col = self.columns[cstr['parent_col_id']]
                    if cstr['operator'] in ['>', '<', '=', '!=']:
                        output = []
                        for i in range(size):
                            val = generator(1)[0]
                            ref = parent_col[i]
                            while not self.check_value(_type, cstr['operator'], val, ref):
                                val = generator(1)[0]
                            output.append(val)
                        self.columns[col_id] = output

                    elif cstr['operator'] == '=>':
                        output = []
                        for i in range(size):
                            val = generator(1)[0]
                            ref = parent_col[i]
                            l_cstr = cstr['info']['if']
                            r_cstr = cstr['info']['then']
                            if self.check_col_val_cstr(_type, l_cstr, ref):
                                while not self.check_col_val_cstr(_type, r_cstr, val):
                                    val = generator(1)[0]
                            output.append(val)
                        self.columns[col_id] = output
                    elif cstr['operator'] == 'superset':
                        output = generator(size)
                        selected = random.sample(list(range(len(output))), k=len(cstr['info']['set']))
                        for s, new_val in zip(selected, cstr['info']['set']):
                            output[s] = new_val
                        self.columns[col_id] = output
                else:
                    # print("not support solve 2 constraints")
                    raise Exception
                # TODO: try to row by row repair generated columns to 
                # satisfy inclusion constraints if any


                # TODO: check all the solved constraints to
                # see if they are still satisfied