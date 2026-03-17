import os
import json
import subprocess

# ============================================================
# CONFIGURATION
# ============================================================
# The main file containing the full subtree structure
ROOT_SUBTREE_FILE = r"query_output/query_output_subtree_body-parser_1.20.2.json"

# Directory patterns
DB_DIR = "query_output"
TOOL_DIR = "tool_output"
RESULT_DIR = "compare_result"

def extract_dependencies(node, deps=None):
    """
    Recursively crawls the JSON tree to find all unique (name, version) pairs.
    """
    if deps is None:
        deps = set()
    
    name = node.get("name")
    version = node.get("version")
    
    if name and version:
        deps.add((name, version))
    
    for child in node.get("children", []):
        extract_dependencies(child, deps)
    
    return deps

def run_comparisons():
    # 1. Load the main subtree file to know what to compare
    if not os.path.exists(ROOT_SUBTREE_FILE):
        print(f"ERROR: Root subtree file not found: {ROOT_SUBTREE_FILE}")
        return

    with open(ROOT_SUBTREE_FILE, "r", encoding="utf-8") as f:
        root_data = json.load(f)

    # 2. Get all unique components in the tree
    dependencies = extract_dependencies(root_data)
    print(f"Found {len(dependencies)} unique components to compare.\n")

    # 3. Ensure result directory exists
    os.makedirs(RESULT_DIR, exist_ok=True)

    # 4. Iterate and compare
    for name, version in dependencies:
        db_file = os.path.join(DB_DIR, f"query_output_subtree_{name}_{version}.json")
        tool_file = os.path.join(TOOL_DIR, f"tool_output_subtree_{name}_{version}.json")
        result_file = os.path.join(RESULT_DIR, f"compare_result_subtree_{name}_{version}.json")
        
        print(f"Checking: {name}@{version}")

        # Check if both files exist before trying to compare
        if not os.path.exists(db_file):
            print(f"  SKIPPING: Database file missing -> {db_file}")
            continue
        if not os.path.exists(tool_file):
            print(f"  SKIPPING: Tool file missing -> {tool_file}")
            continue

        # Construct command to run the existing compare_subtree.py
        # This reuses your existing logic and report generation
        cmd = [
            "python", "compare_subtree.py", 
            db_file, 
            tool_file,
            result_file
        ]

        try:
            # Run the comparison script as a subprocess
            # We don't capture output so you can see the reports in the console
            subprocess.run(cmd, check=True)
            print(f"  SUCCESS: Comparison completed for {name}@{version}\n")
        except subprocess.CalledProcessError as e:
            print(f"  ERROR: Comparison failed for {name}@{version}: {e}\n")

if __name__ == "__main__":
    run_comparisons()