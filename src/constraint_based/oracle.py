from typing import List
from .utils.psql_utils import run_psql
from .utils.utils import dif_table
from .encoder import Encoder
from .flatten import *
from .table_generation import Table_Generator

import random

dbname_id = 0

class Oracle():
    def __init__(self, schema, config: dict) -> None:
        self.testcases = []
        self.schema = schema
        self.config = config
        self.flattener = Flatten(schema=self.schema)
        self.encoder = Encoder()
        self.table_generator = Table_Generator(schema, config)
        random.seed(config['seed'])

    def __gen_one_testcase(self, query: str, generation_guidance: List[dict]) -> dict:
        return self.table_generator.gen_database(generation_guidance)

    def __run_one_query(self, query: str, database):
        global dbname_id
        dbname_id = (dbname_id + 1) % 100
        dbname = 'db' + str(dbname_id)
        return run_psql(query, database, self.schema, dbname, self.config['username'], self.config['password'])

    def gen_testcases(self, query: str, mutants: List[str]=None) -> None:
        self.correct_outputs = []
        flatten_query = self.flattener.flatten(query)
        generation_guidances = self.encoder.encode(flatten_query, max_solutions=self.config['max_trials'])
        generation_guidances = generation_guidances + random.choices(generation_guidances, k=self.config['max_trials']-len(generation_guidances))
        print('#'*10 + ' all testcases generated ' + '#'*10)
        for i in range(self.config['max_trials']):
            testcase = self.__gen_one_testcase(query, generation_guidances[i])
            print(testcase)
            correct_output = self.__run_one_query(query, testcase)
            self.testcases.append(testcase)
            self.correct_outputs.append(correct_output)
        print('#'*10 + ' killing mutants ' + '#'*10)
        if self.config['mode'] == 'mutation':
            testcase_mask = [0] * len(self.testcases)
            k = 0
            n_mutants_killes = 0
            n_all_mutants = len(mutants)
            n_error_mutants = 0
            for correct_output, testcase in zip(self.correct_outputs, self.testcases):
                mutant_mask = [0] * len(mutants)
                for i, mutant in enumerate(mutants):
                    try:
                        output = self.__run_one_query(mutant, testcase)
                        if dif_table(output, correct_output):
                            mutant_mask[i] = 1
                            n_mutants_killes += 1
                            print(f'killed mutant {i}')
                    except Exception as e:
                        print(f'fail to run mutant {i}')
                        mutant_mask[i] = 1
                        n_error_mutants += 1
                if sum(mutant_mask) != 0:
                    testcase_mask[k] = 1
                    temp = []
                    for i, mask in enumerate(mutant_mask):
                        if mask == 0:
                            temp.append(mutants[i])
                    mutants = temp
                k += 1
            temp_testcases = []
            temp_correct_outputs = []
            for k, mask in enumerate(testcase_mask):
                if mask == 1:
                    temp_testcases.append(self.testcases[k])
                    temp_correct_outputs.append(self.correct_outputs[k])
            self.testcases = temp_testcases
            self.correct_outputs = temp_correct_outputs
            print(f'killed mutants: {n_mutants_killes}/{n_all_mutants}')
            print(f'error mutants: {n_error_mutants}/{n_all_mutants}')
    
    def test(self, query_to_test):
        # return the testcase if the query_to_test is detected wrong
        # else return None
        for correct_output, testcase in zip(self.correct_outputs, self.testcases):
            output = self.__run_one_query(query_to_test, testcase)
            if dif_table(output, correct_output):
                return testcase
        return None


