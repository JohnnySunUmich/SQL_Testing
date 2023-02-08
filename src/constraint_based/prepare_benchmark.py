from argparse import MetavarTypeHelpFormatter
from collections import defaultdict
import csv, json, yaml
import os
from utils.get_mutants import query_mutants

class Benchmark():
    # key attributes:
    # self.queries = [[qid, query_text], ...]

    def __init__(self, pid: int, data_dir: str='../../data', queries_dir: str='first_batch_queries') -> None:
        self.pid = pid
        # load schema
        with open(f'{data_dir}/Schema/{pid}.json') as f:
            self.schema = json.load(f)
        # load queries
        self.queries = [] # [qid, query_text]
        with open(f'{queries_dir}/{pid}.csv') as f:
            reader = csv.reader(f)
            _ = next(reader)
            self.ground_truth = next(reader)[1]
            for row in reader:
                self.queries.append(row)
        # load constraints
        if os.path.exists(f'{data_dir}/constraints/{pid}.yml'):
            with open(f'{data_dir}/constraints/{pid}.yml') as f:
                self.data_constraints = yaml.safe_load(f)

    def get_mutant(self):
        print(f'getting mutants for problem {self.pid}')
        self.mutants = defaultdict(list)
        for qid, query in self.queries:
            mutants = query_mutants(self.schema, query)
            self.mutants[qid] = mutants
            print(f'got {len(mutants)} mutants for query {qid}')
            self.n_total_mutants[qid] = len(mutants)

    