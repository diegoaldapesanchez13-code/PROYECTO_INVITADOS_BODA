from django.core.management.base import BaseCommand

from invitaciones.models import EventoBoda
from notificaciones.models import Notificacion
from presupuesto.models import GastoEvento
from tareas.models import TareaEvento


def usuarios_alerta_evento(evento):
    usuarios = []
    if evento.wedding_planner:
        usuarios.append(evento.wedding_planner)
    usuarios.extend(list(evento.clientes.all()))

    unicos = {}
    for usuario in usuarios:
        if usuario and usuario.pk:
            unicos[usuario.pk] = usuario
    return unicos.values()


def crear_si_no_existe(usuario, evento, titulo, mensaje, tipo, enlace):
    existe = Notificacion.objects.filter(
        usuario=usuario,
        evento=evento,
        tipo=tipo,
        enlace=enlace,
        leida=False,
    ).exists()
    if existe:
        return False

    Notificacion.objects.create(
        usuario=usuario,
        evento=evento,
        titulo=titulo,
        mensaje=mensaje,
        tipo=tipo,
        enlace=enlace,
    )
    return True


class Command(BaseCommand):
    help = 'Genera alertas no leidas para tareas y pagos vencidos por evento.'

    def add_arguments(self, parser):
        parser.add_argument('--evento', type=int, help='ID de evento especifico.')

    def handle(self, *args, **options):
        eventos = EventoBoda.objects.all()
        if options.get('evento'):
            eventos = eventos.filter(id=options['evento'])

        creadas = 0
        for evento in eventos:
            usuarios = list(usuarios_alerta_evento(evento))
            if not usuarios:
                continue

            for tarea in TareaEvento.objects.filter(evento=evento):
                if not tarea.esta_vencida:
                    continue
                enlace = f'/admin/tareas/tareaevento/{tarea.id}/change/'
                for usuario in usuarios:
                    if crear_si_no_existe(
                        usuario,
                        evento,
                        f'Tarea vencida: {tarea.titulo}',
                        f'La tarea "{tarea.titulo}" ya vencio y sigue en estado {tarea.get_estado_display()}.',
                        'TAREA',
                        enlace,
                    ):
                        creadas += 1

            for gasto in GastoEvento.objects.filter(evento=evento):
                if not gasto.esta_vencido:
                    continue
                enlace = f'/admin/presupuesto/gastoevento/{gasto.id}/change/'
                for usuario in usuarios:
                    if crear_si_no_existe(
                        usuario,
                        evento,
                        f'Pago vencido: {gasto.concepto}',
                        f'El gasto "{gasto.concepto}" tiene saldo pendiente de ${gasto.saldo_pendiente}.',
                        'PAGO',
                        enlace,
                    ):
                        creadas += 1

        self.stdout.write(self.style.SUCCESS(f'Alertas creadas: {creadas}'))
