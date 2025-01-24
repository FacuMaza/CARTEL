from django.shortcuts import render
from .forms import DNISearchForm
from .models import *  # Importa el modelo "dummy"

def lista_socios(request):
    socios = Socio.objects.all()  # Realiza la consulta
    return render(request, 'tu_template.html', {'socios': socios})


def bienvenida(request):
    mensaje = "Bienvenido al sistema"
    socio_encontrado = None
    form = DNISearchForm()
    mensaje_clases = ""
    mensaje_error = "" # Para mostrar el mensaje de error
    refrescar_pagina = False  # Variable para controlar el refresco

    if request.method == 'POST':
        form = DNISearchForm(request.POST)
        if form.is_valid():
            dni = form.cleaned_data['dni']
            try:
                socio_encontrado = Socio.objects.get(dni=dni)
                mensaje = f"Bienvenido, {socio_encontrado.nombre}!"

                # Registrar el ingreso
                RegistroIngreso.objects.create(dni_socio=dni)

                # Lógica para descuento de clases si es necesario
                if socio_encontrado.tipo_mensualidad:
                    if socio_encontrado.tipo_mensualidad.tipo == "12 clases":
                        if socio_encontrado.clases_restantes > 0:
                            socio_encontrado.clases_restantes -= 1
                            socio_encontrado.save()
                            mensaje_clases = f" Te quedan {socio_encontrado.clases_restantes} clases."
                        else:
                            mensaje_clases = " No te quedan clases disponibles, renueva tu mensualidad."
                
            except Socio.DoesNotExist:
                mensaje_error = "Socio no encontrado o datos incorrectos."
                mensaje = ""  # Limpiar el mensaje principal si hay error
            
            refrescar_pagina = True  # Activar el refresco después de la búsqueda

    return render(request, 'bienvenida.html', {
        'mensaje': mensaje, 
        'form': form, 
        'socio_encontrado': socio_encontrado, 
        'mensaje_clases': mensaje_clases,
        'mensaje_error': mensaje_error, # Pasar el mensaje de error al template
        'refrescar_pagina': refrescar_pagina
    })