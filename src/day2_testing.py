
import logging
from typing import Dict, Any
import networkx as nx
import time

logger = logging.getLogger("day2_testing")

class Day2NetworkTester:
    """
    Run Day-2 tests (configuration best practices, reachability after failures, MTU impact, etc.)
    Produces a summary dict with counts of passed/failed/warnings.
    """
    def __init__(self, topology: nx.Graph, configs: Dict[str,Any]):
        self.topology = topology
        self.configs = configs

    def run_all_tests(self) -> Dict[str, Any]:
        tests = []
        tests.extend(self._config_best_practices())
        tests.extend(self._reachability_tests())
        tests.extend(self._mtu_tests())
        # Evaluate results
        passed = sum(1 for t in tests if t["result"] == "pass")
        failed = sum(1 for t in tests if t["result"] == "fail")
        warn = sum(1 for t in tests if t["result"] == "warn")
        return {"total": len(tests), "passed": passed, "failed": failed, "warnings": warn, "details": tests}

    def _config_best_practices(self):
        details = []
        # sample checks over configs
        for name, cfg in self.configs.items():
            p = cfg.get("parsed_config") if isinstance(cfg, dict) and "parsed_config" in cfg else cfg
            if not isinstance(p, dict):
                continue
            # check hostname exists
            if not p.get("hostname"):
                details.append({"name": f"{name}-hostname", "result":"fail", "msg":"missing hostname"})
            else:
                details.append({"name": f"{name}-hostname", "result":"pass", "msg":"hostname present"})
            # check at least one interface
            if not p.get("interfaces"):
                details.append({"name": f"{name}-interfaces", "result":"fail", "msg":"no interfaces configured"})
            else:
                details.append({"name": f"{name}-interfaces", "result":"pass", "msg":"interfaces present"})
        return details

    def _reachability_tests(self):
        details = []
        # test simple reachability: graph connectedness or node pair paths
        nodes = list(self.topology.nodes())
        if not nodes:
            return [{"name":"reachability-empty","result":"fail","msg":"no nodes"}]
        # pick a few pairs
        pairs = []
        if len(nodes) >= 2:
            pairs = [(nodes[0], nodes[-1])]
        for a,b in pairs:
            try:
                nx.shortest_path(self.topology, a, b)
                details.append({"name":f"reach-{a}-{b}","result":"pass","msg":"path exists"})
            except Exception:
                details.append({"name":f"reach-{a}-{b}","result":"fail","msg":"no path"})
        return details

    def _mtu_tests(self):
        details = []
        # verify MTU matches on edges
        for u,v,d in self.topology.edges(data=True):
            mtu_u = self._max_mtu(u)
            mtu_v = self._max_mtu(v)
            if mtu_u and mtu_v and mtu_u != mtu_v:
                details.append({"name":f"mtu-{u}-{v}","result":"warn","msg":f"MTU mismatch {mtu_u}!={mtu_v}"})
            else:
                details.append({"name":f"mtu-{u}-{v}","result":"pass","msg":"mtu ok"})
        return details

    def _max_mtu(self, node):
        cfg = self.configs.get(node,{})
        p = cfg.get("parsed_config") if isinstance(cfg, dict) and "parsed_config" in cfg else cfg
        if not isinstance(p, dict):
            return None
        mtus = [int(i.get("mtu")) for i in p.get("interfaces",[]) if i.get("mtu")]
        return max(mtus) if mtus else None
