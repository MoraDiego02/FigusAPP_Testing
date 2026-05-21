import http.server
import socketserver
import json
import os

# Importamos las funciones con tu lógica desde funciones.py
from funciones import procesar_registro, verificar_login

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.join(BASE_DIR, "html")

class FormRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HTML_DIR, **kwargs)

    def do_GET(self):
        # Si el usuario entra a la ruta principal, lo mandamos a registro.html
        if self.path == '/':
            self.path = '/registro.html'
        return super().do_GET()

    def do_POST(self):
        if self.path == '/guardar_registro':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            datos_web = json.loads(post_data)
            # Llamamos a tu lógica de validaciones
            resultado = procesar_registro(datos_web)
            # 1. Enviamos el código HTTP dinámico que determinó funciones.py (200, 400, 409, 422, etc.)
            self.send_response(resultado["code"])
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            # 2. Preparamos el JSON de respuesta para el navegador
            if resultado["success"]:
                respuesta = {"mensaje": "Guardado correctamente", "usuario": resultado["data"]}
            else:
                respuesta = {"error": resultado["error"]}
                
            # 3. Enviamos la respuesta
            self.wfile.write(json.dumps(respuesta).encode())
        elif self.path == '/login':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            datos_web = json.loads(post_data)
            # Llamamos a tu lógica de login
            resultado = verificar_login(datos_web)
            # Enviamos el código HTTP dinámico (200, 401, 422, etc.)
            self.send_response(resultado["code"])
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            # Preparamos la respuesta
            if resultado["success"]:
                respuesta = {"mensaje": "Ingreso exitoso", "usuario": resultado["data"]}
            else:
                respuesta = {"error": resultado["error"]}
            self.wfile.write(json.dumps(respuesta).encode())
        else:
            self.send_response(404)
            self.end_headers()

# Iniciar el servidor
with socketserver.TCPServer(("", PORT), FormRequestHandler) as httpd:
    print("="*50)
    print(f"Servidor iniciado. Escuchando en el puerto {PORT}")
    print(f"Por favor, abre esta URL en tu navegador: http://localhost:{PORT}/registro.html")
    print("="*50)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")