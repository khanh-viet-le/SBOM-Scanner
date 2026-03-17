import json
import os

def print_dependency_tree(node, level=0):
    """
    Recursively prints the dependency tree, sorted alphabetically.
    """
    # Extract data
    name = node.get("name", "unknown")
    group = node.get("group")
    version = node.get("version", "unknown")
    children = node.get("children", [])

    # Format the identity string
    identity = f"{group}/{name}@{version}" if group else f"{name}@{version}"

    # Print with indentation
    indent = "    " * level
    print(f"{indent}- {level} {identity}")

    # Sort children alphabetically by (group, name) before recursing
    # We use a lambda to handle None values in 'group' by converting them to empty strings
    sorted_children = sorted(
        children, 
        key=lambda x: (x.get("group") or "", x.get("name", ""))
    )

    # Recurse through sorted children
    for child in sorted_children:
        print_dependency_tree(child, level + 1)

# File loading logic
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "query_output", "query_output_subtree_file-type_16.5.4.json")
    file_path = os.path.join(script_dir, "tool_output", "tool_output_subtree_file-type_16.5.4.json")

    with open(file_path, 'r') as f:
        data = json.load(f)
        
    print_dependency_tree(data)

except FileNotFoundError:
    print(f"Error: The file was not found at {file_path}")
except json.JSONDecodeError:
    print("Error: Failed to decode JSON. Check the file format.")