import os
import json
import urllib.request
import urllib.error

# Load config from environment or fallback to local settings
API_KEY = os.environ.get("JSONBIN_API_KEY", "$2a$10$BFNnx3yWq4lNYjhjPmudAeo3Sf81aT1eE1CyJpz7FtfvOXiJneI4O")

# Try loading from local config if it exists
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, "jsonbin_config.json")
local_config = {}

if os.path.exists(config_path):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            local_config = json.load(f)
    except Exception as e:
        print("Error reading local jsonbin_config.json:", e)

# Bin IDs mapping
BIN_IDS = {
    "registro.json": os.environ.get("JSONBIN_REGISTRO_BIN_ID", local_config.get("registro", "")),
    "colecciones.json": os.environ.get("JSONBIN_COLECCIONES_BIN_ID", local_config.get("colecciones", "")),
    "mensajes.json": os.environ.get("JSONBIN_MENSAJES_BIN_ID", local_config.get("mensajes", ""))
}

# Use JsonBin if API Key is set and all Bin IDs are present
USE_JSONBIN = bool(API_KEY and all(BIN_IDS.values()))

print(f"--- Database Mode: {'JsonBin.io' if USE_JSONBIN else 'Local Files'} ---")

def _request(url, data=None, method="GET"):
    headers = {
        "X-Master-Key": API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
        
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8") if data is not None else None,
        headers=headers,
        method=method
    )
    
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))

def leer_datos(file_name):
    """
    Reads data. If USE_JSONBIN is True, reads from JsonBin.io.
    Otherwise, reads from local file in html/.
    """
    if USE_JSONBIN and file_name in BIN_IDS:
        bin_id = BIN_IDS[file_name]
        url = f"https://api.jsonbin.io/v3/b/{bin_id}/latest"
        try:
            res_data = _request(url, method="GET")
            return res_data["record"]
        except Exception as e:
            print(f"Error reading from JsonBin for {file_name}: {e}. Falling back to local file.")
            # Fallback to local in case of API error
            
    local_path = os.path.join(BASE_DIR, "html", file_name)
    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                contenido = f.read()
                if contenido.strip():
                    return json.loads(contenido)
        except Exception as e:
            print(f"Error reading local backup for {file_name}: {e}")
            
    if file_name == "colecciones.json":
        return {}
    return []

def guardar_datos(file_name, data):
    """
    Writes data. If USE_JSONBIN is True, updates the bin in JsonBin.io.
    Also updates the local file as a backup/cache.
    """
    # Write locally as cache/fallback
    local_path = os.path.join(BASE_DIR, "html", file_name)
    try:
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not write local file backup for {file_name}: {e}")
        # Continue to JsonBin upload even if writing locally fails (like on Vercel's read-only FS)
        
    if USE_JSONBIN and file_name in BIN_IDS:
        bin_id = BIN_IDS[file_name]
        url = f"https://api.jsonbin.io/v3/b/{bin_id}"
        try:
            _request(url, data=data, method="PUT")
            return True
        except Exception as e:
            print(f"Error writing to JsonBin for {file_name}: {e}")
            raise e
            
    return True
