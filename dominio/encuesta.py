from datetime import datetime
from dominio.modulo_utilidades.parseo_hora_fecha import parsear_fecha, parsear_hora
from dominio.modulo_utilidades.validador_de_tipo_evento import ValidadorDetipoEvento
from dominio.ubicacion import Ubicacion
from dominio.juntada.recurrencia import Recurrencia, un_anio_despues

MINIMO_OPCIONES = 2
MAXIMO_OPCIONES = 5
ABIERTA = "abierta"
CERRADA = "cerrada"


class OpcionEncuesta:
    def __init__(self, fecha, hora_inicio, hora_fin, ahora=None):
        self.fecha = parsear_fecha(fecha)
        self.hora_inicio = parsear_hora(hora_inicio, "hora de inicio")
        self.hora_fin = parsear_hora(hora_fin, "hora de finalización")
        if self.hora_inicio == self.hora_fin:
            raise ValueError("La hora de inicio y la de finalización no pueden ser iguales")
        ValidadorDetipoEvento().validar_que_no_empiece_en_el_pasado(
            self.fecha, self.hora_inicio, ahora or datetime.now(), "Una opción de la encuesta")

    @classmethod
    def desde_datos(cls, fecha, hora_inicio, hora_fin):
        """Reconstruye una opción ya guardada (fecha y horas ya parseadas), sin validar."""
        opcion = cls.__new__(cls)
        opcion.fecha, opcion.hora_inicio, opcion.hora_fin = fecha, hora_inicio, hora_fin
        return opcion

    def clave(self):
        return (self.fecha, self.hora_inicio, self.hora_fin)


class Encuesta:
    def __init__(self, organizador, titulo, opciones, invitados, ahora=None, ubicacion="", repeticion=None):
        """opciones: lista de tuplas (fecha "DD/MM/AAAA", hora_inicio "HH:MM", hora_fin "HH:MM")."""
        if not organizador:
            raise ValueError("El campo organizador no puede estar vacío")
        if not titulo or not titulo.strip():
            raise ValueError("El campo título no puede estar vacío")
        self.organizador = organizador
        self.titulo = titulo.strip()
        self.invitados = self._validar_invitados(organizador, invitados)
        self.opciones = self._validar_opciones(opciones, ahora)
        self.ubicacion = Ubicacion(ubicacion).texto
        if repeticion not in (None, "semanal"):
            raise ValueError("La encuesta solo se puede repetir todas las semanas")
        self.repeticion = repeticion
        self.votos = {}  # usuario -> set de índices de opciones
        self.estado = ABIERTA
        self.opcion_confirmada = None

    @classmethod
    def desde_datos(cls, organizador, titulo, opciones, invitados, votos, estado, ubicacion="", repeticion=None):
        """Reconstruye una encuesta ya guardada (opciones: lista de OpcionEncuesta; votos: {usuario: {índices}})."""
        encuesta = cls.__new__(cls)
        encuesta.organizador, encuesta.titulo = organizador, titulo
        encuesta.invitados, encuesta.opciones = list(invitados), list(opciones)
        encuesta.votos, encuesta.estado = {u: set(i) for u, i in votos.items()}, estado
        encuesta.opcion_confirmada = None
        encuesta.ubicacion = ubicacion or ""
        encuesta.repeticion = repeticion
        return encuesta

    @staticmethod
    def _validar_invitados(organizador, invitados):
        invitados = list(dict.fromkeys(invitados or []))
        if not invitados:
            raise ValueError("La encuesta debe tener al menos un invitado")
        if organizador in invitados:
            raise ValueError("El organizador no puede invitarse a sí mismo")
        return invitados

    @staticmethod
    def _validar_opciones(opciones, ahora):
        opciones = opciones or []
        if len(opciones) < MINIMO_OPCIONES:
            raise ValueError(f"La encuesta debe tener al menos {MINIMO_OPCIONES} opciones")
        if len(opciones) > MAXIMO_OPCIONES:
            raise ValueError(f"La encuesta puede tener como máximo {MAXIMO_OPCIONES} opciones")
        ahora = ahora or datetime.now()
        creadas = [OpcionEncuesta(f, hi, hf, ahora) for f, hi, hf in opciones]
        if len({o.clave() for o in creadas}) != len(creadas):
            raise ValueError("Hay opciones repetidas en la encuesta")
        return creadas

    def _validar_abierta(self):
        if self.estado != ABIERTA:
            raise ValueError("La encuesta ya está cerrada")

    def votar(self, usuario, indices_de_opciones):
        """Reemplaza el voto anterior del usuario por las opciones indicadas."""
        self._validar_abierta()
        if usuario != self.organizador and usuario not in self.invitados:
            raise ValueError("Solo el organizador y los invitados pueden votar")
        indices = set(indices_de_opciones or [])
        if not indices:
            raise ValueError("Tenés que elegir al menos una opción")
        if any(i < 0 or i >= len(self.opciones) for i in indices):
            raise ValueError("Opción inexistente")
        self.votos[usuario] = indices

    def cantidad_de_votos(self, indice):
        return sum(1 for marcadas in self.votos.values() if indice in marcadas)

    def resultados(self):
        return [self.cantidad_de_votos(i) for i in range(len(self.opciones))]

    def opciones_ganadoras(self):
        """Índices de las opciones más votadas (varias si hay empate; vacío si nadie votó)."""
        resultados = self.resultados()
        maximo = max(resultados)
        if maximo == 0:
            return []
        return [i for i, v in enumerate(resultados) if v == maximo]

    def cerrar(self, usuario):
        self._validar_organizador(usuario)
        self._validar_abierta()
        self.estado = CERRADA

    def confirmar(self, usuario, indice):
        """Cierra la encuesta eligiendo una opción entre las más votadas. Devuelve la OpcionEncuesta."""
        self._validar_organizador(usuario)
        self._validar_abierta()
        ganadoras = self.opciones_ganadoras()
        if not ganadoras:
            raise ValueError("No se puede confirmar una opción sin votos")
        if indice not in ganadoras:
            raise ValueError("Solo se puede confirmar una de las opciones más votadas")
        self.estado = CERRADA
        self.opcion_confirmada = self.opciones[indice]
        return self.opcion_confirmada

    def recurrencia_de(self, opcion):
        if self.repeticion is None:
            return None
        return Recurrencia(self.repeticion, un_anio_despues(opcion.fecha).strftime("%d/%m/%Y"))

    def _validar_organizador(self, usuario):
        if usuario != self.organizador:
            raise ValueError("Solo el organizador puede hacer esto")