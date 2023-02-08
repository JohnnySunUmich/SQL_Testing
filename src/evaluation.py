import random
import time
from pglast import prettify
import yaml


from constraint_based.load_benchmark import Benchmark_Loader
from constraint_based.constraint_generation import Constraint_Generator
from constraint_based.encoder import Encoder
from constraint_based.constraints.variables import vManager
from constraint_based.commons import reset_table_id
from constraint_based.table_wrapper import gen_database
from constraint_based.oracle import run_psql
from constraint_based.utils.utils import dif_table

supported_problems = ['196', '181', '1821', '595', '1270', '1517', '1068', '1378', '175', '1421', '1757', '1623']

input_size_bound = 2

# sanity-check

n_mutants = 0
time_to_kill = 0

for pid in supported_problems:
    vManager.reset()
    reset_table_id()

    try:
        loader = Benchmark_Loader(pid, "../data")
    except Exception as e:
        print(f"fail to load as {e}")
        continue

    print("#"*50)
    print(f"problem {pid} groundtruth:")

    gt = loader.groundtruth
    wrong_queries = loader.get_wrong()

    print(prettify(gt))

    mutants = loader.load_mutants()

    generator = Constraint_Generator(loader.schema, gt, initial_size_bound=input_size_bound,
                                     mode="pessimistic", verbose=False)

    databases = []

    print(f"{'#'*10} generating databases based on mutants {'#'*10}")

    for mutation_type in mutants:
        print(f"working on mutation type: {mutation_type}")

        count_mutant = 0
        random.shuffle(mutants[mutation_type])
        for mutant in mutants[mutation_type]:
            n_mutants += 1
            print(f"generating constraints for mutant: {mutant}")
            if " natural " in mutant.lower():
                print(f"skip because of natural join")
                continue
            if "> '" in mutant.lower() or ">= '" in mutant.lower() or "< '" in mutant.lower()\
                or "<= " in mutant.lower():
                print(f"cannot compare string")
                continue
            if not generator.load_mutant(mutant, mutation_type):
                continue
            start = time.time()
            constraints = generator.generate_constraints()
            encoder = Encoder()
            encoder.encode(constraints, verbose=False)
            table_ids = [i for i in range(len(loader.schema["Tables"]))]
            model = encoder.eval(table_ids)
            if model is None:
                continue
            print(f"generated Z3 model: {model}")
            database = gen_database(model)
            end = time.time()
            time_to_kill += end - start
            print(f"generated database: {database}")
            databases.append(database)
            count_mutant += 1
            if count_mutant >= 10:
                break
        # break

    # real evaluation

    # print(f"{'#' * 10} trying to kill wrong queries using generated mutants {'#' * 10}")
    #
    # with open(f"constraint_based/config.yml") as f:
    #     config = yaml.safe_load(f)
    #
    # killed = set()
    #
    # for database in databases:
    #     print(f"using generated database {database}")
    #     result = run_psql(gt, database, loader.schema, 'dbt', 'tester', '')
    #     print(f"groundtruth result: {result}")
    #     for qid, query in wrong_queries:
    #         result_w = run_psql(query, database, loader.schema, 'dbt', 'tester', '')
    #         print(f"non-equivalent query {qid} {query} result: {result_w}")
    #         if dif_table(result_w, result):
    #             print(f"non-equivalent query {qid} result was killed")
    #             killed.add(qid)
    # print(f"killed {len(killed)}/{len(wrong_queries)}")

print(f"total number of mutants: {n_mutants}, total time costs to kill mutants: {time_to_kill}")


