
from datetime import date
from dominio.agenda.agenda import Agenda
from base_datos.agenda_acciones import guardar as guardar_agenda
from base_datos.disponibilidad_amigo_acciones import obtener_disponibilidad

FECHA_PRUEBA = "25/09/2030"

agenda_de_juan = Agenda(
    usuario_id=7,
    fecha=FECHA_PRUEBA,
    titulo_reunion="Dentista",
    hora_inicio="15:00",
    hora_fin="16:00",
)
guardar_agenda(agenda_de_juan)
print("Bloque de agenda de juan guardado.")

disponibilidad = obtener_disponibilidad(
    usuario_solicitante_id=1,
    amigos_ids=[7],
    desde=date(2030, 9, 25),
    hasta=date(2030, 9, 25),
)
print("\nDisponibilidad de juan el", FECHA_PRUEBA, "vista por Marina:")
for inicio, fin in disponibilidad[7]:
    print("Ocupado de", inicio, "a", fin)

print("\nProbando con alguien que NO es amigo de Marina (deberia fallar):")
try:
    obtener_disponibilidad(usuario_solicitante_id=1, amigos_ids=[8], desde=date(2030, 9, 25), hasta=date(2030, 9, 25))
    print("ERROR: no debería haber llegado hasta acá")
except ValueError as error:
    print("Bloqueado correctamente:", error)