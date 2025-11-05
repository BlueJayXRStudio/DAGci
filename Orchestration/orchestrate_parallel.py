import sys, os, _bootstrap
import subprocess, threading, time
from Tools.path_tools import PathResolveNormalizer
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
WORKFLOW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflows")
import yaml
from collections import defaultdict, deque
from Orchestration.check_cycles import CheckCycles

path_resolver = PathResolveNormalizer(BASE_DIR)
project_resolver = PathResolveNormalizer(PARENT_DIR)
workflow_path_resolver = PathResolveNormalizer(WORKFLOW_DIR)

config = None
with open(path_resolver.resolved("workflows/full_pipeline_adb_deploy.yml"), "r") as f:
    config = yaml.safe_load(f)

# use for cycles detection
graph = defaultdict(lambda: set())
in_degree = {}
# use for parallelized job queueing
graph_reversed = defaultdict(lambda: set())
in_degree_reversed = {}

for job in config['jobs'].items():
    job_name = job[0]
    in_degree[job_name] = 0
    in_degree_reversed[job_name] = 0

for job in config['jobs'].items():
    job_name = job[0]
    # print("job name: ", job_name)
    job_commands = job[1]['run']
    # print("job commands: ", job_commands)
    job_requirements = job[1]['needs']
    # print("job requirements: ", job_requirements)
    
    for dependency in job_requirements:
        graph[job_name].add(dependency)
        in_degree[dependency] += 1
        graph_reversed[dependency].add(job_name)
        in_degree_reversed[job_name] += 1


cycle_detector = CheckCycles(in_degree, graph)

no_cycles, topo_sorted = cycle_detector.check_cycles()
print("No cycles detected" if no_cycles else "Cycles detected")
print(topo_sorted)

if not no_cycles:
    sys.exit(1)



### RUN JOBS ###
MAX_PARALLEL_JOBS = 2

queue = deque()
for node, degree in in_degree_reversed.items():
    if degree == 0:
        queue.append(node)

lock = threading.Lock()
cond = threading.Condition(lock)
_count = 0

def worker():
    global _count
    while True:
        with cond:
            while not queue:
                print("Waiting for a job...")
                cond.wait()
                if _count == len(in_degree_reversed):
                    return
                
            job_name = queue.popleft()
            print(job_name)

            components = config['jobs'][job_name]['run'][0].split()
            rel_path = config['jobs'][job_name]['run'][0].split()[-1]
            resolved_path = project_resolver.resolved(rel_path)
            components[-1] = resolved_path

        result = subprocess.run(components, capture_output=True, text=True)
        print(result.stdout)
        # if result.returncode == 0:
        with cond:
            _count += 1
            for dependent in graph_reversed[job_name]:
                in_degree_reversed[dependent] -= 1
                if in_degree_reversed[dependent] == 0:
                    queue.append(dependent)
                    cond.notify()
            
            if _count == len(in_degree_reversed):
                cond.notify_all()
                return

threads = [threading.Thread(target=worker) for _ in range(MAX_PARALLEL_JOBS)]
for t in threads: t.start()
for t in threads: t.join()

sys.exit(0)
