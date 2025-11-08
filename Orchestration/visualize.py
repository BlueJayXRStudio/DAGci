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
from Tools.logging.run_logger import RunLogger
import webbrowser
from collections import defaultdict, deque
import sqlite3, json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
base_resolver = PathResolveNormalizer(BASE_DIR)
project_resolver = PathResolveNormalizer(_bootstrap.project_root)

if len(sys.argv) <= 1:
    sys.exit(1)

blob_uuid = sys.argv[1]

### FOR RUN VISUALIZATION ###
run_logger = RunLogger(base_resolver.resolved("db/runs.sqlite"), base_resolver.resolved("blobs"))
run_logger.load(blob_uuid)

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
NODES = run_logger.graph_data['NODES']
EDGES = run_logger.graph_data['EDGES']
LEVELS = run_logger.graph_data['LEVELS']
STATUS = run_logger.graph_data['STATUS']
LOGS = run_logger.graph_data['LOGS']

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

@app.get("/logs/{log_name}")
async def return_logs(log_name: str, request: Request):
    content = "".join(LOGS[f"{log_name}"])
    return Response(content, media_type="text/plain")

async def open_browser():
    url = "http://0.0.0.0:8100"
    # url = "http://localhost:8100"
    webbrowser.open(url)

@app.on_event("startup")
async def start_pusher():
    asyncio.create_task(open_browser())

if __name__ == "__main__":
    # Don't run as main if running for production, I hope you know that.
    # Use Uvicorn or Gunicorn...
    
    uvicorn.run(app, host="0.0.0.0", port=8100, reload=False) # for local network access, bind to all interfaces
    # uvicorn.run(app, host="localhost", port=8100, reload=False) 
