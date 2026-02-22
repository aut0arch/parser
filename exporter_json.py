
import json
import logging
import dataclasses
from typing import Dict, List
from models import Node, Edge, NodeType

logger = logging.getLogger(__name__)

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, NodeType):
            return o.value
        return super().default(o)

def export_to_json(nodes: Dict[str, Node], edges: List[Edge], output_path: str):
    data = {
        "nodes": list(nodes.values()),
        "edges": edges
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, cls=EnhancedJSONEncoder, indent=2)
    
    logger.info(f"JSON export saved to {output_path}")
