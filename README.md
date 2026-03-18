# SBOM Dependency & Vulnerability Analysis Tool

This project provides a comprehensive suite of tools to parse **CycloneDX (1.4/1.6)** SBOM files, extract dependency subgraphs, and compare them against a ground-truth database via a secure SSH tunnel.

---

## 📂 Project Structure

```text
📦 project-root
 ┣ 📂 output/
 ┃ ┣ 📂 compare_result/         # JSON reports showing PASS/FAIL and discrepancies
 ┃ ┣ 📂 query_output/           # "Ground Truth" subtrees fetched from PostgreSQL
 ┃ ┗ 📂 tool_output/            # Subtrees parsed locally from your SBOM files
 ┣ 📂 sbom_files/               # Input directory for your CycloneDX files
 ┃ ┣ 📜 bom.1.4.json
 ┃ ┗ 📜 bom.1.6.json
 ┣ 📜 .env                      # Active environment variables (DO NOT COMMIT)
 ┣ 📜 .env.example              # Template showing required configuration fields
 ┣ 📜 .gitignore                # Tells Git to ignore output/, .env, and .pem files
 ┣ 📜 README.md                 # This documentation file
 ┣ 📜 requirements.txt          # Required Python libraries (paramiko, pg8000, etc.)
 ┗ 📜 sshkey.pem                # Your private SSH key for establishing the DB tunnel
```

#### Core Runners (The Main Workflow)

| File                     | Description                                                                                                                                     |
| :----------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------- |
| **`sbom_runner.py`**     | **Step 1:** Orchestrates parsing the local SBOM and extracting subtrees into `output/tool_output/`.                                             |
| **`database_runner.py`** | **Step 2:** Reads the extracted nodes from database and automates fetching subtrees into `output/query_output/`.                                |
| **`compare_runner.py`**  | **Step 3:** Batch processes all nodes, comparing the local tool output against the database output, saving results to `output/compare_result/`. |

#### Core Engines & Logic

| File                             | Description                                                                                                            |
| :------------------------------- | :--------------------------------------------------------------------------------------------------------------------- |
| **`sbom_vulnerability_tool.py`** | Parses CycloneDX SBOMs, builds internal dependency maps, and traverses the graph.                                      |
| **`database_manager.py`**        | Handles SSH tunneling (with keep-alive) and secure PostgreSQL connections using `pg8000`.                              |
| **`compare_subtree.py`**         | The logic engine for comparing two JSON trees.                                                                         |
| **`sbom_tool_customize.py`**     | Contains the main `SBOMGraph` class designed to load the SBOM file once and reuse the data efficiently across methods. |

#### Utilities & Helpers

| File                              | Description                                                                                                                                      |
| :-------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------- |
| **`cleanup_output.py`**           | Safety script to wipe old JSON results from the `output/` folders before starting a fresh run.                                                   |
| **`create_readme.py`**            | A quick script to automatically generate/export the `README.md` file.                                                                            |
| **`example_find_in_subtrees.py`** | A search utility. Given a folder of JSON subtrees, it finds exactly which top-level direct dependencies contain a specific vulnerable component. |
| **`tree_printer_tool.py`**        | A debugging utility that prints a beautifully indented, human-readable dependency tree directly in your console.                                 |

## 🚀 Getting Started

### 1. Install Requirements

Ensure you have Python 3.x installed. Then, install the necessary third-party libraries (including `paramiko`, `pg8000`, `sshtunnel`, and `python-dotenv`):

```bash
pip install -r requirements.txt

```

### 2. Setup & Configuration

#### 2.1 SSH Key

Paste your `.pem` SSH key file (e.g., `sshkey.pem`) into the **root directory** of the project.

#### 2.2 Environment Variables

Create a file named `.env` in the root directory. Use the following template (`.env.example`) and replace the values with your actual configuration:

```env
# --- SSH Configuration ---
SSH_HOST=127.0.0.1
SSH_USER=ssh_user
SSH_PKEY=sshkey.pem # --> the file that you pasted in step 2.1

# --- Database Configuration ---
DB_HOST=127.0.0.1
DB_NAME=db_name
DB_USER=db_user
DB_PASS=db_password
DB_PORT=5432

MAX_RETRIES=2

# --- SBOM Runner Configuration ---
SBOM_FILENAME=bom.1.4.json

# Use True or False
GEN_ALL_DIRECT=True
GEN_ALL_SUBGRAPH=True

# Specific Subtree to target
SUBTREE_NAME=serve-index
SUBTREE_VERSION=1.9.1
SUBTREE_GROUP=

# Search Configuration
FIND_BY_COMPONENT=False
SEARCH_NAME=
SEARCH_VERSION=
SEARCH_GROUP=

```

#### 2.3 Cleanup (Optional)

If you are running a new scan and want to ensure a fresh start without mixing old JSON files, run the cleanup script:

```bash
python cleanup_output.py

```

---

## 🛠 Execution Flow

### 3. Generate Subtrees from SBOM

Run the tool to parse your local SBOM (defined in `.env`) and generate subtrees for your direct dependencies.

```bash
python sbom_runner.py

```

- **Result Location:** `output/tool_output/`

### 4. Fetch Database then save as Subtrees

Fetch the "official" dependency trees from the database for the components found in step 3.

```bash
python database_runner.py

```

- **Result Location:** `output/query_output/`

### 5. Compare Results

Compare the local tool output against the database output to find discrepancies.

```bash
python compare_runner.py

```

- **Result Location:** `output/compare_result/`
- **Verdict:** Open the generated JSON files to look for `PASS ✅` or `FAIL ❌` (which will highlight MISSING, EXTRA, or WRONG_PROPERTY nodes).

---

## 📝 Important Notes

- **Standard Library:** Do not try to install `os`, `json`, or `sys` via pip; these are built into Python.
- **Security Warning:** Never commit your `.env` or `.pem` files to version control (Git). Ensure they are added to your `.gitignore` file.
- **Network:** Ensure you have an active internet connection to reach the SSH host and database. Large queries may take several minutes; the SSH tunnel will automatically stay alive.
