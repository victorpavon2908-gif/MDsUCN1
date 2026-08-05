from appOne.models import BitacoraAuditoria
# ============================
#     HELPERS DE UTILIDAD
# ============================

def es_administrador(user):
    """Verifica si un usuario posee el rol de Administrador o Superusuario."""
    return user.is_authenticated and (user.rol == "Admin" or user.is_superuser)


def registrar_auditoria(request, accion, tabla_afectada, registro_id=None, detalles=None):
    """Registra una acción realizada por el usuario en la bitácora de auditoría."""
    ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip:
        ip = ip.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    user = request.user if request.user.is_authenticated else None

    BitacoraAuditoria.objects.create(
        usuario=user,
        accion=accion,
        tabla_afectada=tabla_afectada,
        registro_id=registro_id,
        detalles=detalles,
        ip_origen=ip
    )
