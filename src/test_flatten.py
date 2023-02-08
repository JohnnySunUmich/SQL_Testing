from constraint_based.load_benchmark import Benchmark_Loader
from constraint_based.flatten import Flatten

next_to_support = ['181', '1821', '1068', '1378', '175', '1623', '1757']

for pid in next_to_support:
    loader = Benchmark_Loader(pid, "../data")

    ft = Flatten(loader.schema, 2)
    print(loader.groundtruth)
    ft.flatten(loader.groundtruth)
    print(ft)
