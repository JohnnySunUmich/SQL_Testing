import random
from typing import List
from collections import OrderedDict
from faker import Faker
import typing
import datetime

from .utils.type_convertion import int2time, int2date
from .constraints.variables import vManager


def gen_database(z3_models: dict) -> List[typing.OrderedDict]:
    # z3_models = [[{column_id: entry_value} for tuples] for tables]
    translated_z3_models = []
    database = []
    for table_id in z3_models:
        table = z3_models[table_id]
        translated_z3_models.append([])
        for tuple_index, tuple in enumerate(table):
            tuple_value = {}
            for column_id in tuple:
                variable = vManager.get_variable(table_id, tuple_index, column_id)
                if variable.type == "date":
                    tuple_value[variable.column_name] = int2date(int(str(tuple[column_id])))
                elif variable.type == "time":
                    tuple_value[variable.column_name] = int2time(int(str(tuple[column_id])))
                else:
                    tuple_value[variable.column_name] = tuple[column_id]

            translated_z3_models[-1].append(tuple_value)
    for table in translated_z3_models:
        database.append(OrderedDict())
        for tuple in table:
            for column in tuple:
                if column not in database[-1]:
                    database[-1][column] = [tuple[column]]
                else:
                    database[-1][column].append(tuple[column])
    return database
