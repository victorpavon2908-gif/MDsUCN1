from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # =========================
    # AUTH
    # =========================
    path('', views.login_view, name="login"),
    path('salir/', views.logout_view, name="logout"),
    path('registro/', views.registro, name='registro'),

    # =========================
    # DASHBOARD
    # =========================
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboardinicio/', views.layaut_Principal, name='dashboardinicio'),

    # =========================
    # CALENDARIO & API
    # =========================
    path('calendario/', views.calendario_reservas, name='calendario_reservas'),
    path('api/reservas-eventos/', views.api_reservas_eventos, name='api_reservas_eventos'),

    # =========================
    # PANEL ADMIN & AUDITORÍA
    # =========================
    path('panel/usuarios/', views.panel_usuarios, name='panel_usuarios'),
    path('panel/usuarios/aprobar/<int:id>/', views.aprobar_usuario, name='aprobar_usuario'),
    path('panel/usuarios/rechazar/<int:id>/', views.rechazar_usuario, name='rechazar_usuario'),
    path('panel/configuracion/', views.panel_config, name='configuracion'),
    path('usuarios/eliminar/<int:id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('auditoria/', views.bitacora_auditoria, name='bitacora_auditoria'),

    # =========================
    # DISPOSITIVOS
    # =========================
    path('dispositivos/', views.listardispositivos, name='listardispositivos'),
    path('dispositivos/agregar/', views.agregar_dispositivo, name='agregar_dispositivo'),
    path('dispositivos/editar/<int:id>/', views.editar_dispositivo, name='editar_dispositivo'),
    path('dispositivos/eliminar/<int:id>/', views.eliminar_dispositivo, name='eliminar_dispositivo'),

    # =========================
    # PRÉSTAMOS
    # =========================
    path('prestamos/', views.solicitudes_prestamos, name='solicitudes_prestamos'),
    path('prestamos/crear/', views.crear_prestamo, name='crear_prestamo'),
    path('prestamo/modal/<int:id>/', views.modal_prestamo, name="modal_prestamo"),
    path('prestamos/aprobar/<int:id>/', views.aprobar_prestamo, name='aprobar_prestamo'),
    path('devolver_prestamo/<int:id>/', views.devolver_prestamo, name='devolver_prestamo'),
    path('prestamos/rechazar/<int:id>/', views.rechazar_prestamo, name='rechazar_prestamo'),
    path('eliminar-historial/', views.eliminar_historial_prestamos, name='eliminar_historial_prestamos'),
    path('restaurar-historial/', views.restaurar_historial_todos, name='restaurar_historial_todos'), # <-- ¡Agregada aquí!
    path('reportes/', views.reportes, name='reportes'),

    # =========================
    # CONFIGURACIÓN (AJAX)
    # =========================
    path("configuracion/inicio/", views.config_inicio, name="config_inicio"),
    path("configuracion/perfil/", views.config_perfil, name="config_perfil"),
    path("configuracion/seguridad/", views.config_seguridad, name="config_seguridad"),
    path("configuracion/database/", views.config_database, name="config_database"),

    # =========================
    # PASSWORD RESET
    # =========================
    path('reset_password/', 
         auth_views.PasswordResetView.as_view(template_name="appOne/registration/password_reset.html"), 
         name="reset_password"),
         
    path('reset_password_sent/', 
         auth_views.PasswordResetDoneView.as_view(template_name="appOne/registration/password_reset_sent.html"), 
         name="password_reset_done"),
         
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="appOne/registration/password_reset_form.html"), 
         name="password_reset_confirm"),
         
    path('reset_password_complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="appOne/registration/password_reset_done.html"), 
         name="password_reset_complete"),
]