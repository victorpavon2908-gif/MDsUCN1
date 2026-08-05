from .models import Usuario, Prestamo, Notificacion


def notificaciones_globales(request):
    """
    Inyecta las notificaciones del sistema y los conteos de pendientes 
    en todas las plantillas HTML de forma global.
    """
    if not request.user.is_authenticated:
        return {}

    user = request.user
    
    # 1. Notificaciones directas del usuario activo
    notificaciones_usuario = Notificacion.objects.filter(usuario=user)
    notificaciones_no_leidas_count = notificaciones_usuario.filter(leida=False).count()
    notificaciones_recientes = notificaciones_usuario[:5]

    # 2. Préstamos propios
    query_prestamos_propios = Prestamo.objects.filter(
        usuario=user
    ).select_related('dispositivo').order_by('-fecha_solicitud')

    # 3. Lógica de consultas según el rol
    if user.rol == "Admin" or user.is_superuser:
        prestamos_pendientes_admin = Prestamo.objects.filter(
            estado=Prestamo.ESTADO_PENDIENTE
        ).select_related('usuario', 'dispositivo').order_by('-fecha_solicitud')
        
        usuarios_pendientes_admin = Usuario.objects.filter(
            is_active=False
        ).order_by('-date_joined')

        pendientes_count = prestamos_pendientes_admin.count() + usuarios_pendientes_admin.count()
    else:
        prestamos_pendientes_admin = Prestamo.objects.none()
        usuarios_pendientes_admin = Usuario.objects.none()
        pendientes_count = query_prestamos_propios.filter(estado=Prestamo.ESTADO_PENDIENTE).count()

    return {
        # Colecciones para vistas y menús contextuales
        'notificaciones_recientes': notificaciones_recientes,
        'prestamos_pendientes_admin': prestamos_pendientes_admin,
        'usuarios_pendientes_admin': usuarios_pendientes_admin,
        'prestamos_propios': query_prestamos_propios[:5],
        
        # Contadores de alertas y badges
        'notificaciones_no_leidas_count': notificaciones_no_leidas_count,
        'pendientes_count': pendientes_count,
    }