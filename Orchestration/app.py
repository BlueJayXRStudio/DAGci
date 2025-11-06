import sys, os, time, _bootstrap
import subprocess, threading
import uvicorn
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pyvis.network import Network
import json
import asyncio
from asyncio import Queue
from Tools.path_tools import PathResolveNormalizer
from Orchestration.check_cycles import CheckCycles
import webbrowser
import yaml
from collections import defaultdict, deque

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
WORKFLOW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflows")
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

### RUN INTERACTIVE WEB APP ###
app = FastAPI()
message_queue = Queue()
message_queue_log = Queue()
main_loop = None
LOOP_READY_EVENT = threading.Event()
lock = threading.Lock()
cond = threading.Condition(lock)

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# For PyVis
NODES = list(in_degree_reversed.keys())
print(graph_reversed)
EDGES = []
for dependency in list(graph_reversed.keys()):
    for dependent in graph_reversed[dependency]:
        EDGES.append((dependency, dependent))

### Figure out stages/levels for prettier graph visualization   ###
# This has no bearing on the actual runtime algorithm, which      #
# is dynamic and parallel. Will factor em out in the near future. #
level_tracking = in_degree_reversed.copy()
LEVELS = in_degree_reversed.copy()

queue = deque()
count = 0
for node, degree in level_tracking.items():
    if degree == 0:
        LEVELS[node] = 0
        queue.append(node)

while queue:
    node = queue.popleft()
    count += 1

    for neighbor in graph_reversed[node]:
        level_tracking[neighbor] -= 1
        if level_tracking[neighbor] == 0:
            LEVELS[neighbor] = LEVELS[node]+1
            queue.append(neighbor)                                
#                                                                 #
###                                                             ###

STATUS = { node : 'queued' for node in list(in_degree_reversed.keys()) } 
LOGS = { node : [] for node in list(in_degree_reversed.keys()) }

def build_graph():
    net = Network(height="600px", width="100%", directed=True)

    STATUS_COLOR = {
        "success": "#2ecc71",
        "failure": "#e74c3c",
        "queued": "#c9d8da",
        "running": "#eff694"
    }

    for node in NODES:
        status = STATUS.get(node, "queued")
        color = STATUS_COLOR.get(status, "#95a5a6")

        net.add_node(
            node,
            label=node,
            color=color
        )

    for src, dst in EDGES:
        net.add_edge(src, dst)

    for node in net.nodes:
        node["status"] = STATUS.get(node["id"], "queued")
        node["level"] = LEVELS.get(node["id"], 0)

    return net.nodes, net.edges

@app.get("/", response_class=HTMLResponse)
async def render_graph(request: Request):
    node_data, edge_data = build_graph()
    options = json.dumps({
        "layout": {
            "hierarchical": {
                "enabled": True,
                "direction": "LR",
                "sortMethod": "hubsize"
            }
        },
        "physics": {"enabled": False}
    })

    return templates.TemplateResponse("graph.html", {
        "request": request,
        "nodes": node_data,
        "edges": edge_data,
        "options": options,
    })

# Store connected sockets
SOCKETS = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    SOCKETS.add(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        SOCKETS.remove(websocket)

@app.get("/logs/{log_name}")
async def render_graph(log_name: str, request: Request):
    content = "".join(LOGS[f"{log_name}"])
    return Response(content, media_type="text/plain")

async def push_update_to_clients():
    while True:
        node, status = await message_queue.get()
        STATUS[node] = status
        node_data, edge_data = build_graph()

        payload = {
            "type": "GRAPH_UPDATE",
            "data": {
                "nodes": node_data,
                "edges": edge_data
            }
        }
        dead = []
        for ws in SOCKETS:
            try:
                await ws.send_json(payload) 
            except Exception:
                dead.append(ws)
        for ws in dead:
            SOCKETS.remove(ws)

async def push_log_update_to_clients():
    while True:
        node, log_message = await message_queue_log.get()
        LOGS[node].append(log_message)
        
        payload = {
            "type": "LOG_MESSAGE",
            "data": {
                "node": node,
                "message": log_message
                }
        }
        dead = []
        for ws in SOCKETS:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            SOCKETS.remove(ws)

@app.on_event("startup")
async def start_pusher():
    global main_loop
    main_loop = asyncio.get_running_loop()
    LOOP_READY_EVENT.set()

    asyncio.create_task(push_update_to_clients())
    asyncio.create_task(push_log_update_to_clients())

### RUN JOBS AND WORKERS ###
MAX_PARALLEL_JOBS = 5

queue = deque()
for node, degree in in_degree_reversed.items():
    if degree == 0:
        queue.append(node)

_count = 0
_stop = False


def worker():
    '''
    As far as correctness is concerned, this will never queue up a dependent if any one of its dependencies fail.
    Termination was a little harder to prove in the standalone version in Orchestration/orchestrate_DAG.py, but
    here it really doesn't even matter. I will see if I can formally prove some of these properties... but um yea.
    Overall, please think of this as a parallelized version of Kahn's algorithm.
    '''
    LOOP_READY_EVENT.wait() # Need this to ensure that main_loop is initialized and hence we can send socket messages properly! Verrry important!
    
    global _count
    global _stop
    global main_loop

    while True:
        with cond:
            while not queue and _count < len(in_degree_reversed) and not _stop:
                print("Waiting for a job...")
                cond.wait()
            if _count != len(in_degree_reversed) and not _stop:
                job_name = queue.popleft()
                print(job_name)

                components = config['jobs'][job_name]['run'][0].split()
                rel_path = config['jobs'][job_name]['run'][0].split()[-1]
                resolved_path = project_resolver.resolved(rel_path)
                components[-1] = resolved_path
                
                if main_loop and not main_loop.is_closed():
                    asyncio.run_coroutine_threadsafe(
                        message_queue.put((job_name, 'running')),
                        main_loop
                    )
            else:
                return

        # run subprocess outside condition to release the lock for other threads
        # result = subprocess.run(components, capture_output=True, text=True)
        # print(result.stdout)
        result = subprocess.Popen(
            components,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1  # line-buffered
        )

        captured_output = []
        for line in result.stdout:
            # sys.stdout.write(line)        # stream to console
            captured_output.append(line)    # capture for later use
            if main_loop and not main_loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    message_queue_log.put((job_name, line)),
                    main_loop
                )
        result.wait()
        # output_str = "".join(captured_output)
        # print(output_str)

        with cond:
            if _stop:
                return
            if result.returncode == 0:
                if main_loop and not main_loop.is_closed():
                    asyncio.run_coroutine_threadsafe(
                        message_queue.put((job_name, 'success')),
                        main_loop
                    )

                _count += 1
                for dependent in graph_reversed[job_name]:
                    in_degree_reversed[dependent] -= 1
                    if in_degree_reversed[dependent] == 0:
                        queue.append(dependent)
                        cond.notify()
                if _count == len(in_degree_reversed):
                    cond.notify_all()
                    return
            else:
                if main_loop and not main_loop.is_closed():
                    asyncio.run_coroutine_threadsafe(
                        message_queue.put((job_name, 'failure')),
                        main_loop
                    )
                _stop = True
                cond.notify_all()
                return

threads = [threading.Thread(target=worker) for _ in range(MAX_PARALLEL_JOBS)]
for t in threads: t.start()
# for t in threads: t.join() # If this were NOT a web app, you'd ideally join before terminating.
webbrowser.open(f"http://localhost:8100") # Open browser to localhost:8100 

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100, reload=False) # Don't run as main if running for production, I hope you know that.