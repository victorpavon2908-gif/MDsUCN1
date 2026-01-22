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
            'imagen', 'descripcion', 'accesorios', 'observacion'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows':3}),
            'accesorios': forms.Textarea(attrs={'rows':2}),
            'observacion': forms.Textarea(attrs={'rows':2}),
        }




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
