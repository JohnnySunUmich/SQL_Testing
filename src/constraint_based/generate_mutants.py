from utils.get_mutants import query_mutants
import csv, sys, json

def save_mutant(query_dir, pid):
    with open(f'{query_dir}/{pid}.csv') as f:
        reader = csv.reader(f)
        _ = next(reader)
        row = next(reader)
        groundtruth = row[-2]
    groundtruth = "select distinct a.viewer_id from ( select viewer_id, view_date, count(distinct article_id) as cnt from views group by viewer_id, view_date ) as a where cnt > 1 order by viewer_id asc"
    # schema
    with open(f'../../data/Schema/{pid}.json') as f:
        schema = json.load(f)
    mutants = query_mutants(schema, groundtruth)
    with open(f'mutant_{pid}.csv', 'w') as f:
        writer = csv.writer(f)
        for mutant in mutants:
            writer.writerow([mutant])


if __name__ == '__main__':
    pid = sys.argv[1]
    save_mutant('../../data/labeled_queries/inspecting', pid)