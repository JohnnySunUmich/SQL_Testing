import csv
import json
import os.path
import yaml
from collections import defaultdict
from .mutants.mutant import generate_mutants
from pglast.stream import RawStream

query_dir = "labeled_queries"
gt_dir = "groundtruths"
schema_dir = "Schema"
manual_mutants_dir = "manual_mutants"
integrity_constraints_dir = "constraints"


class Benchmark_Loader:
    def __init__(self, pid, path):
        self.pid = pid
        self.path = path
        self._load_schema()
        self._load_groundtruth()
        self._load_labeled_queries()

    def _load_schema(self):
        if not os.path.exists(f"{self.path}/{schema_dir}/{self.pid}.json"):
            raise Exception(f"Schema file does not exist for problem {self.pid}")
        with open(f"{self.path}/{schema_dir}/{self.pid}.json") as f:
            self.schema = json.load(f)

    def _load_groundtruth(self):
        if not os.path.exists(f"{self.path}/{gt_dir}/psql/{self.pid}.csv"):
            raise Exception(f"groundtruth file does not exist for problem {self.pid}")
        with open(f"{self.path}/{gt_dir}/psql/{self.pid}.csv") as f:
            reader = csv.reader(f)
            _ = next(reader)
            _, query = next(reader)
            self.groundtruth = query

    def _load_labeled_queries(self):
        self.queries = {}
        if not os.path.exists(f"{self.path}/{query_dir}/{self.pid}.csv"):
            raise Exception(f"labeled query file does not exist for problem {self.pid}")
        with open(f"{self.path}/{query_dir}/{self.pid}.csv") as f:
            reader = csv.reader(f)
            _ = next(reader)
            # qid,mysql_can_execute?,mysql_correct?,translate_successful?,psql_can_execute?,psql_correct?,mysql_query,psql_query
            for row in reader:
                qid, _, _, _, exe, corr, _, query = row
                self.queries[qid] = {
                    "query": query,
                    "executable": False if exe == "N" else True,
                    "correct": False if corr == "N" else True
                }

    def _load_raw_integrity_constraints(self):
        if not os.path.exists(f"{self.path}/{integrity_constraints_dir}/{self.pid}.yml"):
            self.raw_integrity_constraints = {}
        with open(f"{self.path}/{integrity_constraints_dir}/{self.pid}.yml") as f:
            self.raw_integrity_constraints = yaml.safe_load(f)


    def get_groundtruth(self) -> str:
        return self.groundtruth

    def get_wrong(self) -> []:
        # return a list of [qid, query_str]
        output = []
        for qid in self.queries:
            if self.queries[qid]["executable"] and not self.queries[qid]["correct"]:
                output.append([qid, self.queries[qid]["query"]])
        return output

    def load_manual_mutants(self):
        mutants = defaultdict(list)
        if not os.path.exists(f"{self.path}/{manual_mutants_dir}/{self.pid}.csv"):
            print(f"manual mutants does not exist for problem {self.pid}")
            return None
        with open(f"{self.path}/{manual_mutants_dir}/{self.pid}.csv") as f:
            reader = csv.reader(f)
            _ = next(reader)
            for row in reader:
                if len(row) < 2:
                    continue
                mutation_type, mutant = row
                if mutation_type == "GT":
                    continue
                mutants[mutation_type].append(mutant)
        return mutants

    def load_mutants(self):
        mutants = defaultdict(list)
        mutant_ast = generate_mutants(self.groundtruth)
        for mutant_type in mutant_ast:
            mutants[mutant_type] = []
            for ast in mutant_ast[mutant_type]:
                mutant = RawStream()(ast)
                if mutant not in mutants[mutant_type]:
                    mutants[mutant_type].append(mutant)
        return mutants
