import requests
from django.shortcuts import render, redirect
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
        # Wrap the response in square brackets to make it a valid JSON array (si es necesario)
        if not response_text.startswith('['):
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


def obtener_datos_gym(api_base_url):  # Pasa api_base_url como argumento
    API_URL = f"{api_base_url}/api/socios/"

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


def actualizar_clases_socio(api_base_url, socio_id, nuevas_clases):  # Pasa api_base_url como argumento
    """Función para actualizar las clases restantes de un socio en la API."""

    API_URL = f"{api_base_url}/api/socios/{socio_id}/"

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


def registrar_ingreso_gym(api_base_url, dni_socio, clases_restantes, nombre_socio, apellido_socio):  # Pasa api_base_url como argumento
    """Función para registrar el ingreso de un socio en la base de datos del sistema gym."""

    API_URL = f"{api_base_url}/api/registrar-ingreso/"

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
    alerta_clases = ""

    # Usa una variable para la URL base de la API
    api_base_url = settings.API_BASE_URL  # Obtiene la URL base de la API desde settings

    if request.method == "POST":
        form = DNISearchForm(request.POST)
        if form.is_valid():
            dni = form.cleaned_data["dni"]
            refrescar_pagina = True

            try:
                # 1. Obtener el socio de la API
                datos_gym = obtener_datos_gym(api_base_url)

                if datos_gym:
                    for socio in datos_gym:
                        if socio.get('dni') == dni:
                            socio_encontrado = socio
                            nombre = socio_encontrado.get('nombre', 'Desconocido')
                            apellido = socio_encontrado.get('apellido', 'Desconocido')
                            mensaje = f"Bienvenido, {nombre} {apellido}!"

                            # Lógica de descuento de clases (API)
                            tipo_mensualidad = socio_encontrado.get('tipo_mensualidad', {})
                            clases_restantes = socio_encontrado.get('clases_restantes')
                            socio_id = socio_encontrado.get('id')
                            if tipo_mensualidad.get('tipo') == "12 Clases" and clases_restantes is not None and clases_restantes > 0 and socio_id is not None:
                                nuevas_clases = clases_restantes - 1
                                if actualizar_clases_socio(api_base_url, socio_id, nuevas_clases):
                                    mensaje_clases = f" Te quedan {nuevas_clases} clases."
                                    socio_encontrado["clases_restantes"] = nuevas_clases
                                    # Alerta de dos clases restantes
                                    if nuevas_clases == 2:
                                        alerta_clases = "¡Te quedan 2 clases!"
                                else:
                                    mensaje_error = "Error al actualizar las clases en la API."
                            elif clases_restantes is None or clases_restantes <= 0:
                                mensaje_clases = " No te quedan clases disponibles, renueva tu mensualidad."
                                alerta_clases = ""
                            else:
                                mensaje_error = "Error al procesar la membresía del socio."


                            # 3. Registrar el ingreso (en la API)
                            registrar_ingreso_gym(
                                api_base_url,
                                dni,
                                socio_encontrado.get('clases_restantes', 0) if socio_encontrado else 0,  # Usar get() para evitar errores
                                nombre,
                                apellido,
                            )

                            #4. Datos para mostrar (de la API)
                            datos_socio_mostrar = {
                                "nombre": nombre,
                                "apellido": apellido,
                                "tipo_mensualidad": tipo_mensualidad.get('tipo', "Sin mensualidad"),
                                "clases_restantes": socio_encontrado.get('clases_restantes', 'N/A'),
                                "fecha_vencimiento": socio_encontrado.get('fecha_vencimiento', 'N/A'),
                            }

                            break  # Termina el bucle una vez que se encuentra el socio
                    else:
                        mensaje_error = "Socio no encontrado o datos incorrectos."
                        mensaje = ""
                else:
                    mensaje_error = "Error al obtener datos desde gym"
                    mensaje = ""

            except requests.exceptions.RequestException as e:
                logging.error(f"Error al obtener datos de la API: {e}")
                mensaje_error = f"Error al conectar con la API: {e}"
                mensaje = ""
            except json.JSONDecodeError as e:
                logging.error(f"Error al decodificar JSON: {e}")
                mensaje_error = f"Error al decodificar los datos de la API."
                mensaje = ""
            except Exception as e:
                logging.error(f"Error inesperado: {e}")
                mensaje_error = f"Error inesperado: {e}"
                mensaje = ""

        else:
            refrescar_pagina = False

    else:
        form = DNISearchForm()
        refrescar_pagina = False

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