from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from tareas.models import TareaEvento


class TaskAgendaK51Tests(TestCase):
    """Regresión actualizada: desde K.8.7.1.2 Tarea nunca funciona como Cita."""
    def setUp(self):
        User = get_user_model()
        self.empresa = EmpresaSuscriptora.objects.create(nombre_comercial="Casa Agenda", slug="casa-agenda")
        self.planner = User.objects.create_user(username="planner_agenda", password="test123")
        MembresiaEmpresa.objects.create(empresa=self.empresa, usuario=self.planner, rol="WEDDING_PLANNER")
        self.evento = EventoBoda.objects.create(
            empresa=self.empresa, wedding_planner=self.planner, novio="A", novia="B",
            frase_portada="Test", mensaje_general="Test",
            fecha_misa=timezone.now() + timedelta(days=30), lugar_misa="Ceremonia",
            fecha_fiesta=timezone.now() + timedelta(days=30), lugar_fiesta="Recepcion",
        )
        self.client.force_login(self.planner)

    def test_task_never_becomes_appointment_even_if_legacy_hours_exist(self):
        today = timezone.localdate()
        task = TareaEvento.objects.create(
            evento=self.evento, titulo="Prueba legacy", fecha_inicio=today,
            hora_inicio=time(16, 30), fecha_limite=today, hora_fin=time(18, 0),
        )
        self.assertFalse(task.es_cita_agenda)

    def test_calendar_serializes_task_as_all_day_work_item(self):
        today = timezone.localdate()
        task = TareaEvento.objects.create(
            evento=self.evento, titulo="Trabajo pendiente", fecha_inicio=today,
            hora_inicio=time(9, 0), fecha_limite=today, hora_fin=time(11, 30),
        )
        response = self.client.get(reverse("calendario_eventos_json"), {"evento": self.evento.id})
        self.assertEqual(response.status_code, 200)
        event = next(item for item in response.json() if item["id"] == f"tarea-{task.id}")
        self.assertTrue(event["allDay"])
        self.assertEqual(event["extendedProps"]["tipo"], "Tarea")
        self.assertIsNone(event["end"])

    def test_date_only_task_stays_all_day(self):
        task = TareaEvento.objects.create(evento=self.evento, titulo="Confirmar banquete", fecha_limite=timezone.localdate())
        response = self.client.get(reverse("calendario_eventos_json"), {"evento": self.evento.id})
        event = next(item for item in response.json() if item["id"] == f"tarea-{task.id}")
        self.assertTrue(event["allDay"])
        self.assertEqual(event["start"], task.fecha_limite.isoformat())
