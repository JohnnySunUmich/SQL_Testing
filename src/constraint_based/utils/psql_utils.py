from venv import create
import psycopg2 as psycopg
import os
from collections import OrderedDict
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database(username, dbname, password):
    drop_database(username, dbname, password)
    conn = psycopg.connect(f"dbname=postgres user={username} password={password}")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute('CREATE DATABASE ' + dbname)
    cur.close()
    conn.close()

def drop_database(username, dbname, password):
    conn = psycopg.connect(f"dbname=postgres user={username} password={password}")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute('DROP DATABASE IF EXISTS ' + dbname + ';')
    cur.close()
    conn.close()

def type_string(column, enums: list):
    """
    check size of varchar and add enum type
    """
    types = column["Type"].split(",")
    data_type = types[0]
    extra_info = ""
    if data_type == "varchar" and len(types) > 1 and types[1] == "size":
        assert(column["Size"])
        extra_info = f'({column["Size"]})'
    elif data_type == "enum":
        this_enum = set(types[1:])
        try:
            index = enums.index(this_enum)
        except:
            index = len(enums)
            enums.append(this_enum)
        data_type = f'enum{index}'
    return data_type + extra_info

def gen_create_drop_statement(schema):
    """
    generate CREATE/DROP TABLE statements
    """
    table_schemas = schema["Tables"]
    create_tables = []
    drop_tables = []
    enums = []
    for table_schema in table_schemas:
        create_table = ["CREATE TABLE IF NOT EXISTS ", table_schema["TableName"], " ("]
        fields = []
        primary_key_names = set()
        for pkey in table_schema["PKeys"]:
            fields.append(f'{pkey["Name"]} {type_string(pkey, enums)}')
            primary_key_names.add(pkey["Name"])
        for fkey in table_schema["FKeys"]:
            if fkey["FName"] in primary_key_names: 
                # foreign key is also a primary key
                continue
            ptable_keys = table_schemas[int(fkey["PTable"])]["PKeys"]
            pkey = next(key for key in ptable_keys if key["Name"] == fkey["PName"])
            fields.append(f'{fkey["FName"]} {type_string(pkey, enums)}')
        for col in table_schema["Others"]:
            fields.append(f'{col["Name"]} {type_string(col, enums)}')
        create_table.extend([", ".join(fields), ");"])
        create_tables.append("".join(create_table))
        drop_tables.append(f'DROP TABLE IF EXISTS {table_schema["TableName"]};')
    create_types = []
    drop_types = []
    for i, enum in enumerate(enums):
        enum_string = ", ".join([f"'{item}'" for item in enum])
        create_types.append(f'CREATE TYPE enum{i} AS ENUM ({enum_string});')
        drop_types.append(f'DROP TYPE enum{i};')
    create_statement = "\n".join(create_types + create_tables)
    drop_statement = "\n".join(drop_tables + drop_types)
    return create_statement, drop_statement

def value_string(value):
    if value == None or value == "":
        return "null"
    elif type(value) == int or type(value) == float:
        return str(value)
    elif type(value) == str:
        if value[0] == '"' and value[-1] == '"':
            print(value)
            return value[1:-1]
        return f"'{value}'"
    else:
        value = str(value)
        if value[0] == '"' and value[-1] == '"':
            return f"'{value[1:-1]}'"
        return f"'{value}'"

def gen_insert_statement(schema, database: list):
    """
    generate INSERT INTO statements
    """
    table_schemas = schema["Tables"]
    insert_statements = []
    for table_schema, table in zip(table_schemas, database):
        if len(table) == 0:
            continue
        insert_statement = ["INSERT INTO ", table_schema["TableName"], "\nVALUES\n"]
        columns = []
        for pkey in table_schema["PKeys"]:
            columns.append(pkey["Name"])
        for fkey in table_schema["FKeys"]:
            if fkey["FName"] in columns: 
                # foreign key is also a primary key
                continue
            columns.append(fkey["FName"])
        for col in table_schema["Others"]:
            columns.append(col["Name"])
        values = []
        num_row = len(table[columns[0].lower()])
        for i in range(num_row):
            value = [value_string(table[column.lower()][i]) for column in columns]
            values.append(f'({",".join(value)})')
        insert_statement.extend([",\n".join(values), ";"])
        insert_statements.append("".join(insert_statement))
    return "\n".join(insert_statements)

def run_psql(query: str, database: OrderedDict, schema: dict, dbname: str, username: str, password: str):
    """
    run query on database and return the output
    query can be a list of queries or a single string typed query
    """
    create_database(username=username, dbname=dbname, password=password)
    create_statement, drop_statement = gen_create_drop_statement(schema)
    insert_statement = gen_insert_statement(schema, database)
    commands = "\n".join([create_statement, insert_statement])
    # print(commands)
    # with psycopg.connect(f"dbname={dbname} user={username} password={password}")\
    #     as conn:
    #     with conn.cursor() as cur:
    #         cur.execute(commands)
    #         cur.execute(query)
    #         result = cur.fetchall()
    #         cur.execute(drop_statement)
    conn = psycopg.connect(f"dbname={dbname} user={username} password={password}")
    cur = conn.cursor()
    cur.execute(commands)
    cur.execute(query)
    result = cur.fetchall()
    cur.execute(drop_statement)
    cur.close()
    conn.close()
    drop_database(username=username, dbname=dbname, password=password)
    # print(result)
    return result

def explain_psql(query, database: OrderedDict, schema, conf):
    """
    EXPLAIN ANALYSE query
    return the cost and execution time
    """
    dbname = conf['dbname']
    username = conf['username']
    create_statement, drop_statement = gen_create_drop_statement(schema)
    insert_statement = gen_insert_statement(schema, database)
    commands = "\n".join([create_statement, insert_statement])
    # os.system('./'+conf["clearcache_path"])
    with psycopg.connect(f"dbname={dbname} user={username}", autocommit=False)\
        as conn:
        with conn.cursor() as cur:
            cur.execute(commands)
            if type(query) != str:
                raise ValueError(
                    "query argument must be string"
                )
            timeout = "SET statement_timeout = " + str(conf["timeout"]) + ";"
            cur.execute(timeout)
            cur.execute("EXPLAIN ANALYZE " + query)
            result = cur.fetchall()
            
            # extract cost from output
            cost = result[0][0]
            pos = cost.find('.') + 5
            cost = cost[pos:-1]
            pos = cost.find(' ')
            cost = cost[0:pos]
            cost = float(cost)

            # extract runtime from output
            time = float(result[-1][0][16:-3])

            result = [cost, time]
            
            cur.execute(drop_statement)
    return result