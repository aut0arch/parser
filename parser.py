
import os
import sys
import logging
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_java as tsjava

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from models import Node, Edge, NodeType

# Initialize Tree-sitter
JAVA_LANGUAGE = Language(tsjava.language())
parser = Parser(JAVA_LANGUAGE)

class JavaGraphBuilder:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        # Index for fuzzy linking: ShortName -> List[NodeID]
        self.symbol_index: Dict[str, List[str]] = {}

    def add_node(self, node: Node):
        self.nodes[node.id] = node
        # Add to index
        if node.name not in self.symbol_index:
            self.symbol_index[node.name] = []
        self.symbol_index[node.name].append(node.id)

    def add_edge(self, source: str, target: str, relation: str):
        self.edges.append(Edge(source, target, relation))

    def build_graph(self):
        logger.info(f"Scanning {self.root_dir}...")
        self._pass1_discovery()
        self._pass2_linking()
        
        logger.info(f"Graph built: {len(self.nodes)} nodes, {len(self.edges)} edges.")
        return self.nodes, self.edges

    def _pass1_discovery(self):
        """Walks files, parses them, and records definitions."""
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(".java"):
                    file_path = os.path.join(root, file)
                    self._process_file_pass1(file_path)

    def _process_file_pass1(self, file_path: str):
        try:
            with open(file_path, "rb") as f:
                source_code = f.read()
            
            tree = parser.parse(source_code)
            root_node = tree.root_node
            
            # Create File Node
            file_id = file_path
            self.add_node(Node(file_id, NodeType.FILE, os.path.basename(file_path), file_path=file_path))

            # Query for definitions
            query_scm = """
                (class_declaration name: (identifier) @class.name) @class.def
                (interface_declaration name: (identifier) @interface.name) @interface.def
                (method_declaration name: (identifier) @method.name) @method.def
            """
            query_scm = """
                (class_declaration name: (identifier) @class.name) @class.def
                (interface_declaration name: (identifier) @interface.name) @interface.def
                (method_declaration name: (identifier) @method.name) @method.def
            """
            query = Query(JAVA_LANGUAGE, query_scm)
            
            # Use QueryCursor for Tree-sitter 0.25+
            cursor = QueryCursor(query)
            matches = cursor.matches(root_node)
            
            for pattern_index, captures_dict in matches:
                for tag, nodes in captures_dict.items():
                    # nodes is a list of Node objects
                    if not isinstance(nodes, list):
                        nodes = [nodes]
                    
                    for node in nodes:
                        if tag == "class.name":
                            class_name = source_code[node.start_byte:node.end_byte].decode("utf8")
                            class_id = f"{file_path}::{class_name}"
                            
                            self.add_node(Node(
                                id=class_id,
                                type=NodeType.CLASS,
                                name=class_name,
                                file_path=file_path,
                                parent_id=file_id
                            ))
                            self.add_edge(file_id, class_id, "CONTAINS")

                        elif tag == "interface.name":
                            interface_name = source_code[node.start_byte:node.end_byte].decode("utf8")
                            interface_id = f"{file_path}::{interface_name}"
                            
                            self.add_node(Node(
                                id=interface_id,
                                type=NodeType.INTERFACE,
                                name=interface_name,
                                file_path=file_path,
                                parent_id=file_id
                            ))
                            self.add_edge(file_id, interface_id, "CONTAINS")

                        elif tag == "method.name":
                            method_name = source_code[node.start_byte:node.end_byte].decode("utf8")
                            # Find parent class/interface
                            parent = node.parent
                            while parent and parent.type not in ("class_declaration", "interface_declaration", "file"):
                                parent = parent.parent
                            
                            parent_name = "Unknown"
                            if parent and parent.child_by_field_name("name"):
                                parent_name_node = parent.child_by_field_name("name")
                                parent_name = source_code[parent_name_node.start_byte:parent_name_node.end_byte].decode("utf8")
                            
                            if parent_name == "Unknown":
                                continue

                            parent_id = f"{file_path}::{parent_name}"
                            method_id = f"{parent_id}::{method_name}"

                            self.add_node(Node(
                                id=method_id,
                                type=NodeType.METHOD,
                                name=method_name,
                                file_path=file_path,
                                parent_id=parent_id
                            ))
                            self.add_edge(parent_id, method_id, "CONTAINS")

        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            import traceback
            traceback.print_exc()

    def _pass2_linking(self):
        """Re-visits files to resolve dependencies (function calls)."""
        logger.info("Starting Pass 2: Linking...")
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(".java"):
                    file_path = os.path.join(root, file)
                    self._process_file_pass2(file_path)

    def _process_file_pass2(self, file_path: str):
        try:
            with open(file_path, "rb") as f:
                source_code = f.read()
            
            tree = parser.parse(source_code)
            root_node = tree.root_node
            
            query_scm = """
                (method_invocation 
                    object: (identifier)? @call.object
                    name: (identifier) @call.name
                ) @call.node
            """
            query = Query(JAVA_LANGUAGE, query_scm)

            cursor = QueryCursor(query)
            matches = cursor.matches(root_node)
            
            for pattern_index, captures_dict in matches:
                for tag, nodes in captures_dict.items():
                    if not isinstance(nodes, list):
                        nodes = [nodes]
                    for node in nodes:
                        if tag == "call.name":
                            call_name = source_code[node.start_byte:node.end_byte].decode("utf8")
                            
                            # Find the scope
                            scope = node.parent
                            source_method_name = "Unknown"
                            source_class_name = "Unknown"
                            
                            while scope:
                                if scope.type == "method_declaration":
                                    name_node = scope.child_by_field_name("name")
                                    if name_node:
                                        source_method_name = source_code[name_node.start_byte:name_node.end_byte].decode("utf8")
                                elif scope.type == "class_declaration":
                                    name_node = scope.child_by_field_name("name")
                                    if name_node:
                                        source_class_name = source_code[name_node.start_byte:name_node.end_byte].decode("utf8")
                                    break 
                                scope = scope.parent
                            
                            if source_method_name == "Unknown":
                                continue

                            source_id = f"{file_path}::{source_class_name}::{source_method_name}"
                            
                            object_name = None
                            parent = node.parent # invocation node
                            object_node = parent.child_by_field_name("object")
                            if object_node:
                                object_name = source_code[object_node.start_byte:object_node.end_byte].decode("utf8")
                            
                            target_candidates = []
                            
                            if object_name:
                                if object_name in self.symbol_index:
                                    possible_class_ids = self.symbol_index[object_name]
                                    for class_id in possible_class_ids:
                                        target_id = f"{class_id}::{call_name}"
                                        if target_id in self.nodes:
                                            target_candidates.append(target_id)
                            else:
                                current_class_id = f"{file_path}::{source_class_name}"
                                target_id = f"{current_class_id}::{call_name}"
                                if target_id in self.nodes:
                                    target_candidates.append(target_id)
                            
                            for match_id in target_candidates:
                                self.add_edge(source_id, match_id, "CALLS")
                        
        except Exception as e:
            logger.error(f"Error processing {file_path} in Pass 2: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    import argparse
    import visualizer
    import exporter_json
    import exporter_dot

    cli_parser = argparse.ArgumentParser(description="Java Semantic Parser")
    cli_parser.add_argument("directory", help="Path to Java source directory")
    cli_parser.add_argument("--json", help="Path to save JSON output")
    cli_parser.add_argument("--dot", help="Path to save DOT output")
    
    args = cli_parser.parse_args()
    
    builder = JavaGraphBuilder(args.directory)
    nodes, edges = builder.build_graph()
    
    # Always print terminal visualization
    visualizer.print_terminal_graph(nodes, edges)
    
    if args.json:
        exporter_json.export_to_json(nodes, edges, args.json)
        
    if args.dot:
        exporter_dot.export_to_dot(nodes, edges, args.dot)
