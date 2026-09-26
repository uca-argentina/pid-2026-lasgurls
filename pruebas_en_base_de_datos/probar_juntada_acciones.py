
from dominio.juntada.juntada import Juntada
from base_datos.juntada_acciones import guardar, obtener_invitaciones_de_usuario, responder_invitacion

juntada = Juntada(
    organizador=1,
    fecha="20/09/2030",
    titulo_juntada="Prueba de guardado",
    hora_inicio="10:00",
    hora_fin="11:00",
    amigos_invitados=[2, 3],
)

juntada_id = guardar(juntada)
print("Juntada guardada! Con organizador:", juntada.organizador, "y juntada_id:", juntada_id)

resultados_invitaciones = obtener_invitaciones_de_usuario(2)
print("\nInvitaciones de usuario 2 ANTES de responder:")
for fila in resultados_invitaciones:
    print("id de invitacion:", fila.id, " id de juntada:", fila.juntada_id, " id del invitado:", fila.usuario_id, "estado:", fila.estado)

exito = responder_invitacion(juntada_id, 2, "Tal vez")
print("\n¿Se pudo responder la invitacion (Tal vez)?", exito)

resultados_invitaciones = obtener_invitaciones_de_usuario(2)
print("\nInvitaciones de usuario 2 DESPUES de responder Tal vez:")
for fila in resultados_invitaciones:
    print("id de invitacion:", fila.id, " id de juntada:", fila.juntada_id, " id del invitado:", fila.usuario_id, "estado:", fila.estado)


exito_si = responder_invitacion(juntada_id, 2, "Si")
print("\n¿Se pudo responder la invitacion (Si)? Esperado True ->", exito_si)

exito_no_deberia_cambiar = responder_invitacion(juntada_id, 2, "No")
print("¿Se pudo cambiar de 'Si' a 'No'? Esperado False ->", exito_no_deberia_cambiar)

resultados_invitaciones = obtener_invitaciones_de_usuario(2)
print("\nInvitaciones de usuario 2 DESPUES de intentar cambiar de Si a No:")
for fila in resultados_invitaciones:
    print("id de invitacion:", fila.id, " id de juntada:", fila.juntada_id, " id del invitado:", fila.usuario_id, "estado:", fila.estado)
