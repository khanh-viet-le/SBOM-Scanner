import os
import json
from database_manager import DatabaseManager

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

    # 4. Initialize Database Connection
    db = DatabaseManager()

    for index, item in enumerate(nodes):
           
            subtree_name = (item.get("name").split('/'))[-1]
            subtree_version = item.get("version")
            subtree_group = item.get("group")

            if not subtree_name or not subtree_version:
                continue

            try:
                if index % 5 == 0: db.connect()
                
                print(f"\nFetching tree for {subtree_name}@{subtree_version} and group: {subtree_group}...")
                tree_data = db.get_component_tree(subtree_name, subtree_version, subtree_group)
                
                if tree_data:
                    # 1. Ensure the output directory exists
                    if not os.path.exists(OUTPUT_DIR):
                        os.makedirs(OUTPUT_DIR)
                        print(f"Created directory: {OUTPUT_DIR}")

                    # 2. Define the filename following your format
                    file_name = f"query_output_subtree_{subtree_name}_{subtree_version}.json"
                    file_path = os.path.join(OUTPUT_DIR, file_name)

                    # 3. Save the result to the JSON file
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(tree_data, f, indent=2, ensure_ascii=False)

                    print(f"SUCCESS: Data saved to {file_path}")
                else:
                    print(f"No component found matching {subtree_name} version {subtree_version}")

            except Exception as e:
                print(f"Main Loop Error: {e}")
            finally:
                if index % 5 == 4: db.disconnect()

if __name__ == "__main__":
    process_all_direct_nodes()