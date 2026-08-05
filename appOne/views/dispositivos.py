from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from appOne.forms import DispositivoForm
from appOne.models import Dispositivo, Prestamo, BitacoraAuditoria
from .utils import es_administrador, registrar_auditoria

# ============================
# --- DISPOSITIVOS (CRUD) ----
# ============================

@login_required
def listardispositivos(request):
    dispositivos_disponibles = Dispositivo.objects.filter(estado=Dispositivo.ESTADO_DISPONIBLE)
    dispositivos_ocupados = Dispositivo.objects.filter(estado=Dispositivo.ESTADO_PRESTADO)
    dispositivos_mantenimiento = Dispositivo.objects.filter(estado=Dispositivo.ESTADO_MANTENIMIENTO)
    dispositivos_danados = Dispositivo.objects.filter(estado=Dispositivo.ESTADO_DANADO)

    prestamos_usuario = Prestamo.objects.filter(usuario=request.user)

    context = {
        "disponibles": dispositivos_disponibles,
        "ocupados": dispositivos_ocupados,
        "mantenimiento": dispositivos_mantenimiento,
        "danados": dispositivos_danados,
        "prestamos_usuario": prestamos_usuario,
    }

    return render(request, "appOne/Dispositivos.html", context)


@login_required
def agregar_dispositivo(request):
    if not es_administrador(request.user):
        messages.error(request, "No tienes permiso para agregar equipos al inventario.")
        return redirect('listardispositivos')

    if request.method == "POST":
        form = DispositivoForm(request.POST, request.FILES)
        if form.is_valid():
            dispositivo = form.save()
            registrar_auditoria(
                request, 
                BitacoraAuditoria.ACCION_CREAR, 
                "Dispositivos", 
                dispositivo.id, 
                f"Nuevo dispositivo creado: {dispositivo.nombre_dispositivo} ({dispositivo.codigo_inventario})"
            )
            messages.success(request, "Dispositivo agregado correctamente.")
            return redirect('listardispositivos')
        else:
            messages.error(request, "Error al guardar el dispositivo. Revisa el código de inventario o los datos ingresados.")
    else:
        form = DispositivoForm()

    return render(request, 'appOne/agregar_dispositivo.html', {'form': form})


@login_required
def editar_dispositivo(request, id):
    if not es_administrador(request.user):
        messages.error(request, "No tienes permiso para editar equipos.")
        return redirect('listardispositivos')

    dispositivo = get_object_or_404(Dispositivo, id=id)

    if request.method == "POST":
        form = DispositivoForm(request.POST, request.FILES, instance=dispositivo)
        if form.is_valid():
            form.save()
            registrar_auditoria(
                request, 
                BitacoraAuditoria.ACCION_EDITAR, 
                "Dispositivos", 
                dispositivo.id, 
                f"Edición de dispositivo: {dispositivo.nombre_dispositivo}"
            )
            messages.success(request, "Dispositivo actualizado correctamente.")
            return redirect('listardispositivos')
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = DispositivoForm(instance=dispositivo)

    return render(
        request,
        'appOne/form_editar_dispositivo.html',
        {
            'form': form,
            'dispositivo': dispositivo
        }
    )


@login_required
def eliminar_dispositivo(request, id):
    if not es_administrador(request.user):
        messages.error(request, "No tienes permiso para eliminar equipos.")
        return redirect('listardispositivos')

    dispositivo = get_object_or_404(Dispositivo, id=id)
    
    # Validar que no existan préstamos activos con este dispositivo
    prestamos_activos = Prestamo.objects.filter(
        dispositivo=dispositivo, 
        estado__in=[Prestamo.ESTADO_PENDIENTE, Prestamo.ESTADO_APROBADO]
    ).exists()

    if prestamos_activos:
        messages.error(
            request, 
            f"No se puede eliminar '{dispositivo.nombre_dispositivo}' porque tiene solicitudes o préstamos vigentes."
        )
        return redirect('listardispositivos')

    detalles = f"Eliminación de dispositivo: {dispositivo.nombre_dispositivo} ({dispositivo.codigo_inventario})"
    disp_id = dispositivo.id
    dispositivo.delete()

    registrar_auditoria(request, BitacoraAuditoria.ACCION_ELIMINAR, "Dispositivos", disp_id, detalles)

    messages.warning(request, "Dispositivo eliminado del sistema.")
    return redirect('listardispositivos')