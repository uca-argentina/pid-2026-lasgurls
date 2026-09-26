
from dominio.agenda.agenda import Agenda
from base_datos.agenda_acciones import guardar, obtener_por_usuario

agenda = Agenda(usuario_id=1, fecha="20/09/2030", titulo_reunion="Prueba de guardado", hora_inicio="10:00", hora_fin="11:00")

guardar(agenda)
print("Agenda guardada!")

resultados = obtener_por_usuario(1)
for fila, categoria, _ in resultados:
    print(fila.id, fila.titulo, fila.fecha, fila.hora_inicio, fila.hora_fin, categoria)
