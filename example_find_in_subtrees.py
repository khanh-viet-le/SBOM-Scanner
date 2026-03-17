"""
Example — Find Component in Subtree JSON Files
===============================================
INPUT :
  - Component info: name, version, group
  - List of subtree JSON files OR folder path containing subtree JSON files

OUTPUT:
  - List of direct dependency nodes (root node of each subtree that contains the component)

Chạy: python example_find_in_subtrees.py
"""

import json
import os
from pathlib import Path


# =============================================================================
# INTERNAL — Match component in a subtree
# =============================================================================

def _match_component(node, name, version, group):
    """
    Check if a node matches name + version + group.
    """
    return (
        node.get("name")    == name    and
        node.get("version") == version and
        node.get("group")   == group
    )


def _find_in_subtree(subtree, name, version, group, visited=None):
    """
    Recursively search for a component in a subtree JSON.

    Args:
        subtree : dict — subtree JSON rooted at a direct node
        name    : component name to search
        version : component version to search
        group   : component group to search (can be None)
        visited : set of visited node keys to avoid infinite loop

    Returns:
        True  : if component found in this subtree
        False : if not found
    """
    if visited is None:
        visited = set()

    # Build a unique key for this node to detect duplicates
    node_key = f"{subtree.get('name')}@{subtree.get('version')}@{subtree.get('group')}"

    if node_key in visited:
        return False

    visited.add(node_key)

    # Check if current node matches
    if _match_component(subtree, name, version, group):
        return True

    # Recurse into children
    for child in subtree.get("children", []):
        if _find_in_subtree(child, name, version, group, visited):
            return True

    return False


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def findDirectNodesContainingComponent(input_source, name, version, group):
    """
    Find all direct dependency nodes whose subtree contains
    the specified component (name + version + group).

    Additionally:
        Save result JSON to: sub_trees/result/
    """

    # Step 1 — Collect subtree JSON files
    json_files = []

    if isinstance(input_source, list):
        json_files = input_source
        print(f"Input: list of {len(json_files)} file(s)")

    elif isinstance(input_source, str) and os.path.isdir(input_source):
        for filename in os.listdir(input_source):
            if filename.endswith(".json"):
                json_files.append(os.path.join(input_source, filename))

        print(f"Input: folder '{input_source}' → found {len(json_files)} JSON file(s)")

    else:
        raise ValueError("input_source must be folder path or list of file paths")

    # Step 2 — Search
    matched_direct_nodes = []
    group_label = f"{group}/" if group else ""

    print(f"\nSearching for: {group_label}{name}@{version}")
    print("-" * 60)

    for filepath in sorted(json_files):

        filename = os.path.basename(filepath)

        with open(filepath, "r") as f:
            subtree = json.load(f)

        root_node = {
            "name": subtree.get("name"),
            "version": subtree.get("version"),
            "group": subtree.get("group")
        }

        root_label = f"{root_node['group']+'/' if root_node['group'] else ''}{root_node['name']}@{root_node['version']}"

        found = _find_in_subtree(subtree, name, version, group)

        if found:
            matched_direct_nodes.append(root_node)
            print(f"  ✅ FOUND in [{filename}] → Direct node: {root_label}")
        else:
            print(f"  ❌ NOT FOUND in [{filename}] → Direct node: {root_label}")

    # ============================================================
    # NEW PART — Save result JSON
    # ============================================================

    result_folder = Path("../sub_trees/result")
    result_folder.mkdir(parents=True, exist_ok=True)

    group_prefix = f"{group}_" if group else ""

    result_file = result_folder / f"result_{group_prefix}{name}_{version}.json"

    result_data = {
        "search_component": {
            "name": name,
            "version": version,
            "group": group
        },
        "matched_direct_nodes": matched_direct_nodes,
        "count": len(matched_direct_nodes)
    }

    with open(result_file, "w") as f:
        json.dump(result_data, f, indent=2)

    print("\nSaved result to:", result_file)

    return matched_direct_nodes

def findDirectNodesContainingAllComponents(input_source, components):
    """
    Find direct nodes whose subtree contains ALL components in the list.

    components = [
        {"name": "...", "version": "...", "group": ...},
        ...
    ]
    """

    json_files = []

    if isinstance(input_source, list):
        json_files = input_source

    elif isinstance(input_source, str) and os.path.isdir(input_source):
        for filename in os.listdir(input_source):
            if filename.endswith(".json"):
                json_files.append(os.path.join(input_source, filename))

    else:
        raise ValueError("input_source must be folder path or list of files")

    matched_nodes = []

    print("\nSearching for ALL components:")
    for c in components:
        g = f"{c['group']}/" if c["group"] else ""
        print(f"  - {g}{c['name']}@{c['version']}")

    print("-" * 60)

    for filepath in sorted(json_files):

        with open(filepath, "r") as f:
            subtree = json.load(f)

        root_node = {
            "name": subtree.get("name"),
            "version": subtree.get("version"),
            "group": subtree.get("group")
        }

        root_label = f"{root_node['group']+'/' if root_node['group'] else ''}{root_node['name']}@{root_node['version']}"

        all_found = True

        for comp in components:
            found = _find_in_subtree(
                subtree,
                comp["name"],
                comp["version"],
                comp["group"]
            )

            if not found:
                all_found = False
                break

        if all_found:
            matched_nodes.append(root_node)
            print(f"  ✅ ALL FOUND → {root_label}")
        else:
            print(f"  ❌ Missing component → {root_label}")

    return matched_nodes

def findDirectNodesForEachComponent(input_source, components):
    """
    Find direct nodes for each component individually.

    Return:
    {
        "component_label": [
            {direct_node},
            ...
        ]
    }
    """

    json_files = []

    if isinstance(input_source, list):
        json_files = input_source

    elif isinstance(input_source, str) and os.path.isdir(input_source):
        for filename in os.listdir(input_source):
            if filename.endswith(".json"):
                json_files.append(os.path.join(input_source, filename))

    else:
        raise ValueError("input_source must be folder path or list of files")

    result = {}

    for comp in components:

        comp_label = f"{comp['group']+'/' if comp['group'] else ''}{comp['name']}@{comp['version']}"

        print(f"\nSearching DirectNodes for: {comp_label}")
        print("-" * 60)

        result[comp_label] = []

        for filepath in sorted(json_files):

            with open(filepath, "r") as f:
                subtree = json.load(f)

            root_node = {
                "name": subtree.get("name"),
                "version": subtree.get("version"),
                "group": subtree.get("group")
            }

            root_label = f"{root_node['group']+'/' if root_node['group'] else ''}{root_node['name']}@{root_node['version']}"

            found = _find_in_subtree(
                subtree,
                comp["name"],
                comp["version"],
                comp["group"]
            )

            if found:
                result[comp_label].append(root_node)
                print(f"  ✅ FOUND → {root_label}")
            else:
                print(f"  ❌ NOT FOUND → {root_label}")

    return result

# =============================================================================
# SETUP — Generate sample subtree files for demo
# =============================================================================

def _generate_sample_subtrees(folder):
    """Generate sample subtree JSON files for demo."""

    os.makedirs(folder, exist_ok=True)

    # Subtree 1 — tslib (leaf, no children)
    subtree_tslib = {
        "name": "tslib", "version": "2.8.1", "group": None,
        "children": []
    }

    # Subtree 2 — @typespec/ts-http-runtime (large subtree)
    subtree_ts = {
        "name": "ts-http-runtime", "version": "0.3.2", "group": "@typespec",
        "children": [
            {
                "name": "http-proxy-agent", "version": "7.0.2", "group": None,
                "children": [
                    {
                        "name": "agent-base", "version": "7.1.1", "group": None,
                        "children": [
                            {
                                "name": "debug", "version": "4.3.7", "group": None,
                                "children": [
                                    { "name": "ms", "version": "2.1.3", "group": None, "children": [] }
                                ]
                            }
                        ]
                    },
                    {
                        "name": "debug", "version": "4.4.3", "group": None,
                        "children": [
                            {
                                "name": "supports-color", "version": "8.1.1", "group": None,
                                "children": [
                                    { "name": "has-flag", "version": "4.0.0", "group": None, "children": [] }
                                ]
                            },
                            { "name": "ms", "version": "2.1.3", "group": None, "children": [] }
                        ]
                    },
                    { "name": "agent-base", "version": "7.1.3", "group": None, "children": [] },
                    {
                        "name": "debug", "version": "4.4.0", "group": None,
                        "children": [
                            { "name": "ms", "version": "2.1.3", "group": None, "children": [] },
                            { "name": "supports-color", "version": "10.2.2", "group": None, "children": [] }
                        ]
                    },
                    { "name": "agent-base", "version": "7.1.4", "group": None, "children": [] }
                ]
            },
            {
                "name": "https-proxy-agent", "version": "7.0.6", "group": None,
                "children": [
                    {
                        "name": "debug", "version": "4.4.3", "group": None,
                        "children": [
                            { "name": "ms", "version": "2.1.3", "group": None, "children": [] }
                        ]
                    },
                    { "name": "agent-base", "version": "7.1.3", "group": None, "children": [] }
                ]
            },
            { "name": "tslib", "version": "2.8.1", "group": None, "children": [] }
        ]
    }

    # Save files
    with open(f"{folder}/subtree_tslib_2.8.1.json", "w") as f:
        json.dump(subtree_tslib, f, indent=2)

    with open(f"{folder}/subtree_ts-http-runtime_0.3.2.json", "w") as f:
        json.dump(subtree_ts, f, indent=2)

    print(f"Generated sample subtree files in folder: '{folder}'")
    return [
        f"{folder}/subtree_tslib_2.8.1.json",
        f"{folder}/subtree_ts-http-runtime_0.3.2.json"
    ]


# =============================================================================
# RUN EXAMPLES
# =============================================================================

if __name__ == "__main__":

    FOLDER     = "subtrees"
    FILE_LIST  = _generate_sample_subtrees(FOLDER)

    # =========================================================================
    # TEST 1 — Input: FOLDER PATH | Search: ms@2.1.3
    # =========================================================================
    print("\n" + "=" * 60)
    print("TEST 1 — Input: folder path | Search: ms@2.1.3")
    print("=" * 60)

    result1 = findDirectNodesContainingComponent(
        input_source = FOLDER,
        name         = "ms",
        version      = "2.1.3",
        group        = None
    )

    print(f"\nResult — Affected direct nodes ({len(result1)}):")
    for node in result1:
        g = f"{node['group']}/" if node['group'] else ""
        print(f"  → {g}{node['name']}@{node['version']}")

    # =========================================================================
    # TEST 2 — Input: LIST OF FILES | Search: has-flag@4.0.0
    # =========================================================================
    print("\n" + "=" * 60)
    print("TEST 2 — Input: list of files | Search: has-flag@4.0.0")
    print("=" * 60)

    result2 = findDirectNodesContainingComponent(
        input_source = FILE_LIST,
        name         = "has-flag",
        version      = "4.0.0",
        group        = None
    )

    print(f"\nResult — Affected direct nodes ({len(result2)}):")
    for node in result2:
        g = f"{node['group']}/" if node['group'] else ""
        print(f"  → {g}{node['name']}@{node['version']}")

    # =========================================================================
    # TEST 3 — Input: FOLDER PATH | Search: tslib@2.8.1 (in BOTH subtrees)
    # =========================================================================
    print("\n" + "=" * 60)
    print("TEST 3 — Input: folder path | Search: tslib@2.8.1 (in both subtrees)")
    print("=" * 60)

    result3 = findDirectNodesContainingComponent(
        input_source = FOLDER,
        name         = "tslib",
        version      = "2.8.1",
        group        = None
    )

    print(f"\nResult — Affected direct nodes ({len(result3)}):")
    for node in result3:
        g = f"{node['group']}/" if node['group'] else ""
        print(f"  → {g}{node['name']}@{node['version']}")

    # =========================================================================
    # TEST 4 — Input: FOLDER PATH | Search: not found
    # =========================================================================
    print("\n" + "=" * 60)
    print("TEST 4 — Input: folder path | Search: unknown@9.9.9 (not found)")
    print("=" * 60)

    result4 = findDirectNodesContainingComponent(
        input_source = FOLDER,
        name         = "unknown",
        version      = "9.9.9",
        group        = None
    )

    print(f"\nResult — Affected direct nodes ({len(result4)}):")
    if not result4:
        print("  → Không tìm thấy subtree nào chứa component này!")
