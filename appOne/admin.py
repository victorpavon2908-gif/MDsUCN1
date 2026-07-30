from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Dispositivo, Prestamo


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Información Institucional', {'fields': ('nombre_completo', 'codigo', 'rol')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Institucional', {'fields': ('nombre_completo', 'correo_institucional', 'codigo', 'rol')}),
    )
    list_display = ('correo_institucional', 'nombre_completo', 'codigo', 'rol', 'is_active', 'is_staff')
    search_fields = ('correo_institucional', 'nombre_completo', 'codigo')
    ordering = ('correo_institucional',)


@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    list_display = ('nombre_dispositivo', 'marca', 'codigo_inventario')
    search_fields = ('nombre_dispositivo', 'codigo_inventario', 'marca')


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ('dispositivo', 'usuario', 'fecha_uso', 'hora_inicio', 'hora_entrega', 'estado')
    list_filter = ('estado', 'fecha_uso')
    search_fields = ('dispositivo__nombre_dispositivo', 'usuario__nombre_completo')