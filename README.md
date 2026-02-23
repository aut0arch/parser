# Walkthrough - Java Semantic Repo Parser

We have successfully built a Python-based tool that parses Java repositories and generates a semantic dependency graph using **Tree-sitter**.

## Features
1.  **Strict Parsing**: Uses `tree-sitter-java` to parse files efficiently.
2.  **Symbol Discovery**: Identifies Files, Classes, Interfaces, and Methods.
3.  **Fuzzy Linking**: Connects method calls to their definitions (Cross-file resolution).
4.  **Visualization**: Renders a beautiful tree view in the terminal using `rich`.

## Installation & Setup

### Method 1: Docker Compose (Recommended)

To run the parser seamlessly as part of the full application stack without installing `tree-sitter` and C compilers on your host machine, run this command from the **root directory** of the repository:

```bash
docker-compose up --build -d
```
The parser runs as an internal orchestrator task when processing a repository from the frontend UI.

### Method 2: Local Usage

To use the parser standalone natively:
1. Ensure Python 3.10+ and a C compiler (e.g. `build-essential` or `Xcode Command Line Tools`) are installed (required for compiling Tree-sitter bindings).
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the parser on any directory containing `.java` files:

```bash
python parser.py <directory> [--json output.json] [--dot output.dot]
```

### Export Options
*   `--json <path>`: Saves the semantic graph as a JSON file.
*   `--dot <path>`: Saves the semantic graph as a Graphviz DOT file.

## Example Verification
We created a test repository in `./tests` with:
*   `UserManager.java` (calls `Helper.validate`)
*   `Helper.java` (defines `validate`)

Running the parser with exports:
```bash
python parser.py ./tests --json graph.json --dot graph.dot
```

### Output
The tool correctly identifies the structure and the call dependency:

```text
Dependency Graph
├── 📄 UserManager.java
│   └── Ⓒ UserManager
│       └── ƒ createUser
│           └── ⮑ calls Helper.validate
└── 📄 Helper.java
    └── Ⓒ Helper
        └── ƒ validate
```

## Code Structure
*   `parser.py`: Main logic. Uses `tree-sitter` (v0.25+) with `QueryCursor` for extracting symbols. Implements a 2-pass strategy (Discovery -> Linking).
*   `visualizer.py`: Handles terminal output using `rich.Tree`.
*   `requirements.txt`: Dependencies (`tree-sitter`, `tree-sitter-java`, `rich`).
