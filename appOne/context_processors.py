# appOne/context_processors.py
from .models import Usuario, Prestamo

def notificaciones_globales(request):
    """
    Inyecta las notificaciones globales en todas las plantillas HTML
    sin importar en qué vista se encuentre el usuario.
    """
    if not request.user.is_authenticated:
        return {}

    user = request.user
    
    # 1. Préstamos pendientes de aprobación (para Admins)
    prestamos_pendientes_admin = Prestamo.objects.filter(
        estado=Prestamo.ESTADO_PENDIENTE
    ).select_related('usuario', 'dispositivo').order_by('-fecha_solicitud')
    
    # 2. Registros de nuevos usuarios pendientes (para Admins)
    usuarios_pendientes_admin = Usuario.objects.filter(
        is_active=False
    ).order_by('-date_joined')
    
    # 3. Guardamos la consulta base de préstamos propios (SIN [:5])
    query_prestamos_propios = Prestamo.objects.filter(
        usuario=user
    ).select_related('dispositivo').order_by('-fecha_solicitud')

    # Cálculo del total de pendientes según el rol
    if user.rol == "Admin" or user.is_superuser:
        pendientes_count = prestamos_pendientes_admin.count() + usuarios_pendientes_admin.count()
    else:
        # Hacemos el .filter() sobre la consulta completa
        pendientes_count = query_prestamos_propios.filter(estado=Prestamo.ESTADO_PENDIENTE).count()

    return {
        'prestamos_pendientes_admin': prestamos_pendientes_admin,
        'usuarios_pendientes_admin': usuarios_pendientes_admin,
        # Aplicamos el corte [:5] únicamente al enviar la variable a la plantilla
        'prestamos_propios': query_prestamos_propios[:5],
        'pendientes_count': pendientes_count,
    }