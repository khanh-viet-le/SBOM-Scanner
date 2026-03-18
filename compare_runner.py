import os
import json
from compare_subtree import compare_subtrees

# ============================================================
# CONFIGURATION
# ============================================================
# Path to the list of direct nodes
INPUT_LIST_PATH = os.path.join("output\\tool_output", "tool_output_direct_nodes.json")
# Folder to save the resulting subtrees
OUTPUT_DIR = "output\\query_output"

def process_all_direct_nodes():
    # 1. Check if the input file exists
    if not os.path.exists(INPUT_LIST_PATH):
        print(f"Error: The file was not found at {INPUT_LIST_PATH}")
        return

    # 2. Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    # 3. Load the list of nodes
    try:
        with open(INPUT_LIST_PATH, 'r', encoding='utf-8') as f:
            nodes = json.load(f)
    except Exception as e:
        print(f"Error loading JSON list: {e}")
        return

    for item in nodes:
            subtree_name = item.get("name")
            subtree_version = item.get("version")
            subtree_group = item.get("group")

            query_f   = f"output\\query_output\\query_output_subtree_{subtree_name}_{subtree_version}.json"
            tool_f = f"output\\tool_output\\tool_output_subtree_{subtree_name}_{subtree_version}.json"
            result_f = f"output\\compare_result\\compare_result_subtree_{subtree_name}_{subtree_version}.json"

            if (subtree_group != None) & (not os.path.exists(query_f)):
                query_f = query_f.replace(subtree_group + "/", "")
            
            tool_f = tool_f.replace("/", "_")
            result_f = result_f.replace("/", "_")

            can_process = 1 == 1
            for f in [query_f, tool_f]:
                if not os.path.exists(f):
                    print(f"\nERROR: File not found: {f}")
                    can_process = 1 != 1
            
            if not can_process: continue

            result = compare_subtrees(query_f, tool_f)

            out = os.path.join(os.path.dirname(os.path.abspath("output")), result_f)
            os.makedirs(os.path.dirname(out), exist_ok=True)

            with open(out, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nResult saved: {out}")

if __name__ == "__main__":
    process_all_direct_nodes()