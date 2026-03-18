import paramiko
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

    def get_component_tree(self, name, version, group = None):
        """2. Queries the DB for the specific name and version"""
        if not self.connection:
            raise Exception("Database not connected.")

        if group is None:
            sql = """
            SELECT public.get_component_tree_json(c.id::uuid, 10)
            FROM public.t_components c
            WHERE c.name = %s 
              AND c.version = %s
              AND c.group IS NULL;
            """
            params = (name, version)
        else:
            sql = """
            SELECT public.get_component_tree_json(c.id::uuid, 10)
            FROM public.t_components c
            WHERE c.name = %s 
              AND c.version = %s
              AND c.group = %s;
            """
            params = (name, version, group)
        
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