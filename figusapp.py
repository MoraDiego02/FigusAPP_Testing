import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, Union, Dict, Any

from funciones import (
    procesar_registro, 
    verificar_login, 
    obtener_coleccion_usuario, 
    actualizar_figurita_usuario
)
from intercambio import (
    obtener_coleccionistas_canje,
    obtener_historial_mensajes,
    registrar_mensaje,
    obtener_faltantes_publicos,
    obtener_perfil_usuario,
    actualizar_perfil_usuario,
    unirse_sala_usuario,
    salir_sala_usuario
)

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"estado": "FigusAPP online"}


PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.join(BASE_DIR, "html")

app = FastAPI(
    title="FigusAPP API",
    description="Backend en FastAPI para FigusAPP con soporte completo de códigos HTTP documentados en Swagger y Postman",
    version="1.0.0"
)

# ----------------- Modelos de Datos para Peticiones (Request Models) -----------------

class RegistroRequest(BaseModel):
    nombre: Optional[str] = Field(
        None, 
        description="Nombre del usuario", 
        json_schema_extra={"example": "Diego"}
    )
    apellido: Optional[str] = Field(
        None, 
        description="Apellido del usuario", 
        json_schema_extra={"example": "Mora"}
    )
    mail: Optional[str] = Field(
        None, 
        description="Correo electrónico del usuario", 
        json_schema_extra={"example": "diego@correo.com"}
    )
    dni: Optional[str] = Field(
        None, 
        description="DNI del usuario (sin puntos)", 
        json_schema_extra={"example": "12345678"}
    )
    edad: Optional[Union[int, str]] = Field(
        None, 
        description="Edad del usuario. Si es menor de 18 años, el servidor devolverá HTTP 400.", 
        json_schema_extra={"example": 25}
    )
    password: Optional[str] = Field(
        None, 
        description="Contraseña elegida por el usuario (mínimo 6 caracteres)", 
        json_schema_extra={"example": "secreto123"}
    )
    fechaRegistro: Optional[str] = Field(
        None, 
        description="Fecha y hora del registro en formato ISO", 
        json_schema_extra={"example": "2026-05-21T18:22:00Z"}
    )

class LoginRequest(BaseModel):
    mail: Optional[str] = Field(
        None, 
        description="Correo electrónico registrado", 
        json_schema_extra={"example": "diego@correo.com"}
    )
    dni: Optional[str] = Field(
        None, 
        description="DNI registrado sin puntos", 
        json_schema_extra={"example": "12345678"}
    )
    password: Optional[str] = Field(
        None, 
        description="Contraseña del usuario", 
        json_schema_extra={"example": "secreto123"}
    )

class ActualizarFiguritaRequest(BaseModel):
    dni: str = Field(..., description="DNI del usuario", example="12345678")
    numero_figurita: str = Field(..., description="Código oficial de la figurita", example="ARG10")
    accion: str = Field(..., description="Acción a realizar: 'incrementar' o 'decrementar'", example="incrementar")

# ----------------- Modelos de Datos para Respuestas (Response Models) -----------------

class UsuarioResponse(BaseModel):
    nombre: str = Field(..., description="Nombre registrado del usuario", example="Diego")
    apellido: str = Field(..., description="Apellido registrado del usuario", example="Mora")
    mail: str = Field(..., description="Correo electrónico registrado", example="diego@correo.com")
    dni: str = Field(..., description="DNI registrado", example="12345678")
    edad: int = Field(..., description="Edad registrada", example=25)
    password: str = Field(..., description="Contraseña registrada del usuario", example="secreto123")
    fechaRegistro: str = Field(..., description="Fecha de registro", example="2026-05-21T18:22:00Z")


class RegistroExitosoResponse(BaseModel):
    mensaje: str = Field("Guardado correctamente", description="Mensaje de éxito")
    usuario: UsuarioResponse = Field(..., description="Datos del usuario registrado")

class LoginExitosoResponse(BaseModel):
    mensaje: str = Field("Ingreso exitoso", description="Mensaje de éxito")
    usuario: UsuarioResponse = Field(..., description="Datos del usuario autenticado")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Descripción detallada del error", example="Mensaje de error descriptivo")


# ----------------- Rutas del Servidor -----------------

@app.get("/", summary="Redirección Principal", description="Redirige automáticamente al usuario a registro.html", response_class=RedirectResponse)
async def root():
    return RedirectResponse(url="/registro.html")


@app.post(
    "/guardar_registro",
    summary="Registrar Nuevo Usuario",
    description="Procesa y almacena un nuevo usuario en registro.json. Valida campos obligatorios, edad, contraseña y correos/DNIs duplicados.",
    responses={
        200: {
            "model": RegistroExitosoResponse,
            "description": "Registro completado con éxito."
        },
        400: {
            "model": ErrorResponse,
            "description": "Petición Incorrecta - Edad menor a 18 años."
        },
        409: {
            "model": ErrorResponse,
            "description": "Conflicto - El DNI o Correo electrónico ingresado ya está registrado."
        },
        422: {
            "model": ErrorResponse,
            "description": "Entidad No Procesable - Campos obligatorios vacíos (incluyendo contraseña), formato de correo incorrecto o contraseña menor de 6 caracteres."
        }
    }
)
async def guardar_registro(registro: RegistroRequest):
    # Convertimos el modelo Pydantic a diccionario para compatibilidad directa con funciones.py
    datos_web = registro.model_dump()
    resultado = procesar_registro(datos_web)
    
    if resultado["success"]:
        respuesta = {"mensaje": "Guardado correctamente", "usuario": resultado["data"]}
    else:
        respuesta = {"error": resultado["error"]}
        
    return JSONResponse(status_code=resultado["code"], content=respuesta)


@app.post(
    "/login",
    summary="Iniciar Sesión de Usuario",
    description="Verifica las credenciales de correo electrónico, DNI y contraseña en registro.json para iniciar sesión.",
    responses={
        200: {
            "model": LoginExitosoResponse,
            "description": "Inicio de sesión exitoso."
        },
        401: {
            "model": ErrorResponse,
            "description": "No Autorizado - Correo, DNI o contraseña incorrectos."
        },
        422: {
            "model": ErrorResponse,
            "description": "Entidad No Procesable - Campos de correo, DNI o contraseña vacíos."
        }
    }
)
async def login(login_data: LoginRequest):
    # Convertimos el modelo Pydantic a diccionario para compatibilidad directa con funciones.py
    datos_web = login_data.model_dump()
    resultado = verificar_login(datos_web)
    
    if resultado["success"]:
        respuesta = {"mensaje": "Ingreso exitoso", "usuario": resultado["data"]}
    else:
        respuesta = {"error": resultado["error"]}
        
    return JSONResponse(status_code=resultado["code"], content=respuesta)


@app.get(
    "/api/coleccion/{dni}",
    summary="Obtener Colección del Usuario",
    description="Retorna el inventario completo de figuritas (incluyendo especiales y todos los grupos del A al L) junto con métricas agregadas (faltantes, repetidas y completitud) para un DNI dado.",
    responses={
        200: {
            "description": "Colección recuperada correctamente con estadísticas avanzadas."
        },
        500: {
            "model": ErrorResponse,
            "description": "Error Interno del Servidor - Catálogo base ausente."
        }
    }
)
async def get_coleccion(dni: str):
    resultado = obtener_coleccion_usuario(dni)
    if resultado["success"]:
        return JSONResponse(status_code=200, content=resultado["data"])
    return JSONResponse(status_code=resultado["code"], content={"error": resultado["error"]})


@app.post(
    "/api/coleccion/actualizar",
    summary="Actualizar Cantidad de Cromo",
    description="Incrementa o decrementa en una unidad la cantidad registrada de un cromo específico en el álbum del usuario.",
    responses={
        200: {
            "description": "Cromo actualizado correctamente."
        },
        422: {
            "model": ErrorResponse,
            "description": "Petición Incorrecta - Faltan campos requeridos o acción inválida."
        },
        500: {
            "model": ErrorResponse,
            "description": "Error al persistir cambios."
        }
    }
)
async def post_actualizar_figurita(req: ActualizarFiguritaRequest):
    resultado = actualizar_figurita_usuario(req.dni, req.numero_figurita, req.accion)
    if resultado["success"]:
        return JSONResponse(status_code=200, content=resultado["data"])
    return JSONResponse(status_code=resultado["code"], content={"error": resultado["error"]})


# ---------------- Modelos y Endpoints para Módulo de Intercambio, Chat y Compartir ----------------

class EnviarMensajeRequest(BaseModel):
    remitente: str = Field(..., description="DNI del remitente", json_schema_extra={"example": "11223344"})
    destinatario: str = Field(..., description="DNI del destinatario", json_schema_extra={"example": "12345678"})
    mensaje: str = Field(..., description="Texto del mensaje a enviar", json_schema_extra={"example": "Hola, ¿canjeamos?"})


@app.get(
    "/api/coleccionistas/{dni_usuario}",
    summary="Listado de Coleccionistas disponibles para Canje",
    description="Retorna un listado de coleccionistas con sus métricas básicas (completado %, repetidas, faltantes) y geolocalización simulada."
)
async def get_coleccionistas(dni_usuario: str):
    resultado = obtener_coleccionistas_canje(dni_usuario)
    if resultado["success"]:
        return JSONResponse(status_code=200, content=resultado["data"])
    return JSONResponse(status_code=resultado["code"], content={"error": resultado["error"]})


@app.get(
    "/api/mensajes/{dni_usuario}/{dni_contacto}",
    summary="Historial de mensajes privados",
    description="Obtiene el historial de chat entre el usuario actual y el coleccionista seleccionado."
)
async def get_historial_mensajes(dni_usuario: str, dni_contacto: str):
    resultado = obtener_historial_mensajes(dni_usuario, dni_contacto)
    if resultado["success"]:
        return JSONResponse(status_code=200, content=resultado["data"])
    return JSONResponse(status_code=resultado["code"], content={"error": resultado["error"]})


@app.post(
    "/api/mensajes/enviar",
    summary="Enviar mensaje privado",
    description="Envía un nuevo mensaje privado a otro coleccionista para coordinar el canje."
)
async def post_enviar_mensaje(req: EnviarMensajeRequest):
    resultado = registrar_mensaje(req.remitente, req.destinatario, req.mensaje)
    if resultado["success"]:
        return JSONResponse(status_code=200, content=resultado["data"])
    return JSONResponse(status_code=resultado["code"], content={"error": resultado["error"]})


@app.get(
    "/api/compartir/{dni}",
    summary="Ver figuritas faltantes públicas de un usuario",
    description="Retorna una lista pública de figuritas faltantes y datos de un coleccionista a través de un enlace compartido."
)
async def get_compartir_faltantes(dni: str):
    resultado = obtener_faltantes_publicos(dni)
    if resultado["success"]:
        return JSONResponse(status_code=200, content=resultado["data"])
    return JSONResponse(status_code=resultado["code"], content={"error": resultado["error"]})


# ---------------- Modelos y Endpoints para Perfil y Sala de Intercambio ----------------

class PerfilUpdateRequest(BaseModel):
    dni: str = Field(..., description="DNI del usuario", json_schema_extra={"example": "12345678"})
    barrio: str = Field(..., description="Barrio del usuario", json_schema_extra={"example": "Palermo"})
    localidad: str = Field(..., description="Localidad del usuario", json_schema_extra={"example": "CABA"})
    publico: bool = Field(..., description="Si el perfil es público o privado", json_schema_extra={"example": True})

class UnirseSalaRequest(BaseModel):
    dni: str = Field(..., description="DNI del usuario", json_schema_extra={"example": "12345678"})
    codigo_sala: str = Field(..., description="Código de la sala a unirse", json_schema_extra={"example": "SALA123"})

class SalirSalaRequest(BaseModel):
    dni: str = Field(..., description="DNI del usuario", json_schema_extra={"example": "12345678"})


@app.get(
    "/api/perfil/{dni}",
    summary="Obtener Perfil del Usuario",
    description="Retorna la información del perfil del usuario (nombre, barrio, localidad, si es público y código de sala)."
)
async def get_perfil(dni: str):
    resultado = obtener_perfil_usuario(dni)
    if resultado["success"]:
        return JSONResponse(status_code=200, content=resultado["data"])
    return JSONResponse(status_code=resultado["code"], content={"error": resultado["error"]})


@app.post(
    "/api/perfil/actualizar",
    summary="Actualizar Perfil del Usuario",
    description="Actualiza el barrio, localidad y privacidad del perfil de un usuario."
)
async def post_actualizar_perfil(req: PerfilUpdateRequest):
    resultado = actualizar_perfil_usuario(req.dni, req.barrio, req.localidad, req.publico)
    if resultado["success"]:
        return JSONResponse(status_code=200, content={"mensaje": resultado["data"]})
    return JSONResponse(status_code=resultado["code"], content={"error": resultado["error"]})


@app.post(
    "/api/perfil/sala/unirse",
    summary="Unirse a una Sala de Intercambio",
    description="Asocia al usuario con un código de sala para intercambios privados."
)
async def post_unirse_sala(req: UnirseSalaRequest):
    resultado = unirse_sala_usuario(req.dni, req.codigo_sala)
    if resultado["success"]:
        return JSONResponse(status_code=200, content=resultado["data"])
    return JSONResponse(status_code=resultado["code"], content={"error": resultado["error"]})


@app.post(
    "/api/perfil/sala/salir",
    summary="Salir de la Sala de Intercambio",
    description="Desasocia al usuario de su sala actual."
)
async def post_salir_sala(req: SalirSalaRequest):
    resultado = salir_sala_usuario(req.dni)
    if resultado["success"]:
        return JSONResponse(status_code=200, content=resultado["data"])
    return JSONResponse(status_code=resultado["code"], content={"error": resultado["error"]})


# Montamos la carpeta html para servir los archivos estáticos (HTML, CSS, imágenes, etc.)
# IMPORTANTE: Se monta al final para que no interfiera con las rutas de la API.
app.mount("/", StaticFiles(directory=HTML_DIR, html=True), name="html")

if __name__ == "__main__":
    print("=" * 50)
    print(f"Servidor FastAPI iniciado en el puerto {PORT}")
    print(f"Por favor, abre esta URL en tu navegador: http://localhost:{PORT}/registro.html")
    print(f"Documentación interactiva disponible en: http://localhost:{PORT}/docs")
    print("=" * 50)
    uvicorn.run("figusapp:app", host="0.0.0.0", port=PORT, reload=True)