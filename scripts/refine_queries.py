import csv, os
problem_ids = []
with open("problems.txt", 'r') as f:
    for line in f:
        problem_ids.append(line.strip())
for problem_id in problem_ids:
    print(f"problem {problem_id}")
    queries = []
    with open("queries/" + problem_id + ".txt", 'r') as f:
        for line in f:
            queries.append(line.strip())
    rows = ['100K', '10K', '1M']
    for row in rows:
        if not os.path.exists("../SQL_Optimization/data/psql_analyses/" + \
                 row + "rows/" + row + "runtime" + problem_id + ".csv"):
            continue
        with open("../SQL_Optimization/data/psql_analyses/" + \
                 row + "rows/" + row + "runtime" + problem_id + ".csv") as f:
            reader = csv.reader(f)
            _ = next(reader)
            for row in reader:
                idx = int(row[0])
                psql_query = row[2].strip()
                if idx >= len(queries):
                    queries.append(psql_query)
                    continue
                if queries[idx] != psql_query and len(queries[idx]) == 0:
                    queries[idx] = psql_query
    with open("refined_queries/" + problem_id + ".txt", 'w') as f:
        for query in queries:
            f.write(query+'\n')
            