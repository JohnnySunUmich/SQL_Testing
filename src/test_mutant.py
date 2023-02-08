from constraint_based.mutants.mutant import generate_mutants
from constraint_based.load_benchmark import Benchmark_Loader
from pglast.stream import RawStream

supported_problems = ['196', '181', '1821', '595', '1270', '1517', '1068', '1378', '175', '1623', '1421', '1757']

for pid in supported_problems:
    try:
        loader = Benchmark_Loader(pid, "../data")
    except Exception as e:
        print(f"fail to load as {e}")
        continue

    print("#" * 50)
    print(f"problem {pid} groundtruth: {loader.groundtruth}")
    print(f"problem {pid} mutants:")
    mutants = generate_mutants(loader.groundtruth)
    for mutant_type in mutants:
        print(mutant_type)
        for mutant_ast in mutants[mutant_type]:
            print(RawStream()(mutant_ast))
