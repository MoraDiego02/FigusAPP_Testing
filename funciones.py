import json
import os

def procesar_registro(datos):
    nombre = str(datos.get("nombre") or "").strip()
    apellido = str(datos.get("apellido") or "").strip()
    mail = str(datos.get("mail") or "").strip()
    dni = str(datos.get("dni") or "").strip()
    password = str(datos.get("password") or "").strip()
    
    # 1. Validación HTTP 422: Validar campos vacíos
    if not nombre or not apellido or not mail or not dni or not password:
        return {
            "success": False, 
            "code": 422, 
            "error": "Por favor, completa todos los campos obligatorios."
        }
        
    # 2. Validación HTTP 422: Validar largo mínimo de contraseña (mínimo 6 caracteres)
    if len(password) < 6:
        return {
            "success": False,
            "code": 422,
            "error": "La contraseña debe tener al menos 6 caracteres."
        }
        
    # 3. Validación HTTP 422: Validar formato básico de email (que tenga '@')
    if "@" not in mail:
        return {
            "success": False, 
            "code": 422, 
            "error": "El formato del correo electrónico no es válido."
        }

    try:
        edad = int(datos.get("edad") or 0)
        
        # 4. Validación HTTP 400: Edad mínima de 18 años
        if edad < 18:
            return {
                "success": False, 
                "code": 400, 
                "error": "Debe ser mayor de 18 años para poder registrarse."
            }
            
        # Definimos la ruta del JSON
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(base_dir, "html", "registro.json")
        
        # Leemos los usuarios existentes
        usuarios = []
        if os.path.exists(json_file_path):
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    if contenido.strip():
                        usuarios = json.loads(contenido)
            except Exception as e:
                print("Error leyendo JSON:", e)

        # 5. Validación HTTP 409: Evitar duplicados (DNI o Mail)
        for usuario in usuarios:
            if usuario.get("dni") == dni:
                return {
                    "success": False, 
                    "code": 409, 
                    "error": "El DNI ingresado ya se encuentra registrado."
                }
            if usuario.get("mail") == mail:
                return {
                    "success": False, 
                    "code": 409, 
                    "error": "El correo electrónico ingresado ya se encuentra registrado."
                }

        # Si pasa todas las validaciones, creamos el registro
        usuario_validado = {
            "nombre": nombre,
            "apellido": apellido,
            "mail": mail,
            "dni": dni,
            "edad": edad,
            "password": password,
            "fechaRegistro": datos.get("fechaRegistro", "")
        }
        
        # Guardamos el nuevo usuario en el JSON
        usuarios.append(usuario_validado)
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(usuarios, f, indent=4, ensure_ascii=False)
            
        print(f"\n¡Registro exitoso para {nombre}!")
        return {
            "success": True, 
            "code": 200, 
            "data": usuario_validado
        }
        
    except (ValueError, TypeError):
        return {
            "success": False, 
            "code": 422, 
            "error": "Por favor, ingrese un número válido para la edad."
        }

def verificar_login(datos):
    mail = str(datos.get("mail") or "").strip()
    dni = str(datos.get("dni") or "").strip()
    password = str(datos.get("password") or "").strip()
    
    # 1. Validación HTTP 422: Validar campos vacíos
    if not mail or not dni or not password:
        return {
            "success": False, 
            "code": 422, 
            "error": "Por favor, ingresa el correo, el DNI y la contraseña."
        }
        
    # Definimos la ruta del JSON
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(base_dir, "html", "registro.json")
    
    # Leemos los usuarios existentes
    usuarios = []
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
                if contenido.strip():
                    usuarios = json.loads(contenido)
        except Exception as e:
            print("Error leyendo JSON para login:", e)
            
    # 2. Buscamos si existe un usuario que coincida exactamente con DNI, Mail y Contraseña
    for usuario in usuarios:
        if usuario.get("mail") == mail and usuario.get("dni") == dni and usuario.get("password") == password:
            print(f"\n¡Inicio de sesión exitoso para {usuario.get('nombre')}!")
            return {
                "success": True, 
                "code": 200, 
                "data": usuario
            }
            
    # 3. Validación HTTP 401: Credenciales inválidas (Ideal para QA)
    return {
        "success": False, 
        "code": 401, 
        "error": "El correo electrónico, DNI o contraseña ingresados son incorrectos."
    }


