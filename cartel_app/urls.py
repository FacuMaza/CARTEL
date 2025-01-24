from django.urls import path
from . import views

urlpatterns = [
    path('socios/', views.lista_socios, name='lista_socios'),
]

urlpatterns += [
    path('bienvenida/', views.bienvenida, name='bienvenida'),
]