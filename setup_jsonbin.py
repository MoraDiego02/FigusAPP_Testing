import json
import urllib.request
import os

API_KEY = "$2a$10$BFNnx3yWq4lNYjhjPmudAeo3Sf81aT1eE1CyJpz7FtfvOXiJneI4O"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

files_to_bin = {
    "registro": os.path.join(BASE_DIR, "html", "registro.json"),
    "colecciones": os.path.join(BASE_DIR, "html", "colecciones.json"),
    "mensajes": os.path.join(BASE_DIR, "html", "mensajes.json")
}

bin_ids = {}

print("Initializing JsonBin bins...")

for name, path in files_to_bin.items():
    if not os.path.exists(path):
        print(f"Error: {path} not found.")
        continue
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    req = urllib.request.Request(
        "https://api.jsonbin.io/v3/b",
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Master-Key": API_KEY,
            "X-Bin-Private": "true",
            "X-Bin-Name": f"figusapp_{name}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
        method="POST"
    )
    
    import urllib.error
    try:
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode("utf-8"))
            bin_id = res_data["metadata"]["id"]
            bin_ids[name] = bin_id
            print(f"Created bin for {name}: {bin_id}")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e else ""
        print(f"Error creating bin for {name}: {e} - Body: {error_body}")
    except Exception as e:
        print(f"Error creating bin for {name}: {e}")

if bin_ids:
    config_path = os.path.join(BASE_DIR, "jsonbin_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(bin_ids, f, indent=4)
    print(f"\nConfiguration saved to {config_path}")
    
    # Also write a .env file for convenience
    env_path = os.path.join(BASE_DIR, ".env")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(f"JSONBIN_API_KEY={API_KEY}\n")
        f.write(f"JSONBIN_REGISTRO_BIN_ID={bin_ids.get('registro', '')}\n")
        f.write(f"JSONBIN_COLECCIONES_BIN_ID={bin_ids.get('colecciones', '')}\n")
        f.write(f"JSONBIN_MENSAJES_BIN_ID={bin_ids.get('mensajes', '')}\n")
    print(f"Environment variables written to {env_path}")
else:
    print("Failed to initialize any bins.")
