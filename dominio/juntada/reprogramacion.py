from datetime import datetime
from dominio.modulo_utilidades.parseo_hora_fecha import parsear_fecha, parsear_hora
from dominio.modulo_utilidades.validador_de_tipo_evento import ValidadorDetipoEvento


class Reprogramacion:
    def __init__(self, fecha, hora_inicio, hora_fin, ahora=None):
        self.fecha = parsear_fecha(fecha)
        self.hora_inicio = parsear_hora(hora_inicio, "hora de inicio")
        self.hora_fin = parsear_hora(hora_fin, "hora de finalización")

        if self.hora_inicio == self.hora_fin:
            raise ValueError("La hora de inicio y la de finalización no pueden ser iguales")
        ValidadorDetipoEvento().validar_que_no_empiece_en_el_pasado(self.fecha, self.hora_inicio, ahora or datetime.now(), "La juntada")

    def validar_que_cambie(self, fecha, hora_inicio, hora_fin):
        if (self.fecha, self.hora_inicio, self.hora_fin) == (fecha, hora_inicio, hora_fin):
            raise ValueError("Elegí una fecha u horario distinto al actual")
