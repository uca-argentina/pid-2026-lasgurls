from datetime import datetime
from dominio.modulo_utilidades.parseo_hora_fecha import parsear_fecha, parsear_hora
from dominio.modulo_utilidades.validador_de_tipo_evento import ValidadorDetipoEvento


class Agenda:
    def __init__(self, usuario_id, fecha, titulo_reunion, hora_inicio, hora_fin, ahora=None, categoria_id=None, visibilidad="ocupado", comparte_detalles=True):
        self.usuario_id = usuario_id
        self.categoria_id = categoria_id
        self.fecha = parsear_fecha(fecha)
        self.hora_inicio = parsear_hora(hora_inicio, "hora de inicio")
        self.hora_fin = parsear_hora(hora_fin, "hora de finalización")
        self.titulo_reunion = titulo_reunion
        self.visibilidad=visibilidad

        self.validar_agenda()
        ValidadorDetipoEvento().validar_que_pueda_mostrar_detalle(self.visibilidad, comparte_detalles)
        ValidadorDetipoEvento().validar_que_no_empiece_en_el_pasado(self.fecha, self.hora_inicio, ahora or datetime.now(), "El evento")

    def validar_agenda(self):
        ValidadorDetipoEvento().validar(
            fecha=self.fecha,
            hora_inicio=self.hora_inicio,
            hora_fin=self.hora_fin,
            titulo=self.titulo_reunion,
            responsable=self.usuario_id,
            visibilidad=self.visibilidad,
    )

    def registrar_agenda(self):
        return {
            "usuario": self.usuario_id,
            "titulo_reunion": self.titulo_reunion,
            "fecha": self.fecha.isoformat(),
            "hora_inicio": self.hora_inicio.isoformat(),
            "hora_fin": self.hora_fin.isoformat(),
            "visibilidad":self.visibilidad,
        }
