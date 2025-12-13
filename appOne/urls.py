from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name="login"),
    path('salir/', views.logout_view, name="logout"),
    path('registro/', views.registro, name='registro'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboardinicio/', views.layaut_Principal, name='dashboardinicio'),
    # Panel admin
    path('panel/usuarios/', views.panel_usuarios, name='panel_usuarios'),
    path('panel/usuarios/aprobar/<int:id>/', views.aprobar_usuario, name='aprobar_usuario'),
    path('panel/usuarios/rechazar/<int:id>/', views.rechazar_usuario, name='rechazar_usuario'),
    path('usuarios/eliminar/<int:id>/', views.eliminar_usuario, name='eliminar_usuario'),
    # Dispositivos
    path('listardispositivos/', views.listardispositivos, name='listardispositivos'),
    path('dispositivos/agregar/', views.agregar_dispositivo, name='agregar_dispositivo'),
    path('dispositivos/editar/<int:id>/', views.editar_dispositivo, name='editar_dispositivo'),
    path('dispositivos/eliminar/<int:id>/', views.eliminar_dispositivo, name='eliminar_dispositivo'),
    # configuracion
    path('panel/configuracion/', views.panel_config, name='panel_config'),

]
