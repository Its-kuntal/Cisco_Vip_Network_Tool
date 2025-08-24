
import networkx as nx
from pathlib import Path
import datetime

class TopologyRenderer:
    def render(self, graph: nx.Graph, output_dir: Path) -> str:
        """Render topology as an interactive Vis-Network HTML file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir.mkdir(parents=True, exist_ok=True)
        out_file = output_dir / f"network_topology_{timestamp}.html"

        nodes = []
        edges = []
        for node in graph.nodes():
            nodes.append({"id": node, "label": node})
        for u, v, data in graph.edges(data=True):
            edges.append({
                "from": u,
                "to": v,
                "label": data.get("link_type", ""),
                "title": f"bw={data.get('bandwidth','')}"
            })

        html = f"""
        <html>
        <head>
            <script type="text/javascript" src="lib/vis-9.1.2/vis-network.min.js"></script>
            <link rel="stylesheet" href="lib/vis-9.1.2/vis-network.min.css"/>
        </head>
        <body>
            <div id="mynetwork" style="width:100%; height:800px; border:1px solid lightgray;"></div>
            <script type="text/javascript">
                var nodes = new vis.DataSet({nodes});
                var edges = new vis.DataSet({edges});
                var container = document.getElementById('mynetwork');
                var data = {{nodes:nodes, edges:edges}};
                var options = {{}};
                var network = new vis.Network(container, data, options);
            </script>
        </body>
        </html>
        """

        out_file.write_text(html)
        return str(out_file)
