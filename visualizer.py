
import logging
from rich.console import Console
from rich.tree import Tree

logger = logging.getLogger(__name__)

def print_terminal_graph(nodes, edges):
    console = Console(force_terminal=True, width=100)
    root_tree = Tree("[bold blue]Dependency Graph")

    # Helper: Build a map of ParentID -> [Children Nodes]
    # We use the 'parent_id' field in Node for containment (Class contains Method)
    # We use edges for calls
    
    # 1. Nesting Structure (Files -> Classes -> Methods)
    # We can iterate through files first.
    
    logger.info(f"Total nodes: {len(nodes)}")
    files = [n for n in nodes.values() if n.type.name == "FILE"]
    logger.info(f"Files found: {len(files)}")
    
    for file_node in files:
        file_tree = root_tree.add(f"[green]📄 {file_node.name}")
        
        # Find children of this file (Classes/Interfaces)
        file_children = [n for n in nodes.values() if n.parent_id == file_node.id]
        
        for child in file_children:
            icon = "Ⓒ" if child.type.name == "CLASS" else "Ⓘ"
            class_tree = file_tree.add(f"[cyan]{icon} {child.name}")
            
            # Find methods in this class
            methods = [n for n in nodes.values() if n.parent_id == child.id]
            for method in methods:
                method_text = f"[yellow]ƒ {method.name}"
                method_tree = class_tree.add(method_text)
                
                # Check for outgoing edges from this method
                outgoing_edges = [e for e in edges if e.source == method.id]
                for edge in outgoing_edges:
                    target_node = nodes.get(edge.target)
                    if target_node:
                        # Format: -> TargetClass::TargetMethod
                        # We try to get a cleaner name
                        target_name = target_node.name
                        # Try to find parent class of target
                        parent = nodes.get(target_node.parent_id)
                        if parent:
                            target_name = f"{parent.name}.{target_name}"
                        
                        method_tree.add(f"[red]⮑ calls {target_name}")

    with console.capture() as capture:
        console.print(root_tree)
    
    import sys
    
    try:
        # Try to reconfigure stdout to utf-8 if possible
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        print(capture.get())
    except UnicodeEncodeError:
        # Fallback: print a simplified message if encoding fails
        logger.error("Graph visualization could not be printed due to encoding issues.")
        logger.info(f"Total nodes: {len(nodes)}, Total edges: {len(edges)}")
