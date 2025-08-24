
import threading
import socket
import json
import time
import logging
import queue
from typing import Dict, Any, Optional
import networkx as nx

logger = logging.getLogger("SimulationEngine")
logger.setLevel(logging.INFO)

class NodeWorker(threading.Thread):
    def __init__(self, name: str, topology: nx.Graph, control_event: threading.Event, stats: Dict[str, Any]):
        super().__init__(daemon=True, name=f"Node-{name}")
        self.node = name
        self.topology = topology
        self.control_event = control_event
        self._pause = threading.Event()
        self._stop = threading.Event()
        self.stats = stats
        self.logger = logging.getLogger(f"Node-{name}")

    def run(self):
        self.logger.info(f"Node {self.node} started")
        while not self._stop.is_set():
            if self._pause.is_set():
                time.sleep(0.1)
                continue
            neighs = list(self.topology.neighbors(self.node))
            self.stats.setdefault(self.node, {"ticks":0, "received":0, "sent":0})
            self.stats[self.node]["ticks"] += 1
            self.stats[self.node]["sent"] += max(0, len(neighs))
            self.stats[self.node]["received"] += max(0, len(neighs))
            time.sleep(0.05)
        self.logger.info(f"Node {self.node} stopped")

    def pause(self):
        self._pause.set()
        self.logger.info(f"Node {self.node} paused")

    def resume(self):
        self._pause.clear()
        self.logger.info(f"Node {self.node} resumed")

    def stop(self):
        self._stop.set()

class SimulationEngine:
    """
    Multithreaded simulation engine with optional TCP IPC server and
    capabilities to pause/resume, inject link failures, and gather per-node stats.
    """
    def __init__(self, topology: nx.Graph, host: str='127.0.0.1', port: int=54024):
        self.topology = topology
        self.host = host
        self.port = port
        self.node_threads: Dict[str, NodeWorker] = {}
        self.control_event = threading.Event()
        self.stats: Dict[str,Any] = {}
        self._server_thread: Optional[threading.Thread] = None
        self._server_socket: Optional[socket.socket] = None
        self._paused = False
        self.logger = logging.getLogger("SimulationEngine")

    def start(self):
        # start IPC server
        self._start_ipc_server()
        # create node threads
        for n in list(self.topology.nodes()):
            nw = NodeWorker(n, self.topology, self.control_event, self.stats)
            self.node_threads[n] = nw
            nw.start()
        self.logger.info("Starting network simulation")

    def _start_ipc_server(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(5)
            self._server_socket = s
            t = threading.Thread(target=self._ipc_accept_loop, daemon=True, name="IPC-Accept")
            t.start()
            self._server_thread = t
            self.logger.info(f"IPC server listening on port {self.port}")
        except Exception as e:
            self.logger.warning(f"Failed to start IPC server: {e}")

    def _ipc_accept_loop(self):
        s = self._server_socket
        while True:
            try:
                conn, addr = s.accept()
                threading.Thread(target=self._handle_ipc_conn, args=(conn, addr), daemon=True).start()
            except Exception:
                break

    def _handle_ipc_conn(self, conn: socket.socket, addr):
        try:
            data = conn.recv(8192)
            if not data:
                conn.close()
                return
            payload = data.decode('utf-8').strip()
            try:
                obj = json.loads(payload)
            except Exception:
                obj = {"cmd": payload}
            resp = self._process_ipc(obj)
            conn.sendall(json.dumps(resp).encode('utf-8'))
        finally:
            conn.close()

    def _process_ipc(self, obj):
        cmd = obj.get("cmd") if isinstance(obj, dict) else obj
        if cmd == "status":
            return {"status":"running","nodes":list(self.node_threads.keys())}
        if cmd == "pause":
            self.pause()
            return {"status":"paused"}
        if cmd == "resume":
            self.resume()
            return {"status":"resumed"}
        if cmd == "stats":
            return {"stats": self.stats}
        if cmd == "links":
            return {"links": [{ "u":u, "v":v, **d } for u,v,d in self.topology.edges(data=True)]}
        return {"error":"unknown command"}

    def pause(self):
        if self._paused:
            return
        for nw in self.node_threads.values():
            nw.pause()
        self._paused = True
        self.logger.info("Simulation paused")

    def resume(self):
        if not self._paused:
            return
        for nw in self.node_threads.values():
            nw.resume()
        self._paused = False
        self.logger.info("Simulation resumed")

    def inject_link_failure(self, u, v):
        if self.topology.has_edge(u, v):
            self.topology[u][v]["down"] = True
            self.logger.info(f"Link failure injected: {u} <-> {v}")
            try:
                self.topology.remove_edge(u, v)
            except Exception:
                pass

    def restore_link(self, u, v, **attrs):
        if not self.topology.has_edge(u, v):
            attrs = attrs or {"bandwidth_mbps":1000}
            self.topology.add_edge(u, v, **attrs)
        self.logger.info(f"Link restored: {u} <-> {v}")

    def stop(self):
        for nw in self.node_threads.values():
            nw.stop()
        try:
            if self._server_socket:
                self._server_socket.close()
        except Exception:
            pass
        self.logger.info("Simulation stopped")
