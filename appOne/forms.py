from django import forms
from .models import Usuario , Dispositivo, Prestamo


class RegistroForm(forms.ModelForm):
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Ingrese su contraseña"})
    )
    confirmar_password = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Repita su contraseña"})
    )

    class Meta:
        model = Usuario
        fields = ['nombre_completo', 'correo_institucional', 'codigo', 'rol']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmar = cleaned_data.get("confirmar_password")

        if password and confirmar and password != confirmar:
            self.add_error('confirmar_password', "Las contraseñas no coinciden.")
        
        return cleaned_data

    def save(self, commit=True):
        # Crear instancia del usuario sin guardar aún
        usuario = super().save(commit=False)

        # Asignar el password cifrado
        usuario.set_password(self.cleaned_data.get("password"))

        # Asignar un username automático basado en el código (evita UNIQUE constraint)
        usuario.username = self.cleaned_data.get("codigo")

        # Usuario nuevo no está activo hasta aprobación
        usuario.is_active = False

        if commit:
            usuario.save()
        return usuario


class DispositivoForm(forms.ModelForm):
    class Meta:
        model = Dispositivo
        fields = [
            'nombre_dispositivo', 'marca', 'codigo_inventario', 
            'estado', 'descripcion', 'accesorios', 'observacion', 'imagen'
        ]
        labels = {
            'nombre_dispositivo': 'Nombre del Dispositivo',
            'marca': 'Marca',
            'codigo_inventario': 'Código de Inventario',
            'estado': 'Estado del Dispositivo',
            'descripcion': 'Descripción del Equipo',
            'accesorios': 'Accesorios Incluidos',
            'observacion': 'Observaciones Adicionales',
            'imagen': 'Fotografía del Equipo',
        }
        widgets = {
            'nombre_dispositivo': forms.TextInput(attrs={'placeholder': 'Ej. Laptop Lenovo ThinkPad'}),
            'marca': forms.TextInput(attrs={'placeholder': 'Ej. Lenovo'}),
            'codigo_inventario': forms.TextInput(attrs={'placeholder': 'Ej. INV-2026-001'}),
            'estado': forms.Select(),
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'accesorios': forms.Textarea(attrs={'rows': 2}),
            'observacion': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Excluir la opción 'prestado' del select de estados
        if 'estado' in self.fields:
            opciones_permitidas = [
                choice for choice in Dispositivo.ESTADO_CHOICES 
                if choice[0] != Dispositivo.ESTADO_PRESTADO
            ]
            self.fields['estado'].choices = opciones_permitidas


class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = [
            'motivo',
            'fecha_uso',
            'hora_inicio',
            'hora_entrega'
        ]
        widgets = {
            'motivo': forms.Textarea(attrs={'rows': 3}),
        }
