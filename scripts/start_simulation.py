import os, sys, yaml, json, logging, datetime
from simulator import Simulator

if __name__ == '__main__':
    # setup logging
    log_path = 'logs/simulation_' + datetime.datetime.now().strftime("%m%d%H%M%S") + '_' \
                + ".txt"
    if not os.path.exists('log'):
        os.mkdir('log')
    logging.basicConfig(filename=log_path, encoding='utf-8', level=logging.INFO,\
        format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    input_file_path = sys.argv[1]
    # read tasks pid-slow-fast1_fast2_...
    tasks = []
    with open('simulate_task_list.txt', 'r') as f:
        for line in f:
            tasks.append(line.strip())
    # read default config file
    with open('config.yml', 'r') as f:
        default_config = yaml.safe_load(f)
    # create tasks
    for task in tasks:
        logging.info(f"doing task {task}")
        task_list = task.split('-')
        pid = task_list[0]
        slow_idx = int(task_list[1])
        fast_idx = task_list[2].split('_')
        # read slow query
        with open("queries/" + pid + ".txt", 'r') as f:
            for i, line in enumerate(f):
                if i == slow_idx:
                    slow_query = line.strip()
        # read search output
        output_queries = []
        with open(input_file_path + '/' + task, 'r') as f:
            for line in f:
                output_queries.append(line.strip())
        # read schema
        with open("Schema/" + pid + ".json", 'r') as f:
            schema = json.load(f)
        # read constraint
        cstr_path = "constraints/" + pid + ".yml"
        if os.path.exists(cstr_path):
            with open(cstr_path, 'r') as f:
                cstr = yaml.safe_load(f)
        else:
            cstr = {}
        # customize config
        config = default_config
        config["problem"] = pid
        # simulate
        result_path = "results/simulation_" + pid + '_' + str(slow_idx)
        sim = Simulator(schema, config, output_queries, slow_query, cstr, result_path)
        sim.run()

