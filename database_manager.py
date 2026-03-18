import paramiko
import pg8000
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv
import os

# ============================================================
# CONFIGURATION
# ============================================================

# Load the variables from the .env file
load_dotenv()

SSH_HOST = os.getenv("SSH_HOST")
SSH_USER = os.getenv("SSH_USER")
SSH_PKEY = os.getenv("SSH_PKEY")

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = int(os.getenv("DB_PORT", 15432))

MAX_DEPTH = int(os.getenv("MAX_DEPTH", 10))

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
                local_bind_address=('127.0.0.1', 6543),
                set_keepalive=30 # Sends a packet every 30s to keep the tunnel alive
            )
            self.tunnel.start()

            self.connection = pg8000.connect(
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME,
                host=self.tunnel.local_bind_host,
                port=self.tunnel.local_bind_port,
                timeout=600 # Increases timeout to 10 minutes for large trees
            )

            print("Successfully connected to Database via SSH using pg8000.")
        except Exception as e:
            print(f"Connection Error")
            if self.tunnel:
                self.tunnel.stop()
            raise

    def get_component_tree(self, name, version, group = None):
        """2. Queries the DB for the specific name and version"""
        if not self.connection:
            raise Exception("Database not connected.")

        if group is None:
            sql = """
            SELECT public.get_component_tree_json(c.id::uuid, %s)
            FROM public.t_components c
            WHERE c.name = %s 
              AND c.version = %s
              AND c.group IS NULL;
            """
            params = (MAX_DEPTH, name, version)
        else:
            sql = """
            SELECT public.get_component_tree_json(c.id::uuid, %s)
            FROM public.t_components c
            WHERE c.name = %s 
              AND c.version = %s
              AND c.group = %s;
            """
            params = (MAX_DEPTH, name, version, group)
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql, params)
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