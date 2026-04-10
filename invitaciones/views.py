from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from .models import Grupoinvitacion, Invitado, EventoBoda
from django.http import HttpResponse
from openpyxl import Workbook
from urllib.parse import quote
from django.utils import timezone

# Importaciones de Django y librerías externas usadas en las vistas.

def inicio(request):
    # Renderiza la plantilla de inicio sin lógica adicional.
    return render(request, 'invitaciones/inicio.html')


# Muestra la invitación de un grupo y procesa las respuestas de asistencia.
def ver_invitacion(request, codigo):
    grupo = get_object_or_404(Grupoinvitacion, codigo=codigo)
    invitados = grupo.invitados.all()
    evento = EventoBoda.objects.first()

    if request.method == 'POST':
        for invitado in invitados:
            respuesta = request.POST.get(f'asistira_{invitado.id}')
            comentario = request.POST.get(f'comentario_{invitado.id}', '').strip()

            if respuesta == 'si':
                invitado.asistira = True
            elif respuesta == 'no':
                invitado.asistira = False
            else:
                invitado.asistira = None

            invitado.comentario = comentario
            invitado.save()

        grupo.confirmado = True
        grupo.save()

        # Evita que el formulario se reenvíe al recargar la página.
        return redirect('ver_invitacion', codigo=grupo.codigo)

    context = {
        'grupo': grupo,
        'invitados': invitados,
        'evento': evento,
    }

    return render(request, 'invitaciones/ver_invitacion.html', context)


def dashboard(request):
    # Calcula estadísticas generales de grupos e invitados.
    total_grupos = Grupoinvitacion.objects.count()
    total_invitados = Invitado.objects.count()
    total_asistiran = Invitado.objects.filter(asistira=True).count()
    total_no_asistiran = Invitado.objects.filter(asistira=False).count()
    total_pendientes = Invitado.objects.filter(asistira__isnull=True).count()

    porcentaje_asistencia = 0
    if total_invitados > 0:
        porcentaje_asistencia = round((total_asistiran / total_invitados) * 100, 2)

    grupos = Grupoinvitacion.objects.annotate(
        invitados_totales=Count('invitados'),
        asistentes_confirmados=Count('invitados', filter=Q(invitados__asistira=True)),
        no_asistentes=Count('invitados', filter=Q(invitados__asistira=False)),
        pendientes=Count('invitados', filter=Q(invitados__asistira__isnull=True)),
    ).order_by('-fecha_creacion')

    base_url = request.build_absolute_uri('/')[:-1]

    # Construye enlaces y mensajes personalizados para cada grupo.
    for grupo in grupos:
        link_invitacion = f"{base_url}/invitacion/{grupo.codigo}/"

        if grupo.tipo == "FAMILIAR":
            saludo = f"Hola Familia {grupo.nombre_grupo}"
        else:
            nombres = ", ".join([invitado.nombre for invitado in grupo.invitados.all()])
            saludo = f"Hola {nombres}"

        mensaje_invitacion = (
            f"{saludo}, te compartimos tu invitación digital.\n\n"
            f"Puedes verla aquí:\n{link_invitacion}"
        )

        mensaje_recordatorio = (
            f"{saludo}, este es un recordatorio de tu invitación digital.\n\n"
            f"Puedes revisarla aquí:\n{link_invitacion}"
        )

        telefono = (grupo.telefono_contacto or "").replace(" ", "").replace("+", "").replace("-", "")

        if telefono:
            grupo.whatsapp_invitacion_url = f"https://wa.me/{telefono}?text={quote(mensaje_invitacion)}"
            grupo.whatsapp_recordatorio_url = f"https://wa.me/{telefono}?text={quote(mensaje_recordatorio)}"
        else:
            grupo.whatsapp_invitacion_url = ""
            grupo.whatsapp_recordatorio_url = ""

        grupo.link_invitacion = link_invitacion

    context = {
        'total_grupos': total_grupos,
        'total_invitados': total_invitados,
        'total_asistiran': total_asistiran,
        'total_no_asistiran': total_no_asistiran,
        'total_pendientes': total_pendientes,
        'porcentaje_asistencia': porcentaje_asistencia,
        'grupos': grupos,
        'base_url': base_url,
    }

    return render(request, 'invitaciones/dashboard.html', context)

def exportar_excel(request):
    # Crea un libro de Excel en memoria para descargar las confirmaciones.
    wb = Workbook()
    ws = wb.active
    ws.title = 'Confirmaciones'

    encabezados = [
        'Grupo',
        'Tipo de invitación',
        'Cantidad máxima',
        'Invitado',
        'Asistirá',
        'Comentario',
        'Grupo confirmado',
        'Código'
    ]

    ws.append(encabezados)

    grupos = Grupoinvitacion.objects.prefetch_related('invitados').all().order_by('nombre_grupo')

    for grupo in grupos:
        invitados = grupo.invitados.all()

        if invitados.exists():
            for invitado in invitados:
                if invitado.asistira is True:
                    estado_asistencia = 'Sí'
                elif invitado.asistira is False:
                    estado_asistencia = 'No'
                else:
                    estado_asistencia = 'Pendiente'

                ws.append([
                    grupo.nombre_grupo,
                    grupo.tipo,
                    grupo.cantidad_maxima,
                    invitado.nombre,
                    estado_asistencia,
                    invitado.comentario or '',
                    'Sí' if grupo.confirmado else 'No',
                    str(grupo.codigo),
                ])
        else:
            ws.append([
                grupo.nombre_grupo,
                grupo.tipo,
                grupo.cantidad_maxima,
                '',
                'Pendiente',
                '',
                'Sí' if grupo.confirmado else 'No',
                str(grupo.codigo),
            ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=confirmaciones_boda.xlsx'

    wb.save(response)
    return response

def marcar_envio_invitacion(request, grupo_id):
    # Cambia el estado del grupo para indicar que la invitación está lista.
    grupo = get_object_or_404(Grupoinvitacion, id=grupo_id)
    grupo.estado_envio = 'INVITACION_PREPARADA'
    grupo.fecha_ultimo_envio = timezone.now()
    grupo.save()
    return redirect('dashboard')


# Cambia el estado del grupo cuando el recordatorio ya está preparado.
def marcar_recordatorio(request, grupo_id):
    grupo = get_object_or_404(Grupoinvitacion, id=grupo_id)
    grupo.estado_envio = 'RECORDATORIO_PREPARADO'
    grupo.fecha_ultimo_recordatorio = timezone.now()
    grupo.save()
    return redirect('dashboard')