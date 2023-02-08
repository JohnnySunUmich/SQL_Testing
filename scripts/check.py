from tester import Tester
import yaml, json, os, logging
problem = '1068'

log_path = 'logs/' + 'check_' + problem + ".txt"
logging.basicConfig(filename=log_path, encoding='utf-8', level=logging.INFO,\
    format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
slow_query = "select b.product_name, a.year, a.price from sales as a left join product as b on a.product_id = b.product_id order by 2 asc"
fast_query = "select t2.product_name, t1.year, t1.price from sales as t1 left join product as t2 on t1.product_id = t2.product_id"
found_fast_query = "SELECT c14 AS c15, c9 AS c16, c12 AS c17 FROM (SELECT c1 AS c8, c2 AS c9, c3 AS c10, c4 AS c11, c5 AS c12, c6 AS c13, c7 AS c14 FROM (SELECT sale_id AS c1, year AS c2, product_id AS c3, quantity AS c4, price AS c5 FROM sales) AS cte161 LEFT JOIN (SELECT product_id AS c6, product_name AS c7 FROM product) AS cte162 ON c3 = c6) AS cte163"

# read schema, cstr, and config
with open('config.yml', 'r') as f:
    default_config = yaml.safe_load(f)
with open("Schema/" + problem + ".json", 'r') as f:
    schema = json.load(f)
cstr_path = 'constraints/' + problem + ".yml"
if os.path.exists(cstr_path):
    with open(cstr_path, 'r') as f:
        cstr = yaml.safe_load(f)
else:
    cstr = {}
config = default_config
config["problem"] = 1068
config["tester"]["max_trials"] = 500
tester = Tester(schema, config["tester"], cstr)
logging.info(f"slow_query: {slow_query}")
logging.info(f"fast_query: {fast_query}")
logging.info(f"found_fast_query: {found_fast_query}")
logging.info(f"slow_query vs fast_query")
tester.kill(slow_query, fast_query)
logging.info(f"slow_query vs found_fast_query")
tester.kill(slow_query, found_fast_query)
logging.info(f"fast_query vs found_fast_query")
tester.kill(fast_query, found_fast_query)