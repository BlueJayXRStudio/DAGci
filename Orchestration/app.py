import sys, os, time, _bootstrap
import subprocess, threading
import uvicorn
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
from pyvis.network import Network
import asyncio
from asyncio import Queue
from Tools.path_tools import PathResolveNormalizer
from Tools.DAG.DAG_creator import DAGCreator
from Tools.config_getter import ConfigGetter
import webbrowser
from collections import defaultdict, deque
import sqlite3, json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
base_resolver = PathResolveNormalizer(BASE_DIR)
project_resolver = PathResolveNormalizer(_bootstrap.project_root)

### WORKFLOW SETUP ###
# Open file dialog to retrieve workflow config
config_getter = ConfigGetter()
if not config_getter.config:
    print("No valid file selected.")
    sys.exit(1)

config = config_getter.config
dag_creator = DAGCreator(config)
graph, in_degree = dag_creator.get_DAG()
graph_reversed, in_degree_reversed = dag_creator.get_DAG_reversed()

no_cycles, topo_sorted = dag_creator.check_cycles()
print("No cycles detected" if no_cycles else "Cycles detected")
# print(topo_sorted)
# Exit if cycles detected
if not no_cycles:
    sys.exit(1)

### FOR PYVIS ###
TEMPLATE_DIR = base_resolver.resolved("templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)
'''
NODES: list[str]
EDGES: list[list[str]] # 2-tuple
LEVELS: dict[str, int]
STATUS: dict[str, str]
LOGS: dict[str, list[str]]
'''
NODES, EDGES = dag_creator.get_pyvis_objects()
LEVELS = dag_creator.get_levels()
STATUS = { node : 'queued' for node in list(in_degree_reversed.keys()) } 
LOGS = { node : [] for node in list(in_degree_reversed.keys()) }
# State builder
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
        net.add_node( node, label=node, color=color )
    for src, dst in EDGES:
        net.add_edge(src, dst)
    for node in net.nodes:
        node["status"] = STATUS.get(node["id"], "queued")
        node["level"] = LEVELS.get(node["id"], 0)
    return net.nodes, net.edges

### FOR WEB APP ###
app = FastAPI()
message_queue = Queue()
message_queue_log = Queue()
main_loop = None
lock = threading.Lock()
cond = threading.Condition(lock)
SOCKETS = set()

### BACKEND ###
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
async def return_logs(log_name: str, request: Request):
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

async def start_workflow():
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
        nonlocal _count
        nonlocal _stop
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

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(MAX_PARALLEL_JOBS)]
    for t in threads: t.start()
    # for t in threads: t.join() # If this were NOT a web app, you'd ideally join before terminating.

async def open_browser():
    url = "http://localhost:8100"
    webbrowser.open(url)

@app.on_event("startup")
async def start_pusher():
    global main_loop
    main_loop = asyncio.get_running_loop()

    asyncio.create_task(push_update_to_clients())
    asyncio.create_task(push_log_update_to_clients())
    asyncio.create_task(start_workflow())
    asyncio.create_task(open_browser())

if __name__ == "__main__":
    # Don't run as main if running for production, I hope you know that.
    # Use Uvicorn or Gunicorn...
    
    # uvicorn.run(app, host="0.0.0.0", port=8100, reload=False) # for local network access, bind to all interfaces
    uvicorn.run(app, host="localhost", port=8100, reload=False) 

