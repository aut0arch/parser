
import logging
from typing import Dict, List
from models import Node, Edge, NodeType

logger = logging.getLogger(__name__)

def export_to_dot(nodes: Dict[str, Node], edges: List[Edge], output_path: str):
    """
    Generates a DOT file for Graphviz.
    We'll separate subgraphs by File to keep it organized.
    """
    
    lines = ["digraph G {", "  rankdir=LR;", "  node [shape=box style=filled fillcolor=lightgray];"]
    
    # Group nodes by File
    files = {} # file_path -> [nodes]
    
    for node in nodes.values():
        if node.type == NodeType.FILE:
            if node.id not in files:
                files[node.id] = []
        else:
            # Find root file for this node if possible
            # Simplified: Use file_path field
            if node.file_path:
                if node.file_path not in files:
                    files[node.file_path] = []
                files[node.file_path].append(node)
    
    # Write Subgraphs
    cluster_idx = 0
    for file_path, file_nodes in files.items():
        lines.append(f"  subgraph cluster_{cluster_idx} {{")
        lines.append(f"    label=\"{file_path}\";")
        lines.append("    style=dashed;")
        lines.append("    color=blue;")
        
        file_node_id = f"\"{file_path}\""
        lines.append(f"    {file_node_id} [label=\"{file_path}\" shape=folder fillcolor=gold];")
        
        for node in file_nodes:
            # Escape quotes in ID / Name
            clean_id = node.id.replace('"', '\\"')
            clean_name = node.name.replace('"', '\\"')
            
            color = "white"
            if node.type == NodeType.CLASS: color = "lightblue"
            elif node.type == NodeType.METHOD: color = "lightgreen"
            elif node.type == NodeType.INTERFACE: color = "lightyellow"

            lines.append(f"    \"{clean_id}\" [label=\"{clean_name}\" fillcolor={color}];")
            
        lines.append("  }")
        cluster_idx += 1

    # Write Edges
    for edge in edges:
        src = edge.source.replace('"', '\\"')
        tgt = edge.target.replace('"', '\\"')
        lines.append(f"  \"{src}\" -> \"{tgt}\" [label=\"{edge.relation}\"];")

    lines.append("}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
        
    logger.info(f"DOT export saved to {output_path}")
