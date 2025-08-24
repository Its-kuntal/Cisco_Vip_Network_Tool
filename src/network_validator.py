
import logging
import networkx as nx
from typing import Dict, Any, List, Set

class NetworkValidator:
    """
    Enhanced validator that performs:
    - missing component detection (endpoint -> access switch)
    - duplicate IP detection
    - VLAN consistency checks (basic)
    - gateway presence checks
    - MTU mismatch detection on edges
    - network loop detection
    - aggregation opportunity detection (coalescing multiple endpoints)
    """
    def __init__(self, configs: Dict[str, Dict], topology: nx.Graph):
        self.logger = logging.getLogger(__name__)
        self.configs = configs
        self.topology = topology

    def validate_all(self) -> Dict[str, Any]:
        return {
            "missing_components": self._check_missing_components(),
            "duplicate_ips": self._check_duplicate_ips(),
            "vlan_issues": self._check_vlan_consistency(),
            "gateway_issues": self._check_gateways(),
            "routing_recommendations": self._routing_recommendations(),
            "mtu_mismatches": self._check_mtu_mismatches(),
            "network_loops": self._detect_loops(),
            "aggregation_opportunities": self._aggregation_opportunities(),
        }

    def _check_missing_components(self) -> List[str]:
        """Detect endpoints (pc) that are not connected to a 'switch' in topology or missing switch configs"""
        issues = []
        for node, data in self.topology.nodes(data=True):
            dtype = data.get("device_type","").lower()
            if dtype == "pc":
                neighbors = list(self.topology.neighbors(node))
                if not neighbors:
                    issues.append(f"PC {node} appears to be isolated (no neighbors)")
                else:
                    # expect at least one neighbor to be a switch
                    if not any(self.topology.nodes[n].get("device_type","").lower()=="switch" for n in neighbors):
                        issues.append(f"PC {node} not connected to an access switch")
        return issues

    def _check_duplicate_ips(self) -> List[str]:
        ip_map = {}
        issues = []
        for name, cfg in self.configs.items():
            p = cfg.get("parsed_config") if isinstance(cfg, dict) and "parsed_config" in cfg else cfg
            if not isinstance(p, dict):
                continue
            for iface in p.get("interfaces", []):
                ip = iface.get("ip_address")
                if not ip:
                    continue
                ip_map.setdefault(ip, []).append((name, iface.get("name")))
        for ip, owners in ip_map.items():
            if len(owners) > 1:
                issues.append(f"IP {ip} used by: {', '.join(f'{n}/{i}' for n,i in owners)}")
        return issues

    def _check_vlan_consistency(self) -> List[str]:
        # Basic VLAN ID mismatches for endpoints on same subnet
        issues = []
        subnet_vlans = {}
        for name, cfg in self.configs.items():
            p = cfg.get("parsed_config") if isinstance(cfg, dict) and "parsed_config" in cfg else cfg
            if not isinstance(p, dict):
                continue
            for iface in p.get("interfaces", []):
                net = iface.get("subnet")
                vlan = iface.get("vlan")
                if net and vlan:
                    subnet_vlans.setdefault(net, set()).add(vlan)
        for net, vlans in subnet_vlans.items():
            if len(vlans) > 1:
                issues.append(f"Subnet {net} has multiple VLANs configured: {sorted(vlans)}")
        return issues

    def _check_gateways(self) -> List[str]:
        issues = []
        # If a PC has a gateway configured check it's reachable in topology (basic)
        for name, cfg in self.configs.items():
            p = cfg.get("parsed_config") if isinstance(cfg, dict) and "parsed_config" in cfg else cfg
            if not isinstance(p, dict):
                continue
            if p.get("device_type","").lower() == "pc":
                for iface in p.get("interfaces", []):
                    gw = iface.get("gateway")
                    if gw:
                        # check if gateway IP is present on any interface in configs
                        found = False
                        for other, ocfg in self.configs.items():
                            op = ocfg.get("parsed_config") if isinstance(ocfg, dict) and "parsed_config" in ocfg else ocfg
                            if not isinstance(op, dict):
                                continue
                            for oiface in op.get("interfaces", []):
                                if oiface.get("ip_address") == gw:
                                    found = True
                                    break
                            if found:
                                break
                        if not found:
                            issues.append(f"PC {name} gateway {gw} not found on any device")
        return issues

    def _check_mtu_mismatches(self) -> List[str]:
        issues = []
        for u, v, data in self.topology.edges(data=True):
            mtu_u = self._max_mtu(u)
            mtu_v = self._max_mtu(v)
            if mtu_u and mtu_v and mtu_u != mtu_v:
                issues.append(f"MTU mismatch between {u} ({mtu_u}) and {v} ({mtu_v})")
        return issues

    def _max_mtu(self, node: str):
        cfg = self.configs.get(node, {})
        p = cfg.get("parsed_config") if isinstance(cfg, dict) and "parsed_config" in cfg else cfg
        if not isinstance(p, dict):
            return None
        mtus = [int(i.get("mtu")) for i in p.get("interfaces", []) if i.get("mtu")]
        return max(mtus) if mtus else None

    def _detect_loops(self) -> List[str]:
        issues = []
        try:
            cycles = list(nx.simple_cycles(self.topology.to_directed()))
            for cyc in cycles:
                issues.append(" -> ".join(cyc))
        except Exception:
            # fallback: attempt undirected cycle detection
            if nx.cycle_basis(self.topology):
                for cyc in nx.cycle_basis(self.topology):
                    issues.append(" -> ".join(cyc))
        return issues

    def _routing_recommendations(self) -> List[str]:
        recs = []
        # Suggest BGP for devices that look like edges to the internet (has 'bgp' in routing)
        for name, cfg in self.configs.items():
            p = cfg.get("parsed_config") if isinstance(cfg, dict) and "parsed_config" in cfg else cfg
            if not isinstance(p, dict):
                continue
            rt = p.get("routing", {})
            if isinstance(rt, dict) and rt.get("bgp"):
                recs.append(f"Device {name} has BGP configuration present")
        return recs

    def _aggregation_opportunities(self) -> List[str]:
        recs = []
        # Simple heuristic: nodes with many endpoints could be aggregated
        for n in self.topology.nodes():
            deg = self.topology.degree[n]
            if deg >= 4 and self.topology.nodes[n].get("device_type","")=="switch":
                recs.append(f"Switch {n} has degree {deg} - consider aggregation or stack")
        return recs
