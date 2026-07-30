# appOne/decorators.py
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def admin_required(view_func):
    """
    Decorador para restringir el acceso únicamente a usuarios con rol 'Admin'
    o Superusuarios.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
            
        # Verifica si tiene rol de Admin o es superusuario de Django
        if getattr(request.user, 'rol', None) == 'Admin' or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
            
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('dashboard')
        
    return _wrapped_view