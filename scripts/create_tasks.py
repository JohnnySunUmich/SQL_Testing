from main import run
import yaml
if __name__ == "__main__":
    problem_id = []
    with open("re_problems.txt", 'r') as f:
        for line in f:
            pid = line.strip()
            if len(pid) != 0:
                problem_id.append(int(pid))
    with open("config.yml", 'r') as f:
        default_conf = yaml.safe_load(f)
    configs = [default_conf for _  in range(len(problem_id))]
    for i, conf in enumerate(configs):
        configs[i]["problem"] = problem_id[i]
        run(configs[i])