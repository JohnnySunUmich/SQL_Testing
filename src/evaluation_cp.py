import csv, json
import pglast.ast
import yaml
from pglast import prettify
import yaml


from constraint_based.constraint_generation import backward_generation
from constraint_based.encoder import Encoder
from constraint_based.constraints.variables import vManager
from constraint_based.commons import reset_table_id
from constraint_based.table_wrapper import gen_database
from constraint_based.oracle import run_psql
from constraint_based.utils.utils import dif_table

# manually crafted mutants and try killing non-equivalent queries

problems = [614, 1068, 1070, 181, 1148, 1149, 1445, 1661, 1747, 1141, 1113, 1821]

# problems = [1113]

input_size_bound = 2

mutation_point = 0

mutants = { 181: ["""
                    select a.name as ""employee"" from employee as a, employee as b where (a.managerid is not null and a.managerid = b.id and a.salary >= b.salary)"""
                ],
            1141: ["""
                    select activity_date as day, count(distinct user_id) as active_users 
                    from activity 
                    where activity_date >= '2019-06-28'
                    group by activity_date""",
                    """
                    select activity_date as day, count(distinct user_id) as active_users 
                    from activity 
                    where activity_date >= '2019-06-28' and activity_date < '2019-07-27'
                    group by activity_date"""
                ],
            1113: ["""
                    select extra as report_reason, count(distinct post_id) as report_count 
                    from actions 
                    where (action_date = '2019-07-04' and action = 'report' and extra <> 'null') 
                    group by extra"""
                ],
            1821: ["""
                    select customer_id 
                    from customers 
                    where (year > 2021 and revenue > 0)"""
                ]
        }

for pid in problems:

    print("#"*50)
    print(f"problem {pid} groundtruth:")
    gt = None
    wrong_queries = []
    with open(f"constraint_based/benchmarks/{pid}.csv") as f:
        reader = csv.reader(f)
        _ = next(reader)
        for row in reader:
            qid, query = row
            if int(qid) == -1:
                gt = query
            else:
                wrong_queries.append(row)

    print(prettify(gt))

    with open(f"../data/Schema/{pid}.json") as f:
        schema = json.load(f)

    databases = []

    for idx, mutant in enumerate(mutants[pid]):
        print('#'*30 + f" mutant {idx}")
        print(prettify(mutant))
        vManager.reset()
        vManager.set_bound(input_size_bound)
        reset_table_id()
        pglast_mutant = pglast.parse_sql(mutant)
        pglast_mutant_predicate = pglast_mutant[0].stmt.whereClause

        constraints = backward_generation(schema, gt, mutation_point, pglast_mutant_predicate, 2, False)

        encoder = Encoder()
        encoder.encode(constraints)
        model = encoder.eval(0, max_solutions=1)
        # database = gen_database(model)
        # print(database)
        # databases.append(database)

    # with open(f"constraint_based/config.yml") as f:
    #     config = yaml.safe_load(f)
    #
    # killed = set()
    # for database in databases:
    #     print('#'*30)
    #     print(f"using generated databse {database}")
    #     result = run_psql(gt, database, schema, 'dbt', 'tester', '')
    #     print(f"groundtruth result: {result}")
    #     for qid, query in wrong_queries:
    #         result_w = run_psql(query, database, schema, 'dbt', 'tester', '')
    #         print(f"non-equivalent query {qid} result: {result_w}")
    #         if dif_table(result_w, result):
    #             print(f"non-equivalent query {qid} result was killed")
    #             killed.add(qid)
    # print(f"killed {len(killed)}/{len(wrong_queries)}")
    #
    #
