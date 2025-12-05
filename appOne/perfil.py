from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError
from django.contrib.auth import get_user_model

from appOne.models import Perfil  # Ajusta 'myapp' al nombre de tu app

class Command(createsuperuser.Command):
    help = 'Crea un superusuario con campos adicionales de Perfil'


def add_arguments(self, parser):
    super().add_arguments(parser)
    parser.add_argument('--nombre_completo', type=str, help='Nombre completo del superusuario')
    parser.add_argument('--correo_institucional', type=str, help='Correo institucional del superusuario')
    parser.add_argument('--codigo', type=str, help='Código o carné del superusuario')

def handle(self, *args, **options):
    UserModel = get_user_model()
    username = options[self.UserModel.USERNAME_FIELD]
    if not username:
        raise CommandError(f'Debes ingresar {self.UserModel.USERNAME_FIELD}')

    password = options.get('password')
    user = UserModel.objects.create_superuser(username=username, password=password)
    Perfil.objects.create(
        usuario=user,
        nombre_completo=options.get('nombre_completo'),
        correo_institucional=options.get('correo_institucional'),
        codigo=options.get('codigo'),
        rol='Administrativo',  # o puedes crear un rol especial para admin
    )
    self.stdout.write(self.style.SUCCESS(f'Superusuario {username} creado exitosamente.'))

