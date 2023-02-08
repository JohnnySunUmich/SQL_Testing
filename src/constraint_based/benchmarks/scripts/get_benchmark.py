from collections import defaultdict
import os, csv
benchmark_dir = '../../../../data/labeled_queries/inspecting'
benchmarks = os.listdir(benchmark_dir)
benchmarks = [benchmark.split('.')[0] for benchmark in benchmarks]
confirmed_benchmarks = {}

for pid in benchmarks:
    records = []

    with open(f'{benchmark_dir}/{pid}.csv') as f:
        reader = csv.reader(f)
        _ = next(reader)
        for row in reader:
            records.append([row[0], row[-1]])
    with open(f'../{pid}.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['qid', 'psql_query'])
        writer.writerows(records)

    confirmed_benchmarks[pid] = len(records) - 1

with open('benchmark_summary.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['pid', 'num_not_equivalent'])
    writer.writerows(confirmed_benchmarks)