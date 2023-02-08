from mysql.connector import connect
from collections import OrderedDict
import logging

def create_database(host, username, dbname):
    drop_database(host, username, dbname)
    with connect(host=host, user=username) as conn:
        with conn.cursor() as cursor:
            cursor.execute("CREATE DATABASE " + dbname)

def drop_database(host, username, dbname):
    with connect(host=host, user=username) as conn:
        with conn.cursor() as cursor:
            cursor.execute("DROP DATABASE IF EXISTS " + dbname)

def type_string(column):
    """
    check size of varchar and add enum type
    """
    types = column["Type"].split(",")
    data_type = types[0]
    extra_info = ""
    if data_type == "varchar":
        extra_info = f'(100)'
    elif data_type == "enum":
        types.pop(0)
        types = ['\'' + t + '\'' for t in types]
        extra_info = '(' + ",".join(types) + ')'
    return data_type + extra_info

def gen_create_drop_statement(schema):
    """
    generate CREATE/DROP TABLE statements
    """
    table_schemas = schema["Tables"]
    create_tables = []
    drop_tables = []
    for table_schema in table_schemas:
        create_table = ["CREATE TABLE IF NOT EXISTS ", table_schema["TableName"], " ("]
        fields = []
        primary_key_names = set()
        for pkey in table_schema["PKeys"]:
            fields.append(f'{pkey["Name"]} {type_string(pkey)}')
            primary_key_names.add(pkey["Name"])
        for fkey in table_schema["FKeys"]:
            if fkey["FName"] in primary_key_names: 
                # foreign key is also a primary key
                continue
            ptable_keys = table_schemas[int(fkey["PTable"])]["PKeys"]
            pkey = next(key for key in ptable_keys if key["Name"] == fkey["PName"])
            fields.append(f'{fkey["FName"]} {type_string(pkey)}')
        for col in table_schema["Others"]:
            fields.append(f'{col["Name"]} {type_string(col)}')
        create_table.extend([", ".join(fields), ");"])
        create_tables.append("".join(create_table))
        drop_tables.append(f'DROP TABLE IF EXISTS {table_schema["TableName"]};')
    return create_tables, drop_tables

def value_string(value):
    if value == None:
        return "null"
    elif type(value) == int or type(value) == float:
        return str(value)
    else:
        return f"'{str(value)}'"

def gen_insert_statement(schema, database: list):
    """
    generate INSERT INTO statements
    """
    table_schemas = schema["Tables"]
    insert_statements = []
    for table_schema, table in zip(table_schemas, database):
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
        num_row = len(table[columns[0]])
        for i in range(num_row):
            value = [value_string(table[column][i]) for column in columns]
            
            values.append(f'({",".join(value)})')
        insert_statement.extend([",\n".join(values), ";"])
        insert_statements.append("".join(insert_statement))
    return "\n".join(insert_statements)

def run_mysql(query, database: OrderedDict, schema, conf):
    """
    run query on database and return the output
    query can be a list of queries or a single string typed query
    """
    host = conf['host']
    username = conf['username']
    dbname = conf['dbname']
    create_statement, drop_statement = gen_create_drop_statement(schema)
    insert_statement = [gen_insert_statement(schema, database)]
    commands = "\n".join(create_statement + insert_statement)
    with connect(host=host, user=username, database=dbname) as conn:
        with conn.cursor() as cursor:
            commands = commands.split(';')[:-1]
            for command in commands:
                cursor.execute(command)
                conn.commit()
            if type(query) == list:
                result = []
                for q in query:
                    if type(q) != str:
                        raise ValueError(
                            "query argument must be string or list or strings"
                        )
                    cursor.execute(q)
                    try:
                        result.append(cursor.fetchall())
                    except Exception as e:
                        logging.info(f"fail to fetch due to {e}")
                        logging.info(f"create statement\n {create_statement}")
                        logging.info(f"insert statement\n {insert_statement}")
                        logging.info(f"query\n {q}")
            else:
                if type(query) != str:
                    raise ValueError(
                        "query argument must be string or list or strings"
                    )
                cursor.execute(query)
                try:
                    result = cursor.fetchall()
                except Exception as e:
                    logging.info(f"fail to fetch due to {e}")
                    logging.info(f"create statement\n {create_statement}")
                    logging.info(f"insert statement\n {insert_statement}")
                    logging.info(f"query\n {query}")
            for command in drop_statement:
                cursor.execute(command)
            conn.commit()
    return result