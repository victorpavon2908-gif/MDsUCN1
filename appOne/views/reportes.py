from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone

from appOne.models import Usuario, Dispositivo, Prestamo, BitacoraAuditoria
from .utils import es_administrador


@login_required
def reportes(request):
    if not es_administrador(request.user):
        messages.error(request, "No tienes permisos para visualizar reportes consolidados.")
        return redirect('dashboardinicio')

    # 1. KPIs Generales
    total_dispositivos = Dispositivo.objects.count()
    total_usuarios = Usuario.objects.filter(is_active=True).count()
    total_prestamos = Prestamo.objects.count()

    # 2. Distribución de Préstamos por Estado
    estados_qs = Prestamo.objects.values('estado').annotate(total=Count('id'))
    estados_labels = [e['estado'].capitalize() for e in estados_qs]
    estados_data = [e['total'] for e in estados_qs]

    # 3. Tendencia de Préstamos (Últimos 7 Días) - Sin el lookup __date redundante
    hoy = timezone.now().date()
    hace_7_dias = hoy - timedelta(days=6)

    # Filtrado directo en DateField (gte y lte nativos)
    prestamos_qs = Prestamo.objects.filter(
        fecha_uso__gte=hace_7_dias,
        fecha_uso__lte=hoy
    ).values_list('fecha_uso', flat=True)

    # Agrupación segura en memoria
    conteo_por_fecha = {}
    for fecha in prestamos_qs:
        if fecha:
            conteo_por_fecha[fecha] = conteo_por_fecha.get(fecha, 0) + 1

    dias = []
    prestamos_por_dia = []

    for i in range(6, -1, -1):
        dia_evaluar = hoy - timedelta(days=i)
        dias.append(dia_evaluar.strftime("%d/%m"))
        prestamos_por_dia.append(conteo_por_fecha.get(dia_evaluar, 0))

    # 4. Top 5 Dispositivos más Solicitados
    dispositivos_qs = (
        Prestamo.objects.values('dispositivo__nombre_dispositivo')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )
    dispositivos_labels = [d['dispositivo__nombre_dispositivo'] for d in dispositivos_qs]
    dispositivos_data = [d['total'] for d in dispositivos_qs]

    # 5. Bitácora de Auditoría
    logs = (
        BitacoraAuditoria.objects.select_related('usuario')
        .order_by('-fecha_hora')[:10]
    )

    context = {
        'total_dispositivos': total_dispositivos,
        'total_usuarios': total_usuarios,
        'total_prestamos': total_prestamos,
        'estados_labels': estados_labels,
        'estados_data': estados_data,
        'dias': dias,
        'prestamos_por_dia': prestamos_por_dia,
        'dispositivos_labels': dispositivos_labels,
        'dispositivos_data': dispositivos_data,
        'logs': logs,
    }

    return render(request, 'appOne/reportes.html', context)