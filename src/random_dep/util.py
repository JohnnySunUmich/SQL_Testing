from collections import defaultdict
from copy import deepcopy
import logging
import json, yaml, csv
import os

def dif_table(table1, table2, ordered=False):
    table1 = [list(row) for row in table1]
    table1 = list(zip(*table1))
    table2 = [list(row) for row in table2]
    table2 = list(zip(*table2))
    if ordered:
        for col in table1:
            if col not in table2:
                return True
        return False
    else:
        table1_set = [set(col) for col in table1]
        table2_set = [set(col) for col in table2]
        remap = [-1 for _ in table1]
        for i, col1 in enumerate(table1_set):
            for j, col2 in enumerate(table2_set):
                if col1 == col2:
                    remap[i] = j
        if -1 in remap:
            return True
        table1_re = [table1[remap[i]] for i in range(len(table1))]
        table1_re = list(zip(*table1_re))
        table2 = list(zip(*table2))
        table1_re = set([tuple(col) for col in table1_re])
        table2 = set([tuple(col) for col in table2])
        if table1_re == table2:
            return False
    return True

def topo_sort_cols(num_col, cstr: dict):
    """
    Gives a reversed topological sorting of tables according to foreign key dependency
    Raises an exception when there is a foreign key dependency cycle
    """
    n = num_col
    edges = defaultdict(list)
    alternatives = []
    chosen_alternatives = []
    for col_id in cstr.keys():
        if col_id in ['unique', 'join']: 
            continue
        for col_cstr in cstr[col_id]:
            if col_cstr['parent_col_id'] != -1:
                if col_cstr['operator'] in ['>', '<', '!=', '=']:
                    if [col_id, col_cstr['parent_col_id']] not in alternatives \
                    and [col_cstr['parent_col_id'], col_id] not in alternatives:
                        alternatives.append([
                            col_id, col_cstr['parent_col_id']
                            ])
                else:
                    edges[col_id].append(col_cstr['parent_col_id'])
    if 'unique' in cstr.keys():
        for unique_rel in cstr['unique']:
            if len(unique_rel) == 2:
                if edges[unique_rel[0]] == []:
                    edges[unique_rel[0]] = [unique_rel[1]]
    def dfs(x):
        visited[x] = 1
        for y in use_edges[x]:
            if visited[y] == 0:
                dfs(y)
            elif visited[y] == 1:
                raise Exception("Foreign key dependency cycle")
        visited[x] = 2
        topo_sorted.append(x)
    success = False
    if len(alternatives) == 0:
        use_edges = deepcopy(edges)
        topo_sorted = []
        visited = [0 for _ in range(n)]
        for k in range(n):
            try:
                if visited[k] == False:
                    dfs(k)
                if k == n-1:
                    success = True
            except Exception as e:
                    logging.info(f"fail to topo-sort using alternative {i}")
                    break
        
        if success:
            return topo_sorted
    else:
        for i in range(0, 2 ** len(alternatives)):
            use_edges = deepcopy(edges)
            bin_str = bin(i).split('b')[-1]
            bin_str = '0' * (len(alternatives) - len(bin_str)) + bin_str
            chosen_alternatives = []
            for j, d_str in enumerate(bin_str):
                decision = int(d_str)
                if decision == 0:
                    chosen_alternatives.append(alternatives[j])
                else:
                    chosen_alternatives.append([alternatives[j][-1], alternatives[j][0]])
            print(chosen_alternatives)
            for choice in chosen_alternatives:
                use_edges[choice[0]].append(choice[1])
            topo_sorted = []
            visited = [0 for _ in range(n)]
            for k in range(n):
                try:
                    if visited[k] == False:
                        dfs(k)
                    if k == n-1:
                        success = True
                except Exception as e:
                        logging.info(f"fail to topo-sort using alternative {i}")
                        break
            if success:
                return topo_sorted
    if not success:
        logging.info(f"fail to topo sort the dependency")
        raise Exception('Detected circular dependency')

def print_db(database: list):
    for table in database:
        keys = []
        for key in table.keys():
            keys.append(key)
        print(",".join(keys))
        values = []
        for key in keys:
            values.append(table[key])
        values = list(map(list, zip(*values)))
        for row in values:
            row_str = []
            for entry in row:
                row_str.append(str(entry))
            print(",".join(row_str))
        print("-"*50)

def readable_db(database: list):
    output = ""
    for table in database:
        keys = []
        for key in table.keys():
            keys.append(key)
        output += ",".join(keys) + "\n"
        values = []
        for key in keys:
            values.append(table[key])
        values = list(map(list, zip(*values)))
        for row in values:
            row_str = []
            for entry in row:
                row_str.append(str(entry))
            output += ",".join(row_str) + '\n'
        output += "-"*50 + "\n"
    return output

def get_infos(pid, path):
    with open(f"{path}/Schema/{pid}.json") as f:
        schema = json.load(f)
    with open(f"{path}/config.yml") as f:
        config = yaml.safe_load(f)
    if os.path.exists(f"{path}/constraints/{pid}.yml"):
        with open(f"{path}/constraints/{pid}.yml") as f:
            cstr = yaml.safe_load(f)
    else:
        cstr = {}
    return schema, config, cstr

def get_queries_csv(pid, path):
    queries = []
    with open(path) as f:
        reader = csv.reader(f)
        _ = next(reader)
        for row in reader:
            queries.append(row[1])
    return queries