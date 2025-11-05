from collections import defaultdict, deque

class CheckCycles:
    def __init__(self, in_degree: dict, graph: defaultdict):
        self.in_degree = in_degree
        self.graph = graph

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