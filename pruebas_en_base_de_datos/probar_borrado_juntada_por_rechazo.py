
import time

from dominio.usuario import Usuario
from dominio.juntada.juntada import Juntada
from base_datos.usuario_acciones import guardar as guardar_usuario, buscar_por_email
from base_datos.juntada_acciones import (
    guardar as guardar_juntada,
    obtener_por_id,
    obtener_invitados_de_juntada,
    responder_invitacion,
)
from base_datos.configuracion import Session
from base_datos.usuario_tabla import UsuarioTabla

sufijo = str(int(time.time()))
organizador = Usuario(f"org_borrado_{sufijo}@test.com", "Abcdefg1!", "Organizador Prueba")
invitado_1 = Usuario(f"inv1_borrado_{sufijo}@test.com", "Abcdefg1!", "Invitado Uno")
invitado_2 = Usuario(f"inv2_borrado_{sufijo}@test.com", "Abcdefg1!", "Invitado Dos")

guardar_usuario(organizador)
guardar_usuario(invitado_1)
guardar_usuario(invitado_2)

organizador_id = buscar_por_email(organizador.email).id
invitado_1_id = buscar_por_email(invitado_1.email).id
invitado_2_id = buscar_por_email(invitado_2.email).id

try:
    juntada = Juntada(
        organizador=organizador_id,
        fecha="20/09/2030",
        titulo_juntada="Prueba de borrado por rechazo",
        hora_inicio="10:00",
        hora_fin="11:00",
        amigos_invitados=[invitado_1_id, invitado_2_id],
    )
    juntada_id = guardar_juntada(juntada)
    print("Juntada creada con id:", juntada_id)

    responder_invitacion(juntada_id, invitado_1_id, "No")
    assert obtener_por_id(juntada_id) is not None, "La juntada no debería borrarse con un solo rechazo"
    assert len(obtener_invitados_de_juntada(juntada_id)) == 2, "Los invitados no deberían borrarse todavía"
    print("OK: rechazo parcial -> la juntada sigue existiendo")

    responder_invitacion(juntada_id, invitado_2_id, "No")
    assert obtener_por_id(juntada_id) is None, "La juntada debería borrarse cuando todos rechazan"
    assert len(obtener_invitados_de_juntada(juntada_id)) == 0, "Los invitados deberían borrarse junto con la juntada"
    print("OK: rechazo total -> la juntada se borró junto con sus invitados")

    print("\nTodas las verificaciones pasaron correctamente.")
finally:
    with Session() as sesion:
        sesion.query(UsuarioTabla).filter(
            UsuarioTabla.id.in_([organizador_id, invitado_1_id, invitado_2_id])
        ).delete(synchronize_session=False)
        sesion.commit()
    print("Usuarios de prueba eliminados.")
