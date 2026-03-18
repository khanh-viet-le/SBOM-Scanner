import os
import json
import time
from database_manager import DatabaseManager
from dotenv import load_dotenv


# Load the variables from the .env file
load_dotenv()

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

    # Initial Connection
    db.connect()

    for index, item in enumerate(nodes):
        
        subtree_name = (item.get("name").split('/'))[-1]
        subtree_version = item.get("version")
        subtree_group = item.get("group")

        if not subtree_name or not subtree_version:
            continue

        max_retries = int(os.getenv("MAX_RETRIES", 2))
        for attempt in range(max_retries):
            try:
                print(f"\n[{index+1}/{len(nodes)}] Fetching {subtree_name}@{subtree_version}...")
                
                # Logic 2: Fetch the data
                tree_data = db.get_component_tree(subtree_name, subtree_version, subtree_group)
                
                if tree_data:
                    file_name = f"query_output_subtree_{subtree_name}_{subtree_version}.json"
                    file_path = os.path.join(OUTPUT_DIR, file_name)
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(tree_data, f, indent=2, ensure_ascii=False)
                    print(f"  SUCCESS saved.")
                else:
                    print(f"  NOT FOUND in database.")
                
                # If success, break the retry loop
                break 

            except Exception as e:
                print(f"  ERROR on attempt {attempt + 1}: {e}")
                print("  Re-establishing connection...")
                
                # Forced cleanup and reconnection
                db.disconnect()
                time.sleep(2) # Brief pause for port cleanup
                db.connect()
                
                if attempt == max_retries - 1:
                    print(f"  FAILED permanently for {subtree_name}")

        # Periodic refresh every 10 nodes to prevent "stale" connections
        if index % 10 == 9:
            print("\n--- Periodic connection refresh ---")
            db.disconnect()
            db.connect()

    db.disconnect()

if __name__ == "__main__":
    process_all_direct_nodes()