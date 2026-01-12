
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional

class NodeType(Enum):
    FILE = "FILE"
    CLASS = "CLASS"
    INTERFACE = "INTERFACE"
    METHOD = "METHOD"

@dataclass
class Node:
    id: str  
    type: NodeType
    name: str
    metadata: Dict = field(default_factory=dict)
    # New fields for linking
    file_path: Optional[str] = None
    parent_id: Optional[str] = None

@dataclass
class Edge:
    source: str 
    target: str 
    relation: str 
