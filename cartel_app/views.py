from django.shortcuts import render
from .forms import DNISearchForm
from django.conf import settings
import requests
import json
import logging
from django.views.decorators.csrf import csrf_protect
import datetime

def obtener_datos_gym(api_base_url):
    try:
        response = requests.get(api_base_url + "/api/socios/")
        response.raise_for_status()  # Lanza una excepción para códigos de estado HTTP erróneos
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error en la solicitud GET a la API: {e}")
        return None

def actualizar_clases_socio(api_base_url, socio_id, nuevas_clases):
    try:
        response = requests.patch(f"{api_base_url}/api/socios/{socio_id}/", json={"clases_restantes": nuevas_clases})  # Corrección aquí
        response.raise_for_status()
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al actualizar las clases del socio: {e}")
        return False

def registrar_ingreso_gym(api_base_url, dni_socio, clases_restantes_al_ingresar, nombre_socio, apellido_socio):
    try:
        data = {
            "dni_socio": dni_socio,
            "fecha_ingreso": str(datetime.datetime.now()),  # Asegura que fecha_ingreso sea un string
            "clases_restantes_al_ingresar": clases_restantes_al_ingresar,
            "nombre_socio": nombre_socio,
            "apellido_socio": apellido_socio
        }
        response = requests.post(api_base_url + "/api/registrar-ingreso/", json=data)
        response.raise_for_status()
        return response.status_code == 201
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
                                #Codigo original para las 12 clases
                                nuevas_clases = clases_restantes - 1
                                if actualizar_clases_socio(api_base_url, socio_id, nuevas_clases):
                                    mensaje_clases = f" Te quedan {nuevas_clases} clases."
                                    socio_encontrado["clases_restantes"] = nuevas_clases
                                    # Alerta de dos clases restantes
                                    if nuevas_clases == 2:
                                        alerta_clases = "¡Te quedan 2 clases!"
                                else:
                                    mensaje_error = "Error al actualizar las clases en la API."
                            elif tipo_mensualidad.get('tipo') == "Pase Libre":
                                # Aquí la lógica para "Pase Libre"
                                mensaje_clases = " ¡Disfruta de tu entrenamiento!"  # Un mensaje para el cartel
                                alerta_clases = ""  # Asegúrate de limpiar cualquier alerta anterior.

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
                                "fecha_vencimiento": socio_encontrado.get('fecha_vencimiento', None), # Cambio importante: Obtener fecha o None
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