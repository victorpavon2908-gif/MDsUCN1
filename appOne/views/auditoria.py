from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from appOne.models import BitacoraAuditoria
from .utils import es_administrador



@login_required
def bitacora_auditoria(request):
    if not es_administrador(request.user):
        messages.error(request, "No tienes permisos para consultar la bitácora de auditoría.")
        return redirect('dashboardinicio')

    logs = BitacoraAuditoria.objects.all().select_related('usuario').order_by('-fecha_hora')[:250]
    return render(request, 'appOne/bitacora_auditoria.html', {'logs': logs})


# ============================
# --------- REPORTES ---------
# ============================

