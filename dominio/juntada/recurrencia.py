from datetime import date, timedelta
from dominio.modulo_utilidades.parseo_hora_fecha import parsear_fecha

FRECUENCIAS = {
    "diaria": "Todos los días",
    "semanal": "Cada semana",
    "quincenal": "Cada dos semanas",
    "mensual": "Cada mes",
}

DIAS_EN_PLURAL = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábados", "domingos"]


def texto_de_repeticion(frecuencia, fecha):
    if frecuencia == "semanal":
        return f"Todos los {DIAS_EN_PLURAL[fecha.weekday()]}"
    return FRECUENCIAS.get(frecuencia)


def un_anio_despues(fecha):
    try:
        return fecha.replace(year=fecha.year + 1)
    except ValueError:
        return fecha.replace(year=fecha.year + 1, day=28)


def sumar_meses(fecha, meses):
    total = fecha.month - 1 + meses
    try:
        return date(fecha.year + total // 12, total % 12 + 1, fecha.day)
    except ValueError:
        return None


class Recurrencia:
    def __init__(self, frecuencia, hasta):
        if frecuencia not in FRECUENCIAS:
            raise ValueError("Elegí cada cuánto se repite la juntada")
        if not hasta:
            raise ValueError("Elegí hasta qué fecha se repite la juntada")
        self.frecuencia = frecuencia
        self.hasta = parsear_fecha(hasta)

    def fechas_desde(self, inicio):
        if self.hasta <= inicio:
            raise ValueError("La repetición tiene que terminar después de la primera fecha")
        if self.hasta > un_anio_despues(inicio):
            raise ValueError("La juntada se puede repetir hasta un año después de la primera fecha")

        if self.frecuencia == "mensual":
            fechas = [sumar_meses(inicio, meses) for meses in range(13)]
            return [fecha for fecha in fechas if fecha is not None and fecha <= self.hasta]

        paso = timedelta(days={"diaria": 1, "semanal": 7, "quincenal": 14}[self.frecuencia])
        fechas = []
        fecha = inicio
        while fecha <= self.hasta:
            fechas.append(fecha)
            fecha += paso
        return fechas
