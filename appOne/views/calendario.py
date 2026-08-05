from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from appOne.models import Prestamo
from .utils import es_administrador

@login_required
def calendario_reservas(request):
    return render(request, 'appOne/calendario.html')


@login_required
def api_reservas_eventos(request):
    admin = es_administrador(request.user)
    
    if admin:
        prestamos = Prestamo.objects.select_related('dispositivo', 'usuario').all()
    else:
        prestamos = Prestamo.objects.select_related('dispositivo', 'usuario').filter(usuario=request.user)

    eventos = []
    
    color_map = {
        'pendiente': '#f57c00',
        'aprobado': '#2e7d32',
        'rechazado': '#d32f2f',
        'devuelto': '#616161',
    }

    for p in prestamos:
        nombre_usuario = p.usuario.nombre_completo or p.usuario.username
        if admin:
            titulo = f"{p.dispositivo.nombre_dispositivo} - {nombre_usuario}"
        else:
            titulo = f"{p.dispositivo.nombre_dispositivo} ({p.get_estado_display()})"

        start_iso = None
        end_iso = None

        if p.fecha_uso:
            if p.hora_inicio:
                start_iso = f"{p.fecha_uso.isoformat()}T{p.hora_inicio.isoformat()}"
            else:
                start_iso = p.fecha_uso.isoformat()

            if p.hora_entrega:
                end_iso = f"{p.fecha_uso.isoformat()}T{p.hora_entrega.isoformat()}"
        elif p.fecha_solicitud:
            start_iso = p.fecha_solicitud.isoformat()

        eventos.append({
            'id': p.id,
            'title': titulo,
            'start': start_iso,
            'end': end_iso,
            'backgroundColor': color_map.get(p.estado, '#1976d2'),
            'borderColor': color_map.get(p.estado, '#1976d2'),
            'extendedProps': {
                'estado': p.get_estado_display(),
                'dispositivo': p.dispositivo.nombre_dispositivo,
                'usuario': nombre_usuario,
                'motivo': p.motivo
            }
        })

    return JsonResponse(eventos, safe=False)