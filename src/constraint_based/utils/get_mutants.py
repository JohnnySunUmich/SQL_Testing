from typing import List
import requests
import json

def convert_type(_type: str):
    if 'enum' in _type:
        return 'varchar'
    elif _type == 'bool':
        return 'boolean'
    elif _type == 'numeric':
        return 'decimal'
    else:
        return _type

def construct_request_dict(Schema: dict, query: str):
    request_data = {}
    request_data['sql'] = query
    request_data['schema'] = {}
    request_data['schema']['tables'] = []
    for table_schema in Schema['Tables']:
        table = {}
        table['name'] = table_schema['TableName'].lower()
        table['columns'] = []
        pkeys = table_schema['PKeys']
        fkeys = table_schema['FKeys']
        others = table_schema['Others']
        for pkey in pkeys:
            _name = pkey['Name']
            _type = convert_type(pkey['Type'])
            table['columns'].append({
                'name': _name,
                'datatype': _type,
                'key': 'true'
            })
        for fkey in fkeys:
            _name = fkey['FName'].lower()
            pname = fkey['PName'].lower()
            ptable_id = int(fkey['PTable'])
            _pkeys = Schema['Tables'][ptable_id]['PKeys']
            for pkey in _pkeys:
                if pkey['Name'] == pname:
                    _type = convert_type(pkey['Type'])
            table['columns'].append({
                'name': _name,
                'datatype': _type,
                'fk': 'true',
                'fkname': pname,
            })
        for other in others:
            _name = other['Name']
            _type = convert_type(other['Type'])
            table['columns'].append({
                'name': _name,
                'datatype': _type
            })
        for i, col in enumerate(table['columns']):
            if col['datatype'] == 'varchar':
                table['columns'][i]['size'] = '30'
        request_data['schema']['tables'].append(table) 
    request_data['options'] = 'noequivalent'
    return request_data

def extract_mutants(response_dict: dict) -> List[str]:
    response_list = response_dict['rules']
    mutants = []
    for wrapper in response_list:
        mutants.append(wrapper['sql'])
    return mutants

def query_mutants(schema: dict, query: str):
    API_ENDPOINT = "https://in2test.lsi.uniovi.es/sqlrules/api/v3/mutants"
    request_dict = construct_request_dict(schema, query)
    request_data = json.dumps(request_dict)
    headers = {'content-type': 'application/json', 'accept': 'application/json'}
    # sending post request and saving response as response object
    r = requests.post(url = API_ENDPOINT, data=request_data, headers=headers)
    # extracting response text
    mutant_queries = []
    html_response = r.text
    response_dict = json.loads(html_response)
    mutant_queries = extract_mutants(response_dict)
    return mutant_queries