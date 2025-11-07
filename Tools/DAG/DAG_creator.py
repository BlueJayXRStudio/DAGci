import sys, os, _bootstrap
from collections import defaultdict, deque

class DAGCreator:
    def __init__(self, yaml_config):
        self.config = yaml_config
        self.graph = None
        self.in_degree = None
        self.graph_reversed = None
        self.in_degree_reversed = None
        self.init_DAG()

    def get_DAG(self):
        return self.graph, self.in_degree
    
    def get_DAG_reversed(self):
        return self.graph_reversed, self.in_degree_reversed

    def get_pyvis_objects(self):
        NODES = list(self.in_degree_reversed.keys())
        EDGES = []
        for dependency in list(self.graph_reversed.keys()):
            for dependent in self.graph_reversed[dependency]:
                EDGES.append((dependency, dependent))
        return NODES, EDGES

    def get_levels(self):
        ### Figure out stages/levels for prettier graph visualization   ###
        # This has no bearing on the actual runtime algorithm, which      #
        # is dynamic and parallel. Will factor em out in the near future. #
        level_tracking = self.in_degree_reversed.copy() # shallow copy
        LEVELS = self.in_degree_reversed.copy() # shallow copy

        queue = deque()
        count = 0
        for node, degree in level_tracking.items():
            if degree == 0:
                LEVELS[node] = 0
                queue.append(node)

        while queue:
            node = queue.popleft()
            count += 1

            for neighbor in self.graph_reversed[node]:
                level_tracking[neighbor] -= 1
                if level_tracking[neighbor] == 0:
                    LEVELS[neighbor] = LEVELS[node]+1
                    queue.append(neighbor)                                
        return LEVELS

    def check_cycles(self):
        queue = deque()
        count = 0
        topo_sorted = []
        for node, degree in self.in_degree.items():
            if degree == 0:
                queue.append(node)
                topo_sorted.append(node)

        while queue:
            node = queue.popleft()
            count += 1

            for neighbor in self.graph[node]:
                self.in_degree[neighbor] -= 1
                if self.in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    topo_sorted.append(neighbor)
                    
        # print(topo_sorted[::-1])
        return (count == len(self.in_degree), topo_sorted[::-1])
    
    def init_DAG(self):
        # use for cycles detection
        self.graph = defaultdict(lambda: set())
        self.in_degree = {}
        # use for parallelized job queueing
        self.graph_reversed = defaultdict(lambda: set())
        self.in_degree_reversed = {}

        for job in self.config['jobs'].items():
            job_name = job[0]
            self.in_degree[job_name] = 0
            self.in_degree_reversed[job_name] = 0

        for job in self.config['jobs'].items():
            job_name = job[0]
            # print("job name: ", job_name)
            job_commands = job[1]['run']
            # print("job commands: ", job_commands)
            job_requirements = job[1]['needs']
            # print("job requirements: ", job_requirements)
            
            for dependency in job_requirements:
                self.graph[job_name].add(dependency)
                self.in_degree[dependency] += 1
                self.graph_reversed[dependency].add(job_name)
                self.in_degree_reversed[job_name] += 1
