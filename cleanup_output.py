import os
import glob

# ============================================================
# CONFIGURATION
# ============================================================
# Define the folders to clean up
TARGET_FOLDERS = [
    os.path.join("output", "tool_output"),
    os.path.join("output", "query_output"),
    os.path.join("output", "compare_result")
]

def remove_json_files():
    print("Starting cleanup of JSON files...")
    
    files_removed = 0
    
    for folder in TARGET_FOLDERS:
        # Construct the search pattern (e.g., "output/tool_output/*.json")
        pattern = os.path.join(folder, "*.json")
        
        # Get a list of all matching files
        files = glob.glob(pattern)
        
        if not files:
            print(f"  No JSON files found in: {folder}")
            continue
            
        print(f"  Cleaning folder: {folder}")
        
        for file_path in files:
            try:
                os.remove(file_path)
                files_removed += 1
                # Optional: print(f"    Deleted: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"    Error deleting {file_path}: {e}")

    print("-" * 30)
    print(f"Cleanup complete. Total files removed: {files_removed}")

if __name__ == "__main__":
    # Ask for confirmation to prevent accidental deletion
    confirm = input("This will delete ALL JSON files in the output folders. Proceed? (y/n): ")
    if confirm.lower() == 'y':
        remove_json_files()
    else:
        print("Cleanup cancelled.")