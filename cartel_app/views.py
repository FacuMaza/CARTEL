# cartel/views.py
import requests
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from .forms import DNISearchForm
import logging
import json
from django.conf import settings  # Importa settings para obtener DEBUG
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)


def parse_api_response(response_text):
    try:
        # Remove any leading or trailing whitespace
        response_text = response_text.strip()
        # Wrap the response in square brackets to make it a valid JSON array
        response_text = f"[{response_text}]"
        # Replace instances of }{ with }, {
        response_text = response_text.replace("}{", "}, {")
        # Parse the fixed string
        data = json.loads(response_text)
        return data
    except json.JSONDecodeError as e:
        logging.error(f"JSON Decode Error: {e}")
        return None
    except Exception as e:
        logging.error(f"Error: {e}")
        return None


def obtener_datos_gym():
    API_URL = "http://167.99.144.56:8000/api/socios/"  # URL remota, ahora fija

    try:
        logging.debug(f"Haciendo petición GET a: {API_URL}")
        response = requests.get(API_URL)
        response.raise_for_status()
        logging.debug(
            f"Respuesta de la API: {response.status_code}, {response.text}"
        )

        try:
            # Try parsing as JSON
            data = response.json()
            return data
        except json.JSONDecodeError as e:
            # If parsing failed, try to fix the JSON
            logging.warning(f"Respuesta JSON inválida. Intentando reparar... {e}")
            data = parse_api_response(response.text)
            if data:
                logging.info("JSON reparado exitosamente")
                return data
            else:
                logging.error("No se pudo reparar el JSON")
                return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al obtener datos de la API: {e}")
        return None


def actualizar_clases_socio(socio_id, nuevas_clases):
    """Función para actualizar las clases restantes de un socio en la API."""
    API_URL = f"http://167.99.144.56:8000/api/socios/{socio_id}/"  # URL remota, ahora fija

    try:
        data = {"clases_restantes": nuevas_clases}
        logging.debug(f"Haciendo petición PATCH a: {API_URL} con datos: {data}")
        response = requests.patch(API_URL, json=data)
        response.raise_for_status()
        logging.debug(
            f"Respuesta de la API (actualizar clases): {response.status_code}, {response.text}"
        )
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al actualizar clases en la API: {e}")
        return False


def registrar_ingreso_gym(dni_socio, clases_restantes, nombre_socio, apellido_socio):
    """Función para registrar el ingreso de un socio en la base de datos del sistema gym."""
    API_URL = (
        f"http://167.99.144.56:8000/api/registrar-ingreso/"  # URL remota, ahora fija
    )

    try:
        data = {
            "dni_socio": dni_socio,
            "fecha_ingreso": datetime.now().isoformat(),
            "clases_restantes_al_ingresar": clases_restantes,
            "nombre_socio": nombre_socio,
            "apellido_socio": apellido_socio,
        }  # Incluye la hora actual
        logging.debug(f"Haciendo petición POST a: {API_URL} con datos: {data}")
        response = requests.post(API_URL, json=data)
        response.raise_for_status()
        logging.debug(
            f"Respuesta de la API (registrar ingreso): {response.status_code}, {response.text}"
        )
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al registrar el ingreso en la API: {e}")
        return False


@csrf_protect
def bienvenida(request):
    mensaje = "Bienvenido al sistema"
    socio_encontrado = None
    form = DNISearchForm()
    mensaje_clases = ""
    mensaje_error = ""
    refrescar_pagina = False
    datos_socio_mostrar = {}
    alerta_clases = ""  # Mensaje para la alerta de clases restantes

    if request.method == "POST":
        form = DNISearchForm(request.POST)
        print(f"Formulario valido?: {form.is_valid()}")
        if form.is_valid():
            dni = form.cleaned_data["dni"]
            print(f"DNI Ingresado: {dni}")
            refrescar_pagina = (
                True  # Activar la recarga aquí, siempre que el form sea valido
            )
            datos_gym = obtener_datos_gym()

            if datos_gym:
                for socio in datos_gym:
                    print(
                        f"Comparando DNI: socio['dni']={socio['dni']}, dni={dni}"
                    )  # Imprime los valores a comparar
                    if socio["dni"] == dni:
                        socio_encontrado = socio
                        mensaje = (
                            f"Bienvenido, {socio_encontrado['nombre']} {socio_encontrado['apellido']}!"  # Cambiado aquí
                        )

                        # Lógica de descuento de clases
                        if socio_encontrado.get("tipo_mensualidad"):
                            if socio_encontrado["tipo_mensualidad"].get("tipo") == "12 clases":
                                if socio_encontrado["clases_restantes"] > 0:
                                    # Verificar si quedan 2 clases
                                    if socio_encontrado["clases_restantes"] == 2:
                                        alerta_clases = "¡Te quedan 2 clases!"

                                    # Descontar una clase
                                    nuevas_clases = (
                                        socio_encontrado["clases_restantes"] - 1
                                    )
                                    # Actualizar clases en la API
                                    if actualizar_clases_socio(
                                        socio_encontrado["id"], nuevas_clases
                                    ):
                                        mensaje_clases = (
                                            f" Te quedan {nuevas_clases} clases."
                                        )
                                        socio_encontrado["clases_restantes"] = (
                                            nuevas_clases
                                        )  # Actualizamos el valor para la vista
                                        print(
                                            "Clases actualizadas correctamente, y variable refrescar_pagina seteada a True"
                                        )
                                    else:
                                        mensaje_error = "Error al actualizar clases"
                                else:
                                    mensaje_clases = " No te quedan clases disponibles, renueva tu mensualidad."

                        datos_socio_mostrar = {
                            "nombre": socio_encontrado["nombre"],
                            "apellido": socio_encontrado["apellido"],
                            "tipo_mensualidad": socio_encontrado.get(
                                "tipo_mensualidad", {}
                            ).get("tipo", "Sin mensualidad"),
                            "clases_restantes": socio_encontrado.get(
                                "clases_restantes", "N/A"
                            ),
                            "fecha_vencimiento": socio_encontrado.get(
                                "fecha_vencimiento", "N/A"
                            ),
                        }

                        # Registrar el ingreso en el sistema gym
                        if registrar_ingreso_gym(
                            dni,
                            socio_encontrado["clases_restantes"],
                            socio_encontrado["nombre"],
                            socio_encontrado["apellido"],
                        ):  # Pasar el DNI del socio y clases restantes
                            print("Ingreso registrado correctamente en el sistema gym.")
                        else:
                            mensaje_error = "Error al registrar el ingreso en el sistema gym."
                        break
                else:
                    mensaje_error = "Socio no encontrado o datos incorrectos."
                    mensaje = ""
            else:
                mensaje_error = "Error al obtener datos desde gym"
                mensaje = ""
        else:
            refrescar_pagina = (
                False  # Para que no se recargue si el form no es valido
            )

    else:
        form = DNISearchForm()
        refrescar_pagina = False  # Para que no se recargue al inicializar la pagina

    print(f"refrescar_pagina={refrescar_pagina}")
    return render(
        request,
        "bienvenida.html",
        {
            "mensaje": mensaje,
            "form": form,
            "socio_encontrado": socio_encontrado,
            "mensaje_clases": mensaje_clases,
            "mensaje_error": mensaje_error,
            "refrescar_pagina": refrescar_pagina,
            "datos_socio": datos_socio_mostrar,
            "alerta_clases": alerta_clases,
        },
    )