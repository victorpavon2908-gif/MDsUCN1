from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError
from django.contrib.auth import get_user_model


class Command(createsuperuser.Command):
    help = 'Crea un superusuario con los campos personalizados del modelo Usuario'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--nombre_completo', type=str, help='Nombre completo del superusuario')
        parser.add_argument('--codigo', type=str, help='Código o carné del superusuario')

    def handle(self, *args, **options):
        UserModel = get_user_model()
        
        nombre_completo = options.get('nombre_completo') or 'Administrador Principal'
        codigo = options.get('codigo') or 'ADMIN001'

        options['nombre_completo'] = nombre_completo
        options['codigo'] = codigo
        options['rol'] = 'Admin'

        super().handle(*args, **options)