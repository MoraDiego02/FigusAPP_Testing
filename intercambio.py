import os
import json
import datetime
from funciones import obtener_coleccion_usuario

# ---------------- Módulos de Intercambio, Chat y Compartir (RF-IN, RF-CH, RF-SC) ----------------

def obtener_coleccionistas_canje(mail_usuario):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_usuarios_path = os.path.join(base_dir, "html", "registro.json")
    
    # 1. Cargar todos los usuarios registrados
    usuarios = []
    if os.path.exists(json_usuarios_path):
        try:
            with open(json_usuarios_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
                if contenido.strip():
                    usuarios = json.loads(contenido)
        except Exception as e:
            print("Error leyendo registro.json:", e)

    # Buscar mi sala
    mi_sala = ""
    for u in usuarios:
        if u.get("mail") == mail_usuario:
            mi_sala = u.get("codigo_sala", "").strip().upper()
            break

    # Lista de barrios realistas para geolocalización simulada (RF-IN-02)
    barrios = ["Palermo", "Caballito", "Belgrano", "Recoleta", "Almagro", "Villa Urquiza", "San Telmo", "Colegiales"]
    localidad = "CABA"

    coleccionistas = []
    
    # 2. Para cada usuario (excepto el actual), obtener sus métricas básicas de álbum
    for idx, usuario in enumerate(usuarios):
        u_dni = usuario.get("mail")
        if u_dni == mail_usuario:
            continue
            
        u_publico = usuario.get("publico", True)
        u_sala = usuario.get("codigo_sala", "").strip().upper()

        # Si el perfil es privado, SOLO es visible si compartimos la misma sala no vacía
        if not u_publico:
            if not mi_sala or mi_sala != u_sala:
                continue

        # Asignar un barrio determinista basado en su mail/nombre para consistencia
        barrio_idx = (len(usuario.get("nombre", ""))) % len(barrios)
        usuario_barrio = usuario.get("barrio") or barrios[barrio_idx]
        usuario_localidad = usuario.get("localidad") or localidad
        
        # Obtener estadísticas de su colección
        res_col = obtener_coleccion_usuario(u_dni)
        repetidas = 0
        faltantes = 0
        porcentaje = 0.0
        
        if res_col["success"]:
            col_data = res_col["data"]
            porcentaje = col_data["porcentaje_completitud"]
            faltantes = col_data["faltantes"]
            repetidas = col_data["total_repetidas"]
            
        coleccionistas.append({
            "nombre": usuario.get("nombre"),
            "apellido": usuario.get("apellido"),
            "mail": u_dni,
            "barrio": usuario_barrio,
            "localidad": usuario_localidad,
            "porcentaje_completitud": porcentaje,
            "faltantes": faltantes,
            "repetidas": repetidas,
            "codigo_sala": u_sala,
            "publico": u_publico
        })
        
    return {
        "success": True,
        "code": 200,
        "data": coleccionistas
    }


def obtener_historial_mensajes(mail_usuario, mail_contacto):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    mensajes_path = os.path.join(base_dir, "html", "mensajes.json")
    
    mensajes = []
    if os.path.exists(mensajes_path):
        try:
            with open(mensajes_path, "r", encoding="utf-8") as f:
                contenido = f.read()
                if contenido.strip():
                    mensajes = json.loads(contenido)
        except Exception as e:
            print("Error leyendo mensajes.json:", e)

    # Filtrar historial entre ambos usuarios (RF-CH-01, RF-CH-03)
    historial = []
    modificado = False
    
    for msg in mensajes:
        rem = msg.get("remitente")
        dest = msg.get("destinatario")
        
        if (rem == mail_usuario and dest == mail_contacto) or (rem == mail_contacto and dest == mail_usuario):
            # Si el mensaje va dirigido al usuario actual y está sin leer, lo marcamos como leído
            if dest == mail_usuario and not msg.get("leido", False):
                msg["leido"] = True
                modificado = True
            historial.append(msg)

    # Persistir cambios si se marcaron mensajes como leídos
    if modificado:
        try:
            with open(mensajes_path, "w", encoding="utf-8") as f:
                json.dump(mensajes, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print("Error actualizando lectura de mensajes:", e)

    return {
        "success": True,
        "code": 200,
        "data": historial
    }


def registrar_mensaje(remitente, destinatario, texto):
    texto_limpio = str(texto or "").strip()
    if not remitente or not destinatario or not texto_limpio:
        return {
            "success": False,
            "code": 422,
            "error": "El remitente, destinatario y texto del mensaje son obligatorios."
        }

    base_dir = os.path.dirname(os.path.abspath(__file__))
    mensajes_path = os.path.join(base_dir, "html", "mensajes.json")
    
    mensajes = []
    if os.path.exists(mensajes_path):
        try:
            with open(mensajes_path, "r", encoding="utf-8") as f:
                contenido = f.read()
                if contenido.strip():
                    mensajes = json.loads(contenido)
        except Exception as e:
            print("Error leyendo mensajes.json al enviar:", e)

    nuevo_msg = {
        "remitente": str(remitente),
        "destinatario": str(destinatario),
        "mensaje": texto_limpio,
        "fecha": datetime.datetime.utcnow().isoformat() + "Z",
        "leido": False
    }

    mensajes.append(nuevo_msg)
    
    try:
        with open(mensajes_path, "w", encoding="utf-8") as f:
            json.dump(mensajes, f, indent=4, ensure_ascii=False)
    except Exception as e:
        return {
            "success": False,
            "code": 500,
            "error": f"No se pudo enviar el mensaje: {str(e)}"
        }

    return {
        "success": True,
        "code": 200,
        "data": nuevo_msg
    }


def obtener_faltantes_publicos(mail):
    res_col = obtener_coleccion_usuario(mail)
    if not res_col["success"]:
        return res_col

    col_data = res_col["data"]
    
    # Extraer la lista de figuritas faltantes (RF-SC-01, RF-SC-02)
    faltantes_lista = []
    
    # Revisar Especiales
    for fig in col_data["seccion_especial"]["figuritas"]:
        if fig["estado"] == "faltante":
            faltantes_lista.append({
                "numero": fig["numero"],
                "nombre": fig["nombre"],
                "grupo": "Especiales"
            })
            
    # Revisar Grupos y Selecciones
    for grupo in col_data["grupos"]:
        for sel in grupo["selecciones"]:
            for fig in sel["figuritas"]:
                if fig["estado"] == "faltante":
                    faltantes_lista.append({
                        "numero": fig["numero"],
                        "nombre": fig["nombre"],
                        "grupo": f"Grupo {grupo['grupo']} - {sel['pais']}"
                    })

    # Cargar datos básicos del usuario
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_usuarios_path = os.path.join(base_dir, "html", "registro.json")
    
    nombre_usuario = "Coleccionista"
    if os.path.exists(json_usuarios_path):
        try:
            with open(json_usuarios_path, 'r', encoding='utf-8') as f:
                usuarios = json.load(f)
                for u in usuarios:
                    if u.get("mail") == mail:
                        nombre_usuario = f"{u.get('nombre')} {u.get('apellido')}"
                        break
        except Exception as e:
            print("Error cargando usuarios para enlace público:", e)

    return {
        "success": True,
        "code": 200,
        "data": {
            "nombre": nombre_usuario,
            "mail": mail,
            "total_faltantes": len(faltantes_lista),
            "faltantes": faltantes_lista
        }
    }


def obtener_perfil_usuario(mail):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_usuarios_path = os.path.join(base_dir, "html", "registro.json")
    if os.path.exists(json_usuarios_path):
        try:
            with open(json_usuarios_path, 'r', encoding='utf-8') as f:
                usuarios = json.load(f)
                for u in usuarios:
                    if u.get("mail") == mail:
                        return {
                            "success": True,
                            "code": 200,
                            "data": {
                                "mail": u.get("mail"),
                                "nombre": u.get("nombre"),
                                "apellido": u.get("apellido"),
                                "barrio": u.get("barrio", ""),
                                "localidad": u.get("localidad", ""),
                                "publico": u.get("publico", True),
                                "codigo_sala": u.get("codigo_sala", "")
                            }
                        }
        except Exception as e:
            return {"success": False, "code": 500, "error": str(e)}
    return {"success": False, "code": 404, "error": "Usuario no encontrado"}


def actualizar_perfil_usuario(mail, barrio, localidad, publico):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_usuarios_path = os.path.join(base_dir, "html", "registro.json")
    if os.path.exists(json_usuarios_path):
        try:
            usuarios = []
            with open(json_usuarios_path, 'r', encoding='utf-8') as f:
                usuarios = json.load(f)
            
            encontrado = False
            for u in usuarios:
                if u.get("mail") == mail:
                    u["barrio"] = str(barrio or "").strip()
                    u["localidad"] = str(localidad or "").strip()
                    u["publico"] = bool(publico)
                    encontrado = True
                    break
            
            if encontrado:
                with open(json_usuarios_path, 'w', encoding='utf-8') as f:
                    json.dump(usuarios, f, indent=4, ensure_ascii=False)
                return {"success": True, "code": 200, "data": "Perfil actualizado correctamente"}
        except Exception as e:
            return {"success": False, "code": 500, "error": str(e)}
    return {"success": False, "code": 404, "error": "Usuario no encontrado"}


def unirse_sala_usuario(mail, codigo_sala):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_usuarios_path = os.path.join(base_dir, "html", "registro.json")
    codigo_limpio = str(codigo_sala or "").strip().upper()
    if os.path.exists(json_usuarios_path):
        try:
            usuarios = []
            with open(json_usuarios_path, 'r', encoding='utf-8') as f:
                usuarios = json.load(f)
            
            encontrado = False
            for u in usuarios:
                if u.get("mail") == mail:
                    u["codigo_sala"] = codigo_limpio
                    encontrado = True
                    break
            
            if encontrado:
                with open(json_usuarios_path, 'w', encoding='utf-8') as f:
                    json.dump(usuarios, f, indent=4, ensure_ascii=False)
                return {"success": True, "code": 200, "data": {"codigo_sala": codigo_limpio}}
        except Exception as e:
            return {"success": False, "code": 500, "error": str(e)}
    return {"success": False, "code": 404, "error": "Usuario no encontrado"}


def salir_sala_usuario(mail):
    return unirse_sala_usuario(mail, "")

