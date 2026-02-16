# Codebase Explanation: Java Semantic Graph Parser

This project is a Python-based tool designed to parse a Java repository and generate a semantic dependency graph. It uses **tree-sitter** for robust parsing and implements a fuzzy linking strategy to resolve cross-file dependencies (function calls) without requiring a full build environment.

## 1. Project Structure

The codebase is organized into the following key components:

- **`models.py`**: Defines the data structures for the graph (Nodes, Edges).
- **`parser.py`**: The core logic. Handles file scanning, parsing (via tree-sitter), and graph building (2-pass strategy).
- **`visualizer.py`**: Provides a terminal-based visualization of the dependency graph using the `rich` library.
- **`exporter_dot.py`** & **`exporter_json.py`**: Modules for exporting the graph to Graphviz DOT and JSON formats, respectively.

---

## 2. Detailed Component Breakdown

### A. Data Models (`models.py`)

This file defines the schema for the semantic graph.

- **`NodeType` (Enum)**:
  - `FILE`: Represents a Java source file.
  - `CLASS`: Represents a class definition.
  - `INTERFACE`: Represents an interface definition.
  - `METHOD`: Represents a method definition.

- **`Node` (Dataclass)**:
  - `id`: Unique identifier (e.g., `path/to/File.java::ClassName::MethodName`).
  - `type`: `NodeType` enum.
  - `name`: Human-readable name (e.g., `main`, `UserManager`).
  - `file_path`: Origin file.
  - `parent_id`: ID of the containing node (e.g., a method's parent is its class).

- **`Edge` (Dataclass)**:
  - `source`: ID of the caller/container.
  - `target`: ID of the callee/child.
  - `relation`: Relationship type (`CONTAINS` for structure, `CALLS` for invocation).

### B. The Parser (`parser.py`)

This is the brain of the application. It uses `tree-sitter-java` to parse code into an Abstract Syntax Tree (AST). The parsing process is divided into **two passes**.

#### Initialization
- Sets up the Tree-sitter `JAVA_LANGUAGE`.
- Initializes a `JavaGraphBuilder` with a root directory.
- Maintains a `symbol_index` (Dictionary: `ShortName -> List[NodeID]`) to help with fuzzy linking.

#### Pass 1: Discovery (`_pass1_discovery`)
**Goal**: Identify all definitions (Files, Classes, Interfaces, Methods) and build the structural backbone of the graph.

1.  **File Walk**: Recursively finds all `.java` files.
2.  **Tree-sitter Query**: Uses an S-expression query to find declarations:
    - `class_declaration`
    - `interface_declaration`
    - `method_declaration`
3.  **Node Creation**:
    - Creates a `Node` for each match.
    - Generates a unique ID based on the file path and containment hierarchy.
    - Adds a `CONTAINS` edge from the parent (File or Class) to the child.
4.  **Indexing**: Adds the node's name (e.g., `validate`) to `symbol_index` for later lookup.

#### Pass 2: Linking (`_pass2_linking`)
**Goal**: Find method calls and resolve them to the definitions found in Pass 1.

1.  **Re-parse**: Scans files again to look for usage.
2.  **Tree-sitter Query**: Finds `method_invocation` nodes.
3.  **Resolution Strategy**:
    - Extracts the `call.name` (method being called) and optional `call.object` (the variable/class calling it).
    - **Fuzzy Match**:
        - If an object is specified (e.g., `helper.validate()`), it looks up `helper` (or inferred class type) in the symbol index to find candidates.
        - If no object is specified (e.g., `validate()`), it assumes a method in the current class or inherited (simplified logic).
    - **Edge Creation**: Adds a `CALLS` edge from the current method (Source) to the resolved target method ID (Target).

### C. Visualization (`visualizer.py`)

Uses the `rich` library to render a hierarchical tree in the terminal.
1.  **Grouping**: Starts with Files, then nests Classes, then Methods.
2.  **Edges**: For each method, it lists outgoing calls (red arrows `⮑`) underneath the method definition.

### D. Exporters (`exporter_*.py`)

- **DOT Export**: Group nodes by file using "subgraphs" (clusters) for visual grouping in tools like Graphviz. Useful for generating images.
- **JSON Export**: Dumps the raw Node and Edge data to JSON for use in other tools or web frontends. Uses a custom encoder to handle dataclasses and Enums.

---

## 3. Key Dependencies

- **`tree-sitter`**: The underlying parsing engine. Fast and incremental.
- **`tree-sitter-java`**: Grammar for Java.
- **`rich`**: For pretty terminal output.

## 4. Execution Flow

1.  **CLI Entry**: `parser.py` is executed with a target directory.
2.  **Build**: `JavaGraphBuilder` runs Pass 1 (definitions) then Pass 2 (calls).
3.  **Output**:
    - Prints the text-based graph to the console.
    - Optionally writes `.json` or `.dot` files if flags are provided.
