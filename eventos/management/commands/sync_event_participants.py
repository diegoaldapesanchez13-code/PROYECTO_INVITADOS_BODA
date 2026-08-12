from django.core.management.base import BaseCommand

from eventos.services import sincronizar_participantes_legacy
from invitaciones.models import EventoBoda


class Command(BaseCommand):
    help = 'Sincroniza wedding_planner/clientes legacy hacia ParticipanteEvento.'

    def handle(self, *args, **options):
        creados = 0
        actualizados = 0
        for evento in EventoBoda.objects.all().iterator():
            resultado = sincronizar_participantes_legacy(evento)
            creados += resultado['creados']
            actualizados += resultado['actualizados']
        self.stdout.write(self.style.SUCCESS(
            f'Participantes sincronizados. creados={creados} actualizados={actualizados}'
        ))
