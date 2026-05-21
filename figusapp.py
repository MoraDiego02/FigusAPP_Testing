import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

# Importamos las funciones con tu lógica desde funciones.py
from funciones import procesar_registro, verificar_login

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.join(BASE_DIR, "html")

app = FastAPI(
    title="FigusAPP API",
    description="Backend en FastAPI para FigusAPP",
    version="1.0.0"
)

@app.get("/")
async def root():
    # Si el usuario entra a la ruta principal, lo mandamos a registro.html
    return RedirectResponse(url="/registro.html")

@app.post("/guardar_registro")
async def guardar_registro(request: Request):
    datos_web = await request.json()
    # Llamamos a tu lógica de validaciones
    resultado = procesar_registro(datos_web)
    
    # Preparamos la respuesta JSON
    if resultado["success"]:
        respuesta = {"mensaje": "Guardado correctamente", "usuario": resultado["data"]}
    else:
        respuesta = {"error": resultado["error"]}
        
    return JSONResponse(status_code=resultado["code"], content=respuesta)

@app.post("/login")
async def login(request: Request):
    datos_web = await request.json()
    # Llamamos a tu lógica de login
    resultado = verificar_login(datos_web)
    
    # Preparamos la respuesta JSON
    if resultado["success"]:
        respuesta = {"mensaje": "Ingreso exitoso", "usuario": resultado["data"]}
    else:
        respuesta = {"error": resultado["error"]}
        
    return JSONResponse(status_code=resultado["code"], content=respuesta)

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