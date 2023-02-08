import requests
import json, csv, os
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.etree import cElementTree as et
import logging
log_path = 'logs/mutants3.log'
logging.basicConfig(filename=log_path, encoding='utf-8', level=logging.INFO,\
    format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

def convert_type(_type: str):
    if 'enum' in _type:
        return 'varchar'
    elif _type == 'bool':
        return 'boolean'
    elif _type == 'numeric':
        return 'decimal'
    else:
        return _type

def schema_to_xml(Schema: dict, query: str):
    body = Element('body')
    sql = SubElement(body, 'sql')
    sql.text = query
    schema = SubElement(body, 'schema')
    for table_schema in Schema['Tables']:
        table = SubElement(schema, 'table')
        table.attrib['name'] = table_schema['TableName']
        pkeys = table_schema['PKeys']
        fkeys = table_schema['FKeys']
        others = table_schema['Others']
        for pkey in pkeys:
            _name = pkey['Name']
            _type = convert_type(pkey['Type'])
            table.append(et.Element('column', {
                'name': _name,
                'type': _type,
                'key': 'true'
            }))
        for fkey in fkeys:
            _name = fkey['FName']
            pname = fkey['PName']
            ptable_id = int(fkey['PTable'])
            _pkeys = Schema['Tables'][ptable_id]['PKeys']
            for pkey in _pkeys:
                if pkey['Name'] == pname:
                    _type = convert_type(pkey['Type'])
            table.append(et.Element('column', {
                'name': _name,
                'type': _type,
            }))
        for other in others:
            _name = other['Name']
            _type = convert_type(other['Type'])
            table.append(et.Element('column', {
                'name': _name,
                'type': _type
            }))
    options = SubElement(body, 'options')
    options.text = 'noequivalent'
    return tostring(body)

def query_mutants(schema: dict, query: str):
    API_ENDPOINT = "http://in2test.lsi.uniovi.es/sqlmutation/api/v2/mutants.xml"
    with open('../Schema/' + str(pid) + '.json') as f:
        schema = json.load(f)
    xml_input = schema_to_xml(schema, query)
    # sending post request and saving response as response object
    r = requests.post(url = API_ENDPOINT, data=xml_input)
    
    # extracting response text
    mutant_queries = []
    html_response = r.text
    try:
        tree = ET.ElementTree(ET.fromstring(html_response))
    except Exception as e:
        logging.info(f"fail to get api response as {e}")
        return []    
    root = tree.getroot()
    if len(root.findall('error')) != 0:
        error = root.findall('error')[0]
        logging.info(f'fail to get mutant as {error.text}')
    mutants = root[2]
    for mutant in mutants:
        is_equv = False
        for tag in mutant:
            if tag.tag == 'equivalent':
                is_equv = True
        if not is_equv: 
            mutant_queries.append(mutant[-1].text)
    return mutant_queries
    

pids = []
with open('problems3.txt') as f:
    for row in f:
        pids.append(row.strip())
    for pid in pids:
        if not os.path.exists('../mutants/' + pid):
            os.mkdir('../mutants/' + pid)
        queries = []
        with open(f'../mysql_queries/origin{pid}.csv') as f:
            reader = csv.reader(f)
            _ = next(reader)
            for row in reader:
                queries.append([row[0], row[1]])
        with open(f'../Schema/{pid}.json') as f:
            schema = json.load(f)
        for query in queries:
            qid = query[0]
            logging.info(f'problem {pid}, query {qid}')
            mutant_queries = query_mutants(schema, query[1])
            if len(mutant_queries) == 0:
                logging.info(f"no mutants for problem {pid}, query {qid}")
                continue
            with open(f'../mutants/{pid}/{qid}.csv', 'w') as f:
                writer = csv.writer(f)
                writer.writerow(['mutant_id', 'query'])
                writer.writerow(['-1', query[1]])
                for i, mutant in enumerate(mutant_queries):
                    writer.writerow([i, mutant])