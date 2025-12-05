from django.contrib.auth.management.commands.createsuperuser import Command as BaseCommand

class Command(BaseCommand):
    help = "Crea un superusuario con campos extra"

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument('--nombre_completo', type=str)
        parser.add_argument('--codigo', type=str)

    def handle(self, *args, **options):
        # Preguntar si no se pasa como argumento
        if not options.get("nombre_completo"):
            options["nombre_completo"] = input("Nombre completo: ")

        if not options.get("codigo"):
            options["codigo"] = input("Código institucional: ")

        # Rol admin por defecto
        options["rol"] = "Admin"

        super().handle(*args, **options)
