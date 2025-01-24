from django.db import models

class TipoMensualidad(models.Model):
    tipo = models.CharField(max_length=255)  # Ejemplo de longitud máxima, ajústala según necesites
    precio = models.DecimalField(max_digits=10, decimal_places=2)  # Usando DecimalField para precios
    
    def __str__(self):
        return '%s %s  '%(self.tipo,self.precio)

    class Meta:
        managed = False
        db_table = 'TipoMensualidades'


class Gimnasio(models.Model):

    direccion = models.CharField(max_length=255)
    
    class Meta:
        managed = False
        db_table = 'Gimnasios'  # Nombre de la tabla exactamente igual al proyecto A

class TipoUsuario(models.Model):
    tipousuario = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'TipoUsuarios'  # Nombre de la tabla exactamente igual al proyecto A

class Usuario(models.Model):
    tipo_usuario = models.ForeignKey(TipoUsuario, on_delete=models.CASCADE)  # Ej: "admin", "entrenador", "miembro"
    usuario = models.CharField(max_length=255, unique=True) # Nombre de usuario
    contrasena = models.CharField(max_length=255)  # Considera el hash de contraseñas

    class Meta:
        managed = False
        db_table = 'Usuarios'  # Nombre de la tabla exactamente igual al proyecto A


class Socio(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255)
    dni = models.CharField(max_length=20)
    gimnasio = models.ForeignKey(Gimnasio, on_delete=models.CASCADE, related_name="socios",default=None)
    tipo_mensualidad = models.ForeignKey('TipoMensualidad', on_delete=models.SET_NULL, null=True, blank=True) # Relación con TipoMensualidad
    clases_restantes = models.IntegerField(default=0)
    
    class Meta:
        managed = False
        db_table = 'Socios'



class RegistroIngreso(models.Model):
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    dni_socio = models.CharField(max_length=20)

    def __str__(self):
        return '%s %s' % (self.fecha_ingreso, self.dni_socio)

    class Meta:
        managed = False
        db_table = 'Registro Ingresos'