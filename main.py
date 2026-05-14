#Impostamos lobreria  para enviar correos (SMTP)
import smtplib

# Iportamos herramienta para construir el email (asunto, destinatario, etc.)
from email.message import EmailMessage

# IMportamos FastAPI para crear la app
from fastapi import FastAPI, Form

# Importamos HTMLResponse para poder devolver HTML (Formularios, paginas)
from fastapi.responses import HTMLResponse

# Validamos que el Email está correcto
from pydantic import EmailStr

# Importamos random
import random
import string

from pydantic import BaseModel

import requests

import dns.resolver

from dotenv import load_dotenv 
import os

#Cargar variables del .env
load_dotenv()

#Obtener variable de Email
email_user = os.getenv("EMAIL_USER")
email_password = os.getenv("EMAIL_PASWORD")

#Obtener variables Telegram
telegram_token = os.getenv("TELEGRAM_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

#Creamos la aplicacion FAstAPI
app = FastAPI()

# Lista para guardar textos generados
textos_generados = []
class TextoEntrada(BaseModel):
    texto: str

# Ruta para mostrar un formulario HTML
@app.get("/", response_class=HTMLResponse)
def mostrar_formulario():
    return """
    <html>
        <head>
            <title>Formulario con FastAPI</title>
            </head>
            <body>
                <h1>Formulario de contactos</h1>

                <form action="/enviar" method="post">
                    
                    <label>Nombre:</label><br>
                    <input 
                        type="text"
                        name="nombre"
                        minlength="2"
                        maxlength="50"
                        required>
                        <br>

                    <label>Apellido:</label><br>
                    <input
                        type="text"
                        name="apellido"
                        minlength="2"
                        maxlength="50"
                        required>
                        <br>

                    <label>Email:</label><br>
                    <input 
                        type="email" 
                        name="email"
                        required>
                        <br>

                    <button type="submit">Enviar</button>
                </form>
            </body>
        </html>
    """

## Ruta que recibe los datos del formulario
@app.post("/enviar", response_class=HTMLResponse)
def recibir_formulario(
    nombre: str = Form(...),
    apellido: str = Form(...),
    email: EmailStr = Form(...)
):

    # Quitamos espacios al inicio y al final
    nombre = nombre.strip()
    apellido = apellido.strip()

    # Validamos minimo y maximo de caracteres del nombre
    if len(nombre) <2 or len(nombre) > 50:
        return """
        <html>
            <body>
                <h1>Eroor</h1>
                <p>El nombre de tener al menos 2 caracteres y maximo 50.</p>
                <a href="/">Volver</a>
            </body>
        </html>
        """
    if len(apellido) < 2 or len(apellido) > 50:
        return """
        <html>
            <body>
                <h1>Eroor</h1>
                <p>El apellido de tener al menos 2 caracteres y maximo 50.</p>
                <a href="/">Volver</a>
            </body>
        </html>
        """

    emails_gratuitos = ["gmail", "hotmail", "outlook", "yahoo"]

    dominio = email.split("@")[1].lower()
    proveedor = dominio.split(".")[0]
    
    if proveedor in emails_gratuitos:
        return """
        <html>
            <body>
                <h1>Error</h1>
                <p>No se permiten correos gratuitos.</p>
                <a href="/">Volver</a>
            </body>
        </html>
        """
    

    ## Email desde donde se envia
    correo_origen = email_user
    password = email_password

    # Creamos un objeto email
    correo = EmailMessage()

    ## Quien envia el correo
    correo["From"] = correo_origen

    ## A quien se envia (mail del formulario)
    correo["To"] = email

    ## Asunto del correo
    correo["Subject"] = "Formulario recibido"

    # Generamos el token
    caracteres = string.ascii_letters + string.digits

    while True:
        token = ''.join(random.choice(caracteres) for _ in range(43))

        if token not in textos_generados:
            textos_generados.append(token)
            break

    ## Lo que llegará en el correo
    correo.set_content(f"""
Hola {nombre} {apellido},

Gracias por contactarnos.

Tu codigo de verificación es:

{token}

Por favor colocalo en la URL de tu pagina web para validar que eres el propietario.
""")

    ## Enviamos el correo
    ## Nos conectamos el servidor Gamil
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        # Activamos una conexion segura
        smtp.starttls()
        # Iniciamos sesion en el correo origen
        smtp.login(correo_origen, password)
        # Enviamos el corero
        smtp.send_message(correo)
    
    return f"""
        <html>
            <body>
                <h1>Correo enviado correctamente</h1>
                <p>Se ha enviado un coreo a: {email}</p>
                <a href="/">Volver</a>
            </body>
        </html>
        """

@app.get("/generar-texto")
def generar_texto():

    # Definimos los caracteres posibles
    caracteres = string.ascii_letters + string.digits

    # Generamos hasta encontrar uno que no esté repetido
    while True:
        texto = ''.join(random.choice(caracteres) for _ in range(43))
        if texto not in textos_generados:
            textos_generados.append(texto)
            return {
                "token": texto,
                "mensaje" : "Por favor coloca este codigo en la URL de tu pagina web."
            }

@app.post("/verificar-texto")
def verificar_texto(datos: TextoEntrada):

    # Recibimos el texto enviado por el ususario
    texto_recibido = datos.texto

    # Verificamos si el texto existe en la lista
    if texto_recibido in textos_generados:
        return {
            "existe": True,
            "mensaje": "El texto si existe"
        }
    # Si no existe, devolvemos respuesta negativa
    return {
        "existe": False,
        "mensaje": "El texto no existe"
    }

class VerificarURL(BaseModel):
    url: str
    token: str

@app.post("/verificar-txt")
def verificar_txt(datos: VerificarURL):
    url = datos.url
    token = datos.token

    # Validar que el token existe
    if token not in textos_generados:
        return {
            "verificado": False,
            "mensaje": "El token no existe en el sistema"
        }

    #Construimos la URL del
    url_txt = url

    #Intentamos acceder al archivo
    try:
        response = requests.get(url_txt)
    except:
        return {
            "verificado": False,
            "mensaje": "No se pudo acceder al archivo"
        }

    #Validamos respuesta
    if response.status_code != 200:
        return {
            "verificado": False,
            "mensaje": "EL archivo .txt no existe"
        }
    contenido = response.text.strip()

    #Comprobamos token
    if contenido == token:
        return {
            "verificado": True,
            "mensaje": "Dominio verificado correctamente por el archivo TXT"
        }

    return{
        "verificado": False,
        "mensaje": "EL token no coincide"
    }

@app.post("/verificar-dns")
def verificar_dns(datos: VerificarURL):

    dominio = datos.url
    token = datos.token

    #Validar que el token exista
    if token not in textos_generados:
        return {
            "verificado": False,
            "mensaje": "El token no existe en el sistema"
        }

    #Consultar registros TXT
    try:
        respuestas = dns.resolver.resolve(dominio, 'TXT')
    except:
        return {
            "verificado": False,
            "mensaje": "No se pudieron consultar los DNS"
        }

    #Buscar el token en los TXT
    for rdata in respuestas:
        texto = rdata.to_text()

        if token in texto:
            return {
                "verificado": True,
                "mensaje": "Dominio verificado correctamente por DNS"
            }

    return {
        "verificado": False,
        "mensaje": "El token no se encontró en los registros DNS"
    }

def enviar_telegram(mensaje):

    token = telegram_token
    chat_id = telegram_chat_id

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": mensaje
    }

    requests.post(url, data=data)

@app.get("/simular-pago")
def simular_pago():

    # Simulamos resultado (True o False)
    pago_exitoso = random.choice([True, False])

    if pago_exitoso:
        mensaje = "✅ Pago realizado correctamente"
    else:
        mensaje = "❌ Pago rechazado"

    # Enviamos mensaje a Telegram
    enviar_telegram(mensaje)

    return {
        "pago_exitoso": pago_exitoso,
        "mensaje": mensaje
    }