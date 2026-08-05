from .utils import es_administrador, registrar_auditoria
from .auth import login_view, logout_view, registro
from .dashboard import dashboard, layaut_Principal
from .usuarios import panel_usuarios, aprobar_usuario, rechazar_usuario, eliminar_usuario
from .dispositivos import listardispositivos, agregar_dispositivo, editar_dispositivo, eliminar_dispositivo
from .prestamos import (
    modal_prestamo, crear_prestamo, aprobar_prestamo, rechazar_prestamo,
    devolver_prestamo, solicitudes_prestamos, eliminar_historial_prestamos,
    restaurar_historial_todos
)
from .configuracion import panel_config, config_inicio, config_database, config_perfil, config_seguridad
from .auditoria import bitacora_auditoria
from .reportes import reportes
from .calendario import calendario_reservas, api_reservas_eventos