import csv, json

pids = []
with open('problems.txt') as f:
    for row in f:
        pids.append(row.strip())
for pid in pids:
    with open('../Schema/' + pid + '.json') as f:
        schema = json.load(f)
    rows = []
    with open('../mysql_queries/origin' + pid + '.csv') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            rows.append([row[0], row[1]])
    names = []
    for table in schema['Tables']:
        names.append(table['TableName'])
    for i, row in enumerate(rows):
        for name in names:
            name_u = name.upper()
            name_l = name.lower()
            if name_u in row[1]:
                print(rows[i][1])
                print(name_u)
                print(name)
                rows[i][1] = rows[i][1].replace(name_u, name)
                print(rows[i][1])
            if name_l in row[1]:
                rows[i][1] = rows[i][1].replace(name_l, name)

    with open('../mysql_queries/origin' + pid + '.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)