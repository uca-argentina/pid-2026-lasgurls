from amistad import GestorAmistades


def test_enviar_solicitud():
    gestor=GestorAmistades()

    solicitud=gestor.enviarSolicitud(1,2)

    assert solicitud.estado=="Pendiente"
    assert len(gestor.solicitudes)==1

def test_aceptar_solicitud():
    gestor=GestorAmistades()
    solicitud=gestor.enviarSolicitud(1,2)

    solicitud.aceptar(2)

    assert solicitud.estado=="Aceptada"
    assert gestor.sonAmigos(1,2)
    assert len(gestor.solicitudesRecibidas(2))==0

def test_rechazar_solicitud():
    gestor=GestorAmistades()
    solicitud=gestor.enviarSolicitud(1,2)

    solicitud.rechazar(2)

    assert solicitud.estado=="Rechazada"
    assert not gestor.sonAmigos(1,2)
    assert len(gestor.solicitudesRecibidas(2))==0

def test_emisor_no_puede_aceptar():
    gestor=GestorAmistades()
    solicitud=gestor.enviarSolicitud(1,2)

    solicitud.aceptar(1)

    assert solicitud.estado=="Pendiente"
    assert not gestor.sonAmigos(1,2)
    assert len(gestor.solicitudesRecibidas(2))==1

def test_emisor_no_puede_rechazar():
    gestor=GestorAmistades()
    solicitud=gestor.enviarSolicitud(1,2)

    solicitud.rechazar(1)

    assert solicitud.estado=="Pendiente"
    assert len(gestor.solicitudesRecibidas(2))==1

def test_no_permite_enviarse_a_uno_mismo():
    gestor=GestorAmistades()

    resultado=gestor.enviarSolicitud(1,1)

    assert resultado is None
    assert len(gestor.solicitudes)==0

def test_no_permite_solicitud_duplicada():
    gestor=GestorAmistades()
    primera=gestor.enviarSolicitud(1,2)

    segunda=gestor.enviarSolicitud(1,2)

    assert segunda is None
    assert len(gestor.solicitudes)==1
    assert gestor.solicitudesRecibidas(2)==[primera]

def test_no_permite_solicitud_cruzada():
    gestor=GestorAmistades()
    primera=gestor.enviarSolicitud(1,2)

    segunda=gestor.enviarSolicitud(2,1)

    assert segunda is None
    assert len(gestor.solicitudes)==1
    assert gestor.solicitudesRecibidas(2)==[primera]
    assert gestor.solicitudesRecibidas(1)==[]

def test_no_permite_solicitudes_entre_amigos():
    gestor=GestorAmistades()
    solicitud=gestor.enviarSolicitud(1,2)
    solicitud.aceptar(2)

    mismoSentido=gestor.enviarSolicitud(1,2)
    sentidoInverso=gestor.enviarSolicitud(2,1)

    assert mismoSentido is None
    assert sentidoInverso is None
    assert len(gestor.solicitudes)==1
    assert gestor.sonAmigos(1,2)
    assert gestor.sonAmigos(2,1)

def test_no_permite_rechazar_una_solicitud_aceptada():
    gestor=GestorAmistades()
    solicitud=gestor.enviarSolicitud(1,2)
    solicitud.aceptar(2)

    solicitud.rechazar(2)

    assert solicitud.estado=="Aceptada"
    assert gestor.sonAmigos(1,2)
    assert len(gestor.solicitudesRecibidas(2))==0

def test_no_permite_aceptar_una_solicitud_rechazada():
    gestor=GestorAmistades()
    solicitud=gestor.enviarSolicitud(1,2)
    solicitud.rechazar(2)

    solicitud.aceptar(2)

    assert solicitud.estado=="Rechazada"
    assert not gestor.sonAmigos(1,2)
    assert len(gestor.solicitudesRecibidas(2))==0

def test_puede_reenviar_solicitud_despues_de_un_rechazo():
    gestor=GestorAmistades()
    primera=gestor.enviarSolicitud(1,2)
    primera.rechazar(2)

    segunda=gestor.enviarSolicitud(1,2)

    assert segunda is not None
    assert segunda.estado=="Pendiente"
    assert len(gestor.solicitudes)==2

def test_no_permite_rechazar_una_solicitud_ya_rechazada():
    gestor=GestorAmistades()
    solicitud=gestor.enviarSolicitud(1,2)
    solicitud.rechazar(2)

    solicitud.rechazar(2)

    assert solicitud.estado=="Rechazada"

def test_recibidas_solo_incluye_solicitudes_del_usuario():
    gestor=GestorAmistades()
    paraUsuario2=gestor.enviarSolicitud(1,2)
    paraUsuario3=gestor.enviarSolicitud(1,3)

    assert gestor.solicitudesRecibidas(2)==[paraUsuario2]
    assert gestor.solicitudesRecibidas(3)==[paraUsuario3]
    assert gestor.solicitudesRecibidas(1)==[]

def test_eliminar_amistad():
    gestor=GestorAmistades()
    solicitud=gestor.enviarSolicitud(1,2)
    solicitud.aceptar(2)

    solicitud.eliminar(1)

    assert solicitud.estado=="Eliminada"
    assert not gestor.sonAmigos(1,2)

def test_despues_de_eliminar_pueden_volver_a_ser_amigos():
    gestor=GestorAmistades()
    solicitud=gestor.enviarSolicitud(1,2)
    solicitud.aceptar(2)
    solicitud.eliminar(2)

    nueva=gestor.enviarSolicitud(2,1)

    assert nueva is not None
    assert nueva.estado=="Pendiente"

def test_no_se_elimina_una_solicitud_pendiente():
    gestor=GestorAmistades()
    solicitud=gestor.enviarSolicitud(1,2)

    solicitud.eliminar(1)

    assert solicitud.estado=="Pendiente"

def test_un_tercero_no_puede_eliminar_la_amistad():
    gestor=GestorAmistades()
    solicitud=gestor.enviarSolicitud(1,2)
    solicitud.aceptar(2)

    solicitud.eliminar(3)

    assert solicitud.estado=="Aceptada"
    assert gestor.sonAmigos(1,2)
