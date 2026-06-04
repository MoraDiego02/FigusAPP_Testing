import json
import os

def procesar_registro(datos):
    nombre = str(datos.get("nombre") or "").strip()
    apellido = str(datos.get("apellido") or "").strip()
    mail = str(datos.get("mail") or "").strip()
    password = str(datos.get("password") or "").strip()
    
    # 1. Validación HTTP 422: Validar campos vacíos
    if not nombre or not apellido or not mail or not password:
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

        # 5. Validación HTTP 409: Evitar duplicados (Mail)
        for usuario in usuarios:
            if usuario.get("mail") == mail:
                return {
                    "success": False, 
                    "code": 409, 
                    "error": "El correo electrónico ingresado ya se encuentra registrado."
                }

        # Si pasa todas las validaciones, creamos el registro (sin DNI ni Edad)
        usuario_validado = {
            "nombre": nombre,
            "apellido": apellido,
            "mail": mail,
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
            "error": "Por favor, ingrese datos válidos."
        }

def verificar_login(datos):
    mail = str(datos.get("mail") or "").strip()
    password = str(datos.get("password") or "").strip()
    
    # 1. Validación HTTP 422: Validar campos vacíos
    if not mail or not password:
        return {
            "success": False, 
            "code": 422, 
            "error": "Por favor, ingresa el correo y la contraseña."
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
            
    # 2. Buscamos si existe un usuario que coincida con Mail y Contraseña
    for usuario in usuarios:
        if usuario.get("mail") == mail and usuario.get("password") == password:
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
        "error": "El correo electrónico o contraseña ingresados son incorrectos."
    }

# ----------------- Funciones del Módulo de Gestión de Colección -----------------

def obtener_coleccion_usuario(mail):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    base_album_path = os.path.join(base_dir, "html", "album_base_completo.json")
    colecciones_path = os.path.join(base_dir, "html", "colecciones.json")

    # 1. Cargar el Catálogo Base de figuritas del Mundial 2026
    if not os.path.exists(base_album_path):
        return {
            "success": False,
            "code": 500,
            "error": "El catálogo base del álbum no está inicializado."
        }

    with open(base_album_path, "r", encoding="utf-8") as f:
        album_base = json.load(f)

    # 2. Cargar o Inicializar la colección del usuario específico
    colecciones = {}
    if os.path.exists(colecciones_path):
        try:
            with open(colecciones_path, "r", encoding="utf-8") as f:
                contenido = f.read()
                if contenido.strip():
                    colecciones = json.loads(contenido)
        except Exception as e:
            print("Error cargando colecciones.json:", e)

    user_inventory = colecciones.get(str(mail), {})

    # 3. Contadores para Métricas / Estadísticas (RF-CO-04)
    total_album = 0
    obtenidas_unicas = 0
    total_repetidas = 0

    # Procesar Secciones Especiales
    especiales_procesadas = []
    seccion_esp = album_base["album"]["secciones_especiales"]
    for fig in seccion_esp["figuritas"]:
        num = fig["numero"]
        total_album += 1
        cantidad = user_inventory.get(num, 0)
        
        # Clasificar estado (RF-CO-02)
        estado = "faltante"
        copias_disponibles = 0
        if cantidad == 1:
            estado = "obtenida"
            obtenidas_unicas += 1
        elif cantidad > 1:
            estado = "repetida"
            obtenidas_unicas += 1
            copias_disponibles = cantidad - 1 # RF-CO-03
            total_repetidas += copias_disponibles

        especiales_procesadas.append({
            "numero": num,
            "nombre": fig["descripcion"],
            "posicion": "Especial",
            "cantidad": cantidad,
            "estado": estado,
            "copias_disponibles": copias_disponibles
        })

    # Procesar Grupos y Selecciones (RF-CO-01)
    grupos_procesados = []
    for grupo_data in album_base["grupos"]:
        selecciones_procesadas = []
        for sel in grupo_data["selecciones"]:
            figuritas_procesadas = []
            for fig in sel["figuritas"]:
                num = fig["numero"]
                total_album += 1
                cantidad = user_inventory.get(num, 0)

                # Clasificar estado (RF-CO-02)
                estado = "faltante"
                copias_disponibles = 0
                if cantidad == 1:
                    estado = "obtenida"
                    obtenidas_unicas += 1
                elif cantidad > 1:
                    estado = "repetida"
                    obtenidas_unicas += 1
                    copias_disponibles = cantidad - 1 # RF-CO-03
                    total_repetidas += copias_disponibles

                figuritas_procesadas.append({
                    "numero": num,
                    "nombre": fig["nombre"] or f"Jugador {num}",
                    "posicion": fig["posicion"] or "Jugador",
                    "cantidad": cantidad,
                    "estado": estado,
                    "copias_disponibles": copias_disponibles
                })

            selecciones_procesadas.append({
                "pais": sel["pais"],
                "codigo": sel["codigo"],
                "flag": sel["flag"],
                "total_figuritas": sel["total_figuritas"],
                "figuritas": figuritas_procesadas
            })

        grupos_procesados.append({
            "grupo": grupo_data["grupo"],
            "selecciones": selecciones_procesadas
        })

    # 4. Calcular porcentaje de completitud (RF-CO-04)
    porcentaje = round((obtenidas_unicas / total_album) * 100, 2) if total_album > 0 else 0.0

    return {
        "success": True,
        "code": 200,
        "data": {
            "mail": mail,
            "total_album": total_album,
            "obtenidas_unicas": obtenidas_unicas,
            "faltantes": total_album - obtenidas_unicas,
            "total_repetidas": total_repetidas,
            "porcentaje_completitud": porcentaje,
            "seccion_especial": {
                "nombre": seccion_esp["nombre"],
                "codigo": seccion_esp["codigo"],
                "figuritas": especiales_procesadas
            },
            "grupos": grupos_procesados
        }
    }

def actualizar_figurita_usuario(mail, numero_figurita, accion):
    dni_str = str(mail).strip()
    num_fig = str(numero_figurita).strip()
    accion = str(accion).strip().lower()

    if not dni_str or not num_fig or not accion:
        return {
            "success": False,
            "code": 422,
            "error": "Faltan parámetros obligatorios: mail, numero_figurita o accion."
        }

    base_dir = os.path.dirname(os.path.abspath(__file__))
    colecciones_path = os.path.join(base_dir, "html", "colecciones.json")

    # 1. Cargar colecciones existentes
    colecciones = {}
    if os.path.exists(colecciones_path):
        try:
            with open(colecciones_path, "r", encoding="utf-8") as f:
                contenido = f.read()
                if contenido.strip():
                    colecciones = json.loads(contenido)
        except Exception as e:
            print("Error leyendo colecciones.json en actualizar:", e)

    # 2. Obtener inventario del usuario
    if dni_str not in colecciones:
        colecciones[dni_str] = {}

    user_inventory = colecciones[dni_str]
    cantidad_actual = user_inventory.get(num_fig, 0)

    # 3. Aplicar acción (incrementar/decrementar)
    if accion == "incrementar":
        nueva_cantidad = cantidad_actual + 1
    elif accion == "decrementar":
        nueva_cantidad = max(0, cantidad_actual - 1)
    else:
        return {
            "success": False,
            "code": 422,
            "error": f"Acción '{accion}' no permitida. Debe ser 'incrementar' o 'decrementar'."
        }

    # 4. Guardar en inventario
    if nueva_cantidad > 0:
        user_inventory[num_fig] = nueva_cantidad
    else:
        # Si la cantidad llega a 0, remover la llave para mantener limpio el JSON
        user_inventory.pop(num_fig, None)

    # 5. Persistir en el archivo JSON
    try:
        with open(colecciones_path, "w", encoding="utf-8") as f:
            json.dump(colecciones, f, indent=4, ensure_ascii=False)
    except Exception as e:
        return {
            "success": False,
            "code": 500,
            "error": f"No se pudo guardar la colección en el archivo: {str(e)}"
        }

    # Determinar el nuevo estado
    nuevo_estado = "faltante"
    if nueva_cantidad == 1:
        nuevo_estado = "obtenida"
    elif nueva_cantidad > 1:
        nuevo_estado = "repetida"

    return {
        "success": True,
        "code": 200,
        "data": {
            "mail": dni_str,
            "numero_figurita": num_fig,
            "nueva_cantidad": nueva_cantidad,
            "nuevo_estado": nuevo_estado,
            "copias_disponibles": max(0, nueva_cantidad - 1)
        }
    }



