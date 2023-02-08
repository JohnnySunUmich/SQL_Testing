import csv, os, json
filenames = os.listdir('../search_output/confirmed_benchmarks')
for i in range(len(filenames)):
    filenames[i] = filenames[i].split('.')[0]
for filename in filenames:
    csv_filename = filename.replace('_', '-') + '.csv'
    json_filename = filename.replace('-', '_') + '.json'
    filestrin = ""
    with open('../search_output/' + csv_filename) as f:
        for row in f:
            filestrin += row.strip() + ' '
    output = filestrin.split('\"')
    queries = []
    for row in output:
        if len(row) > 1:
            queries.append(row)
    with open('../search_output/confirmed_benchmarks/' + json_filename) as f:
        benchmark = json.load(f)
        slow_query = benchmark['slow']['query']
    with open('../search_output/cleaned/' + filename + '.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'query'])
        writer.writerow([-1, slow_query])
        for i, query in enumerate(queries):
            writer.writerow([i, query])
