from prepare_benchmark import Benchmark
from oracle import Oracle
from typing import List

def run(pids: List[int], config: dict):
    for pid in pids:
        # prepare benchmarks
        benchmark = Benchmark(pid, queries_dir='output')
        benchmark.load_search_output()
        if config['mode'] == 'mutation':
            benchmark.get_mutant()
        for qid, query in benchmark.queries:
            equivs = benchmark.equivs[qid]
            inequivs = benchmark.inequivs[qid]
            if len(equivs) == 0 and len(inequivs) == 0:
                continue
            mutants = benchmark.mutants[qid] if benchmark.mutants != [] else None
            oracle = Oracle(benchmark.schema, config)
            oracle.gen_testcases(query, mutants)
            # record statistics
            n_equivs = len(equivs)
            n_inequivs = len(inequivs)
            n_false_positive = 0
            n_false_negative = 0
            false_positives = []
            false_negatives = []
            # test equivs
            for cqid, equiv_query in equivs:
                testcase = oracle.test(equiv_query)
                if testcase:
                    n_false_positive += 1
                    false_positives.append(cqid)
            # test inequivs
            for cqid, inequivs_query in inequivs:
                testcase = oracle.test(inequivs_query)
                if not testcase:
                    n_false_negative += 1
                    false_negatives.append(cqid)
            # print summary
            print(f"{'#'*10}problem {pid} query {qid}{'#'*10}")
            if config['mode'] == 'mutation':
                print(f"{len(benchmark.n_total_mutants[qid]) - len(benchmark.mutants)} mutants killed over total {len(benchmark.n_total_mutants[qid])} mutants")
            print(f"{n_false_positive} false positives over all {n_equivs} equivalent queries: {false_positives}")
            print(f"{n_false_negative} false negatives over all {n_inequivs} inequivalent queries: {false_negatives}")
            
