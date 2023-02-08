import os
import csv
query_files = os.listdir('../mysql_queries')
counts = []
pair_counts = []
for qf in query_files:
    count = 0
    with open('../mysql_queries/' + qf) as f:
        reader = csv.reader(f)
        _ = next(reader)
        for row in reader:
            count += 1
    counts.append(count)
    pair_count = count * (count - 1) / 2
    pair_counts.append(pair_count)
print(sum(counts))
print(sum(pair_counts))
