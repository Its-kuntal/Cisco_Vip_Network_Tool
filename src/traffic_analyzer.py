from typing import Dict, Any
import networkx as nx

class TrafficAnalyzer:
    def __init__(self, topology: nx.Graph, configs: Dict[str,Any]):
        self.topology = topology
        self.configs = configs

    def analyze(self) -> Dict[str, Any]:
        results = {"link_utilization": {}, "bottlenecks": [], "load_balancing_recommendations": []}
        for u,v,d in self.topology.edges(data=True):
            cap = d.get("bandwidth_mbps", 1000)
            est = (self.topology.degree[u] + self.topology.degree[v]) * 10.0
            util = min(100.0, est*100.0/cap if cap else 0.0)
            key = f"{u}-{v}"
            results["link_utilization"][key] = {
                "capacity_mbps": cap,
                "estimated_traffic_mbps": est,
                "utilization_percent": util,
                "link_type": d.get("link_type","unknown")
            }
            if util > 80.0:
                results["bottlenecks"].append({"link": key, "utilization_percent": util, "severity": "warning" if util<=95 else "critical"})
        for b in results["bottlenecks"]:
            results["load_balancing_recommendations"].append(f"Consider upgrade or ECMP for {b['link']} (util {b['utilization_percent']:.1f}%)")
        return results
