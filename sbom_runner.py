import json
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Helper to convert string "True"/"False" from .env to Python Booleans
def get_env_bool(key, default=False):
    val = os.getenv(key, str(default)).lower()
    return val in ("true", "1", "yes")

# Add current dir to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sbom_vulnerability_tool import SBOMVulnerabilityTool

# ============================================================
# CONFIGURATION — Edit these values
# ============================================================

SBOM_FILENAME      = os.getenv("SBOM_FILENAME", "bom.1.4.json")

GEN_ALL_DIRECT     = get_env_bool("GEN_ALL_DIRECT", True)
GEN_ALL_SUBGRAPH   = get_env_bool("GEN_ALL_SUBGRAPH", True)

SUBTREE_NAME       = os.getenv("SUBTREE_NAME", "serve-index")
SUBTREE_VERSION    = os.getenv("SUBTREE_VERSION", "1.9.1")
SUBTREE_GROUP      = os.getenv("SUBTREE_GROUP") or None

FIND_BY_COMPONENT  = get_env_bool("FIND_BY_COMPONENT", False)
SEARCH_NAME        = os.getenv("SEARCH_NAME") or None
SEARCH_VERSION     = os.getenv("SEARCH_VERSION") or None
SEARCH_GROUP       = os.getenv("SEARCH_GROUP") or None

# ============================================================
# PATH SETUP
# ============================================================

# Get the base directory where this script resides
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define specific folders
INPUT_FOLDER = os.path.join(BASE_DIR, "sbom_files")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output\\tool_output")

# Ensure the tool_output directory exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Construct final path to the SBOM file
# Priority: 1. Command line argument, 2. Hardcoded filename in /sbom_files/
if len(sys.argv) > 1:
    SBOM_FILE = sys.argv[1]
else:
    SBOM_FILE = os.path.join(INPUT_FOLDER, SBOM_FILENAME)

if not os.path.exists(SBOM_FILE):
    print(f"ERROR: SBOM file not found at: {SBOM_FILE}")
    sys.exit(1)

print(f"\nReading SBOM from : {SBOM_FILE}")
print(f"Saving Results to : {OUTPUT_FOLDER}\n")

tool = SBOMVulnerabilityTool(SBOM_FILE)

# Helper function to clean filenames (replaces characters that might break paths)
def safe_path(filename):
    return os.path.join(OUTPUT_FOLDER, filename.replace("/", "_"))

# ============================================================
# METHOD 1 — getAllDirectDependenceNodes
# ============================================================
if GEN_ALL_DIRECT:
    print("[1] Generating all direct dependency nodes...")
    result = tool.getAllDirectDependenceNodes()
    outfile = safe_path("tool_output_direct_nodes.json")
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"    Done: {outfile}")

# ============================================================
# METHOD 2a — getSubTree for ALL direct nodes
# ============================================================
if GEN_ALL_SUBGRAPH:
    print("\n[2a] Generating subtrees for ALL direct nodes...")
    direct_nodes = tool.getAllDirectDependenceNodes()
    for node in direct_nodes:
        subtree = tool.getSubTreeByDirectNode(node["name"], node["version"], node["group"])
        fname = f"tool_output_subtree_{node['name']}_{node['version']}.json"
        outfile = safe_path(fname)
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(subtree, f, indent=2, ensure_ascii=False)
    print(f"    Done: Processed {len(direct_nodes)} nodes.")

# ============================================================
# METHOD 2b — getSubTree for ONE specific node
# ============================================================
if SUBTREE_NAME:
    print(f"\n[2b] Generating subtree for {SUBTREE_NAME}@{SUBTREE_VERSION}...")
    subtree = tool.getSubTreeByDirectNode(SUBTREE_NAME, SUBTREE_VERSION, SUBTREE_GROUP)
    if subtree:
        fname = f"tool_output_subtree_{SUBTREE_NAME}_{SUBTREE_VERSION}.json"
        outfile = safe_path(fname)
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(subtree, f, indent=2, ensure_ascii=False)
        print(f"    Done: {outfile}")
    else:
        print(f"    WARNING: Component not found: {SUBTREE_NAME}")

# ============================================================
# METHOD 3 — findAffectedDirectNodes
# ============================================================
if FIND_BY_COMPONENT and SEARCH_NAME:
    print(f"\n[3] Finding affected nodes for {SEARCH_NAME}...")
    result = tool.findAffectedDirectNodes([{ "name": SEARCH_NAME, "version": SEARCH_VERSION, "group": SEARCH_GROUP }])
    fname = f"tool_output_affected_{SEARCH_NAME}.json"
    outfile = safe_path(fname)
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"    Done: {outfile}")

print("\nProcessing complete! Check the output/tool_output/ folder.")
input("\nPress Enter to exit...")