from datetime import datetime
VISIBILIDADES_VALIDAS = ("detalle", "ocupado", "oculto")

class ValidadorDetipoEvento:
    def validar(self, fecha, hora_inicio, hora_fin, titulo, responsable, visibilidad):
        if not responsable:
            raise ValueError("El campo responsable no puede estar vacío")

        if not titulo:
            raise ValueError("El campo título no puede estar vacío")

        if not fecha:
            raise ValueError("El campo fecha no puede estar vacío")

        if hora_inicio == hora_fin:
            raise ValueError("La hora de inicio y la de finalización no pueden ser iguales")
        
        if visibilidad not in VISIBILIDADES_VALIDAS:
            raise ValueError("La visibilidad tiene que ser: detalle, ocupado u oculto")

    def validar_que_no_empiece_en_el_pasado(self, fecha, hora_inicio, ahora, nombre):
        if datetime.combine(fecha, hora_inicio) < ahora.replace(second=0, microsecond=0):
            raise ValueError(f"{nombre} no puede empezar en un horario que ya pasó")

    def validar_que_pueda_mostrar_detalle(self, visibilidad, comparte_detalles):
        if visibilidad == "detalle" and not comparte_detalles:
            raise ValueError("Para mostrar el título activá «Compartir detalles» en Mi perfil")
