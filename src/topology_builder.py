
import ipaddress
import networkx as nx
import logging
from typing import Dict, Any, Tuple

class TopologyBuilder:
    """
    Build a topology from parsed Cisco configs.
    Adds nodes with metadata and edges when interfaces share a subnet
    or when interface descriptions reference another device.
    Also assigns hierarchical layers: core, distribution, access, endpoint.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def build_from_configs(self, configs: Dict[str, Dict[str, Any]]) -> nx.Graph:
        G = nx.Graph()
        # Add nodes
        for key, cfg in configs.items():
            # parser output may either be the parsed_config directly or nested
            p = cfg.get("parsed_config") if isinstance(cfg, dict) and "parsed_config" in cfg else cfg
            hostname = p.get("hostname", key) if isinstance(p, dict) else key
            device_type = (p.get("device_type") or "router").lower() if isinstance(p, dict) else "router"
            G.add_node(key, label=f"{hostname}", device_type=device_type, title=self._make_title(p) if isinstance(p, dict) else "")
        # Add edges by same subnet
        self._add_subnet_edges(G, configs)
        # Add edges by description hints
        self._add_description_edges(G, configs)
        # Compute simple link bandwidth annotations and determine layers
        for u, v in G.edges():
            if "bandwidth_mbps" not in G[u][v]:
                G[u][v]["bandwidth_mbps"] = 1000
            if "link_type" not in G[u][v]:
                G[u][v]["link_type"] = "subnet"
            G[u][v]["title"] = f"{G[u][v]['link_type']} | {G[u][v]['bandwidth_mbps']} Mbps"

        self._assign_layers(G, configs)
        return G

    def _make_title(self, p: Dict[str, Any]) -> str:
        dt = (p.get("device_type") or "router").upper()
        ints = p.get("interfaces", []) if isinstance(p, dict) else []
        mtu_set = {i.get("mtu") for i in ints if i.get("mtu")}
        return f"{dt} | interfaces: {len(ints)} | MTUs: {', '.join(map(str, mtu_set)) if mtu_set else 'default'}"

    def _iter_intfs(self, p: Dict[str, Any]):
        for i in p.get("interfaces", []):
            ipaddr = i.get("ip_address")
            mask = i.get("subnet_mask")
            if ipaddr and mask:
                try:
                    network = ipaddress.ip_interface(f"{ipaddr}/{mask}").network
                except Exception:
                    network = None
            else:
                network = None
            yield i, network

    def _add_subnet_edges(self, G: nx.Graph, configs: Dict[str, Dict[str, Any]]):
        # Map network -> list[(device, iface)]
        net_map = {}
        for dev, cfg in configs.items():
            p = cfg.get("parsed_config") if isinstance(cfg, dict) and "parsed_config" in cfg else cfg
            if not isinstance(p, dict):
                continue
            for iface, net in self._iter_intfs(p):
                if net is None:
                    continue
                net_map.setdefault(str(net), []).append((dev, iface))
        for net, members in net_map.items():
            for i in range(len(members)):
                for j in range(i+1, len(members)):
                    u, _ = members[i]; v, _ = members[j]
                    if u == v:
                        continue
                    if not G.has_edge(u, v):
                        G.add_edge(u, v, link_type="subnet", subnet=net, bandwidth_mbps=1000)

    def _add_description_edges(self, G: nx.Graph, configs: Dict[str, Dict[str, Any]]):
        hostnames = set(configs.keys())
        for dev, cfg in configs.items():
            p = cfg.get("parsed_config") if isinstance(cfg, dict) and "parsed_config" in cfg else cfg
            if not isinstance(p, dict):
                continue
            for iface in p.get("interfaces", []):
                desc = (iface.get("description") or "").strip()
                for other in hostnames:
                    if other != dev and other in desc and not G.has_edge(dev, other):
                        G.add_edge(dev, other, link_type="desc", bandwidth_mbps=1000)

    def _assign_layers(self, G: nx.Graph, configs: Dict[str, Dict[str, Any]]):
        # Simple heuristics:
        # - Devices with BGP or degree >=4 -> core
        # - Routers with degree 2-3 -> distribution
        # - Switches -> access
        # - PCs/endpoints -> endpoint
        for n, d in G.nodes(data=True):
            cfg = configs.get(n, {})
            p = cfg.get("parsed_config") if isinstance(cfg, dict) and "parsed_config" in cfg else cfg
            dtype = (d.get("device_type") or "").lower()
            has_bgp = False
            if isinstance(p, dict):
                rt = p.get("routing", {})
                if isinstance(rt, dict):
                    has_bgp = bool(rt.get("bgp") or rt.get("has_bgp"))
            deg = G.degree[n]
            if has_bgp or deg >= 4:
                layer = "core"
            elif dtype == "switch":
                layer = "access"
            elif dtype == "pc":
                layer = "endpoint"
            elif 2 <= deg <= 3:
                layer = "distribution"
            else:
                layer = "distribution"
            G.nodes[n]["layer"] = layer
