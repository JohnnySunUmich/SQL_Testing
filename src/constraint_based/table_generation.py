import random
from typing import List
from collections import OrderedDict
from faker import Faker
import typing
import datetime

from .utils.type_convertion import int2date, int2time
from .constraints.variables import vManager

class Table_Generator():
    def __init__(self, schema, config) -> None:
        self.schema = schema
        self.size = config['size']
        Faker.seed(config['seed'])
        random.seed(config['seed'])
        self.fake = Faker()


    def gen_database(self, z3_models: list) -> List[typing.OrderedDict]:
        # z3_models = [[{column_id: entry_value} for tuples] for tables]
        translated_z3_models = []
        for table_id, table in enumerate(z3_models):
            translated_z3_models.append([])
            for tuple_index, tuple in enumerate(table):
                tuple_value = {}
                for column_id in tuple:
                    variable = vManager.get_variable(table_id, tuple_index, column_id)
                    tuple_value[variable.column_name] = tuple[column_id]
                translated_z3_models[-1].append(tuple_value)
        print(translated_z3_models)
        database = []
        for table_schema, z3_model in zip(self.schema['Tables'], z3_models):
            database.append(
                self.gen_table(table_schema, z3_model))
        return database

    def gen_table(self, schema: dict, z3_model: List[dict]):
        table = OrderedDict()
        constraints = {}
        schema = self.__preprocess_table_schema(schema)
        print(schema)
        for tuple in z3_model:
            # transform constraints
            for col in tuple:
                constraints[col] = tuple[col]
            for col in constraints:
                if schema[col]['data_type'] == 'date':
                    constraints[col] = int2date(int(str(constraints[col])))
                elif schema[col]['date_type'] == 'time':
                    constraints[col] = int2time(int(str(constraints[col])))
                if col not in table:
                    table[col] = [constraints[col]]
                else:
                    table[col].append(constraints[col])
            # for col in schema:
            #     if col not in table:
            #         table[col] = self.random_gen_col(schema[col])
            return table

    def __preprocess_table_schema(self, schema: dict):
        """ Convert a table schema to something like
            {
                "col_name": {
                    "data_type": "string",
                    "pkey": "bool"
                }
            }
        """
        processed_schema = {}
        # process pkey:
        for pkey in schema['PKeys']:
            processed_schema[pkey['Name'].lower()] = {
                "data_type": pkey['Type'],
                "pkey": True
            }
        # process others
        for other in schema['Others']:
            processed_schema[other['Name'].lower()] = {
                "data_type": other['Type'],
                "pkey": False
            }
        return processed_schema

    def random_gen_col(self, col_schema: dict):
        if col_schema['pkey']:
            return self.random_gen(col_schema['data_type'], True)
        else:
            return self.random_gen(col_schema['data_type'], False)

    def random_gen(self, _type: str, unique: bool=False):
        if unique:
            if _type == 'int':
                return random.sample(list(range(self.size)), k=self.size)
            elif _type == 'varchar':
                return [self.fake.unique.name() for _ in range(self.size)]
            else:
                raise Exception(f'type {_type} is not supported currently')
        else:
            if _type == 'int':
                return random.choices(list(range(self.size)), k=self.size)
            elif _type == 'varchar':
                return [self.fake.name() for _ in range(self.size)]
            elif _type == 'date':
                lower = datetime.date(2000,1,1)
                upper = datetime.date(2022,12,30)
                return [self.fake.date_between(lower, upper) for _ in range(self.size)]
            elif _type.startswith('enum,'):
                enums = _type.split(',')[1:]
                return random.choices(enums, k=self.size)
            else:
                raise Exception(f'type {_type} is not supported currently')
