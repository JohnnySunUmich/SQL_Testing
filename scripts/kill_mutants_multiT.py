import sys
sys.path.append('..')
from mysql_util import create_database, drop_database
import multiprocessing as mp
import logging, os
import json, csv, yaml
from tester import Tester

log_path = '../logs/kill_mutants.log'
logging.basicConfig(filename=log_path, encoding='utf-8', level=logging.INFO,\
    format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

def init_worker():
    global worker_id
    worker_id = int(mp.current_process().name.split('-')[1]) - 1

def do_task(tasks):
    test_one_problem(f"run{worker_id}", tasks)

def test_one_problem(dbname, mutation_fn: str):
    pid, qid = mutation_fn.split('.')[0].split('_')
    with open('../config.yml') as f:
        config = yaml.safe_load(f)
    host = config['tester']['mysql']['host']
    username = config['tester']['mysql']['username']
    create_database(host, username, dbname)
    with open('../Schema/' + pid + '.json') as f:
        schema = json.load(f)
    if os.path.exists('../constraints/' + pid + '.yml'):
        with open('../constraints/' + pid + '.yml') as f:
            cstr = yaml.safe_load(f)
    else:
        cstr = {}
    queries = []
    with open(f'../data/search_output/mutants/{mutation_fn}') as f:
        reader = csv.reader(f)
        _ = next(reader)
        for row in reader:
            queries.append(row[1])
    config['problem'] = int(pid)
    config['tester']['mysql']['dbname'] = dbname
    tester = Tester(schema, config['tester'], cstr, engin='mysql')
    reference = queries[0]
    mutants = queries[1:]
    tester.database_buffer = []
    outputs = tester.kill_mutants(reference, mutants, False, 'timeout')
    logging.info(outputs)
    tester.save_database_buffer(f'mutation_databases/{pid}_{qid}')
    drop_database(host, username, dbname)


if __name__ == '__main__':
    num_processes = int(sys.argv[1])
    tasks = []
    with open('tasks.txt') as f:
        for row in f:
            tasks.append(row.strip())
    
    with mp.Pool(processes=num_processes, initializer=init_worker) as pool:
        pool.map(do_task, tasks, chunksize=1)
    