import hashlib
import hmac
import math
from datetime import timedelta
from dominio.modulo_utilidades.rango_horario import rango_del_evento

SEGUNDOS_POR_CODIGO = 10
CODIGOS_ACEPTADOS = 3
ANTES_DEL_INICIO = timedelta(minutes=15)
DESPUES_DEL_FIN = timedelta(minutes=60)
DISTANCIA_MINIMA = 150
DISTANCIA_MAXIMA = 500
PRECISION_MAXIMA = 5000
RADIO_TIERRA = 6371000
PREFIJO = "JA1"


class Posicion:
    def __init__(self, latitud, longitud, precision):
        try:
            self.latitud = float(latitud)
            self.longitud = float(longitud)
            self.precision = float(precision)
        except (TypeError, ValueError):
            raise ValueError("Necesitamos tu ubicación para hacer el check-in")
        if not all(math.isfinite(valor) for valor in (self.latitud, self.longitud, self.precision)):
            raise ValueError("Necesitamos tu ubicación para hacer el check-in")
        if not -90 <= self.latitud <= 90 or not -180 <= self.longitud <= 180:
            raise ValueError("La ubicación no es válida")
        if not 0 <= self.precision <= PRECISION_MAXIMA:
            raise ValueError("Tu ubicación es muy imprecisa. Probá activar el GPS")

    def distancia_a(self, otra):
        lat1, lat2 = math.radians(self.latitud), math.radians(otra.latitud)
        delta_lat = lat2 - lat1
        delta_lon = math.radians(otra.longitud - self.longitud)
        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
        return 2 * RADIO_TIERRA * math.asin(math.sqrt(a))

    def esta_cerca_de(self, otra):
        tolerancia = min(max(DISTANCIA_MINIMA, self.precision + otra.precision), DISTANCIA_MAXIMA)
        return self.distancia_a(otra) <= tolerancia


def ventana_de_checkin(fecha, hora_inicio, hora_fin):
    inicio, fin = rango_del_evento(fecha, hora_inicio, hora_fin)
    return inicio - ANTES_DEL_INICIO, fin + DESPUES_DEL_FIN


def se_puede_hacer_checkin(fecha, hora_inicio, hora_fin, ahora):
    desde, hasta = ventana_de_checkin(fecha, hora_inicio, hora_fin)
    return desde <= ahora <= hasta


def _turno(ahora):
    return int(ahora.timestamp()) // SEGUNDOS_POR_CODIGO


def _firmar(secreto, contenido):
    return hmac.new(secreto.encode("utf-8"), contenido.encode("utf-8"), hashlib.sha256).hexdigest()[:24]


def generar_codigo(secreto, juntada_id, posicion, ahora):
    contenido = f"{PREFIJO}:{juntada_id}:{_turno(ahora)}:{posicion.latitud:.5f}:{posicion.longitud:.5f}:{round(posicion.precision)}"
    return f"{contenido}:{_firmar(secreto, contenido)}"


def leer_codigo(secreto, codigo, ahora):
    partes = (codigo or "").strip().split(":")
    if len(partes) != 7 or partes[0] != PREFIJO:
        raise ValueError("Ese QR no es de una juntada de JuntApp")
    contenido = ":".join(partes[:-1])
    if not hmac.compare_digest(_firmar(secreto, contenido), partes[-1]):
        raise ValueError("Ese QR no es de una juntada de JuntApp")
    juntada_id, turno = int(partes[1]), int(partes[2])
    if not 0 <= _turno(ahora) - turno < CODIGOS_ACEPTADOS:
        raise ValueError("El QR venció. Escaneá el que se ve ahora en la pantalla")
    return juntada_id, Posicion(partes[3], partes[4], partes[5])
