import paramiko
import os
import json
import pg8000
from sshtunnel import SSHTunnelForwarder

# ============================================================
# CONFIGURATION
# ============================================================
SSH_HOST = "35.74.242.225"
SSH_USER = "qc"
SSH_PKEY = "sshkey.pem"

DB_HOST = "35.74.242.225"
DB_NAME = "vuln_pilot"
DB_USER = "postgres"
DB_PASS = "password"
DB_PORT = 15432

# Output folder configuration
OUTPUT_DIR = "query_output"

class DatabaseManager:
    def __init__(self):
        self.tunnel = None
        self.connection = None

    def connect(self):
        """1. Establishes SSH Tunnel and connects to DB via pg8000"""
        try:
            mypkey = paramiko.RSAKey.from_private_key_file(SSH_PKEY)

            self.tunnel = SSHTunnelForwarder(
                (SSH_HOST, 22),
                ssh_username=SSH_USER,
                ssh_pkey=mypkey,
                remote_bind_address=(DB_HOST, DB_PORT),
                local_bind_address=('127.0.0.1', 6543)
            )
            self.tunnel.start()

            self.connection = pg8000.connect(
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME,
                host=self.tunnel.local_bind_host,
                port=self.tunnel.local_bind_port
            )

            print("Successfully connected to Database via SSH using pg8000.")
        except Exception as e:
            print(f"Connection Error")
            if self.tunnel:
                self.tunnel.stop()
            raise

    def get_component_tree(self, name, version):
        """2. Queries the DB for the specific name and version"""
        if not self.connection:
            raise Exception("Database not connected.")

        sql = """
        SELECT public.get_component_tree_json(c.id::uuid, 10)
        FROM public.t_components c
        WHERE c.name = %s 
          AND c.version = %s;
        """
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql, (name, version))
            result = cursor.fetchone()
            
            if result:
                return result[0] 
            return None
        except Exception as e:
            print(f"Query Error")
            return None
        finally:
            if cursor:
                cursor.close()

    def disconnect(self):
        """Clean up connections"""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
        if self.tunnel:
            self.tunnel.stop()
        print("Disconnected.")

# ============================================================
# EXECUTION LOGIC
# ============================================================
# if __name__ == "__main__":
#     db = DatabaseManager()
    
#     # Target component to search
#     subtree_name = "cors"
#     subtree_version = "2.8.5"

#     try:
#         db.connect()
        
#         print(f"Fetching tree for {subtree_name}@{subtree_version}...")
#         tree_data = db.get_component_tree(subtree_name, subtree_version)
        
#         if tree_data:
#             # 1. Ensure the output directory exists
#             if not os.path.exists(OUTPUT_DIR):
#                 os.makedirs(OUTPUT_DIR)
#                 print(f"Created directory: {OUTPUT_DIR}")

#             # 2. Define the filename following your format
#             file_name = f"query_output_subtree_{subtree_name}_{subtree_version}.json"
#             file_path = os.path.join(OUTPUT_DIR, file_name)

#             # 3. Save the result to the JSON file
#             with open(file_path, "w", encoding="utf-8") as f:
#                 json.dump(tree_data, f, indent=2, ensure_ascii=False)

#             print(f"\nSUCCESS: Data saved to {file_path}")
#         else:
#             print(f"\nNo component found matching {subtree_name} version {subtree_version}")

#     except Exception as e:
#         print(f"Main Loop Error")
#     finally:
#         db.disconnect()