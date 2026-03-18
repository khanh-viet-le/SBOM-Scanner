"""
Dependency Graph Comparator
============================
Compare subtree JSON from our tool (ground truth)
vs subtree JSON from client app.

USAGE:
  python compare_subtree.py <tool_file> <client_file>

EXAMPLE:
  python compare_subtree.py output_subtree_exif_0.6.0.json exif-0.6.0.json

OR set config directly in CONFIGURATION section below.
"""

import json
import os
import sys


# ============================================================
# CONFIGURATION — used when no command line args provided
# ============================================================

TOOL_FILE   = r"query_output\\query_output_subtree_file-type_16.5.4.json"  # can be full path e.g. r"D:\folder\output_subtree_exif_0.6.0.json"
CLIENT_FILE = r"tool_output\\tool_output_subtree_file-type_16.5.4.json"                 # can be full path e.g. r"D:\folder\exif-0.6.0.json"
OUTPUT_FILE = "compare_result\\compare_result_subtree_file-type_16.5.4.json"              # save result here

# ============================================================
# HELPERS (UPDATED)
# ============================================================

def sanitize_node(node):
    """
    Standardizes node data to handle cases where 'name' includes the 'group'.
    Example: name='@babel/core', group=None  ->  name='core', group='@babel'
    """
    name = node.get("name") or ""
    group = node.get("group") or ""

    # If name contains the group (e.g., @typespec/ts-http-runtime)
    if "/" in name and name.startswith("@"):
        parts = name.split("/", 1)
        # Only override group if it was missing, or keep existing
        group = parts[0]
        name = parts[1]
    
    return name, group

def node_key(node):
    """Generates a key based on sanitized values."""
    name, group = sanitize_node(node)
    version = node.get('version')
    return f"{name}@{version}@{group}"

def node_label(node):
    """Generates a label based on sanitized values."""
    name, group = sanitize_node(node)
    version = node.get('version')
    g = f"{group}/" if group else ""
    return f"{g}{name}@{version}"

def normalize(node):
    """
    Strip extra fields and apply sanitization recursively.
    """
    name, group = sanitize_node(node)
    return {
        "name"    : name,
        "version" : node.get("version"),
        "group"   : group,
        "children": [normalize(c) for c in node.get("children", [])]
    }

# ============================================================
# CORE COMPARE
# ============================================================

def compare_nodes(tool_node, client_node, path="root"):
    issues = []

    # Check name, version, group at current node
    for prop in ["name", "version", "group"]:
        tool_val   = tool_node.get(prop)
        client_val = client_node.get(prop)

        tool_val= (tool_val.split("/"))[-1]
        client_val = (client_val.split("/"))[-1]

        if tool_val != client_val:
            issues.append({
                "type"    : "WRONG_PROPERTY",
                "path"    : path,
                "property": prop,
                "expected": tool_val,
                "actual"  : client_val
            })

    # Compare children
    tool_children   = tool_node.get("children", [])
    client_children = client_node.get("children", [])

    tool_map   = { node_key(c): c for c in tool_children }
    client_map = { node_key(c): c for c in client_children }

    tool_keys   = set(tool_map.keys())
    client_keys = set(client_map.keys())

    # MISSING: in tool but not in client
    for key in tool_keys - client_keys:
        node = tool_map[key]
        issues.append({
            "type"  : "MISSING",
            "path"  : path,
            "parent": node_label(tool_node),
            "node"  : node_label(node),
            "detail": f"Expected '{node_label(node)}' under '{node_label(tool_node)}' but NOT found in client"
        })

    # EXTRA: in client but not in tool
    for key in client_keys - tool_keys:
        node = client_map[key]
        issues.append({
            "type"  : "EXTRA",
            "path"  : path,
            "parent": node_label(client_node),
            "node"  : node_label(node),
            "detail": f"Unexpected '{node_label(node)}' under '{node_label(client_node)}' found in client"
        })

    # Recurse into matching children
    for key in tool_keys & client_keys:
        child_path = f"{path} → {node_label(tool_map[key])}"
        issues.extend(compare_nodes(tool_map[key], client_map[key], child_path))

    return issues


# ============================================================
# MAIN COMPARE
# ============================================================

def compare_subtrees(tool_file, client_file):
    with open(tool_file, "r", encoding="utf-8") as f:
        tool_data = json.load(f)
    with open(client_file, "r", encoding="utf-8") as f:
        client_data = json.load(f)

    tool_norm   = normalize(tool_data)
    client_norm = normalize(client_data)

    issues  = compare_nodes(tool_norm, client_norm)
    missing = [i for i in issues if i["type"] == "MISSING"]
    extra   = [i for i in issues if i["type"] == "EXTRA"]
    wrong   = [i for i in issues if i["type"] == "WRONG_PROPERTY"]
    passed  = len(issues) == 0

    return {
        "verdict"      : "PASS ✅" if passed else "FAIL ❌",
        "tool_file"    : tool_file,
        "client_file"  : client_file,
        "root_node"    : node_label(tool_norm),
        "total_issues" : len(issues),
        "summary"      : { "MISSING": len(missing), "EXTRA": len(extra), "WRONG": len(wrong) },
        "issues"       : { "MISSING": missing, "EXTRA": extra, "WRONG": wrong }
    }


# ============================================================
# PRINT REPORT
# ============================================================

def print_report(result):
    print("\n" + "=" * 60)
    print("  DEPENDENCY GRAPH COMPARISON REPORT")
    print("=" * 60)
    print(f"  Tool file   : {result['tool_file']}")
    print(f"  Client file : {result['client_file']}")
    print(f"  Root node   : {result['root_node']}")
    print("=" * 60)
    print(f"\n  VERDICT      : {result['verdict']}")
    print(f"  Total issues : {result['total_issues']}")
    print(f"    MISSING    : {result['summary']['MISSING']}  (in tool but NOT in client)")
    print(f"    EXTRA      : {result['summary']['EXTRA']}  (in client but NOT in tool)")
    print(f"    WRONG      : {result['summary']['WRONG']}  (wrong name/version/group)")

    if result["issues"]["MISSING"]:
        print("\n" + "-" * 60)
        print("  MISSING NODES:")
        for i in result["issues"]["MISSING"]:
            print(f"  ❌ {i['detail']}")
            print(f"     Path: {i['path']}")

    if result["issues"]["EXTRA"]:
        print("\n" + "-" * 60)
        print("  EXTRA NODES:")
        for i in result["issues"]["EXTRA"]:
            print(f"  ⚠️  {i['detail']}")
            print(f"     Path: {i['path']}")

    if result["issues"]["WRONG"]:
        print("\n" + "-" * 60)
        print("  WRONG PROPERTIES:")
        for i in result["issues"]["WRONG"]:
            print(f"  ⚠️  [{i['property']}] expected='{i['expected']}' actual='{i['actual']}'")
            print(f"     Path: {i['path']}")

    if result["verdict"] == "PASS ✅":
        print("\n  ✅ Client graph matches tool output perfectly!")

    print("\n" + "=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    # Accept command line args: python compare_subtree.py <tool_file> <client_file>
    if len(sys.argv) == 5:
        tool_f   = sys.argv[1]
        client_f = sys.argv[2]
        OUTPUT_FILE = sys.argv[3]
        has_print_report = sys.argv[4] == 1
    else:
        tool_f   = TOOL_FILE
        client_f = CLIENT_FILE
        has_print_report = 0!=0

    result_f = "compare_result"

    # Validate files exist
    for f in [tool_f, client_f]:
        if not os.path.exists(f):
            print(f"ERROR: File not found: {f}")
            sys.exit(1)

    # Run compare
    result = compare_subtrees(tool_f, client_f)

    # # Print report
    if has_print_report:
        print_report(result)

    # Save result
    out = os.path.join(os.path.dirname(os.path.abspath(result_f)), OUTPUT_FILE)
    os.makedirs(os.path.dirname(out), exist_ok=True)

    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n  Result saved: {out}")
