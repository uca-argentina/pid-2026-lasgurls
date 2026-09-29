from datetime import datetime
from dominio.modulo_utilidades.parseo_hora_fecha import parsear_fecha, parsear_hora
from dominio.modulo_utilidades.validador_de_tipo_evento import ValidadorDetipoEvento


class Juntada:
    def __init__(self, organizador, fecha, titulo_juntada, hora_inicio, hora_fin, amigos_invitados, ahora=None, categoria_id=None, visibilidad="ocupado"):
        self.organizador = organizador
        self.categoria_id = categoria_id
        self.fecha = parsear_fecha(fecha)
        self.hora_inicio = parsear_hora(hora_inicio, "hora de inicio")
        self.hora_fin = parsear_hora(hora_fin, "hora de finalización")
        self.titulo_juntada = titulo_juntada
        self.amigos_invitados = amigos_invitados
        self.visibilidad= visibilidad

        self.validar_juntada()
        self.validar_amigos_invitados()
        ValidadorDetipoEvento().validar_que_no_empiece_en_el_pasado(self.fecha, self.hora_inicio, ahora or datetime.now(), "La juntada")

    def validar_juntada(self):
        ValidadorDetipoEvento().validar(
            fecha=self.fecha,
            hora_inicio=self.hora_inicio,
            hora_fin=self.hora_fin,
            titulo=self.titulo_juntada,
            responsable=self.organizador,
            visibilidad=self.visibilidad,
        )

    def validar_amigos_invitados(self):
        if not self.amigos_invitados:
            raise ValueError("La juntada debe tener al menos un invitado")

        if self.organizador in self.amigos_invitados:
            raise ValueError("El organizador no puede invitarse a sí mismo")

    def registrar_juntada(self):
        return {
            "organizador": self.organizador,
            "titulo_juntada": self.titulo_juntada,
            "fecha": self.fecha.isoformat(),
            "hora_inicio": self.hora_inicio.isoformat(),
            "hora_fin": self.hora_fin.isoformat(),
            "amigos_invitados": self.amigos_invitados,
            "visibilidad": self.visibilidad,
        }
