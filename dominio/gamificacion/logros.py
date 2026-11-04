from collections import Counter

RACHA_CON_FUEGO = 2

DESBLOQUEOS = [
    {"clave": "color", "nombre": "Color del avatar", "mide": "cumplidas", "meta": 1},
    {"clave": "forma", "nombre": "Forma del avatar", "mide": "racha", "meta": 3},
    {"clave": "marco", "nombre": "Marco del avatar", "mide": "racha", "meta": 5},
    {"clave": "titulo", "nombre": "Nombre con degradé y título", "mide": "racha", "meta": 10},
]

COLORES_AVATAR = {
    "#c46f4e": "Terracota",
    "#d9a441": "Mostaza",
    "#5b7fa6": "Azul",
    "#8c6bb1": "Lavanda",
    "#d16d8e": "Frambuesa",
    "#3f8f8a": "Petróleo",
    "#2b2b26": "Carbón",
    "#6fb3d2": "Celeste",
}
FORMAS = {"circulo": "Círculo", "hexagono": "Hexágono", "estrella": "Estrella", "flor": "Flor"}
MARCOS = {"dorado": "Dorado", "arcoiris": "Arcoíris", "noche": "Noche"}
TITULOS = ["Nunca falla", "Alma de la juntada", "Organiza de todo", "Siempre llega", "Leyenda del grupo"]


class Logros:
    def __init__(self, historial):
        self.cumplidas = sum(1 for cumplio in historial if cumplio)
        self.faltas = len(historial) - self.cumplidas
        self.racha_actual = 0
        self.racha_maxima = 0
        for cumplio in historial:
            self.racha_actual = self.racha_actual + 1 if cumplio else 0
            self.racha_maxima = max(self.racha_maxima, self.racha_actual)

    @property
    def palabra(self):
        total = self.cumplidas + self.faltas
        return round(self.cumplidas / total * 100) if total else None

    @property
    def tiene_fuego(self):
        return self.racha_actual >= RACHA_CON_FUEGO

    def _valor(self, desbloqueo):
        return self.cumplidas if desbloqueo["mide"] == "cumplidas" else self.racha_maxima

    def desbloqueados(self):
        return {desbloqueo["clave"] for desbloqueo in DESBLOQUEOS if self._valor(desbloqueo) >= desbloqueo["meta"]}

    def progreso(self):
        return [{
            **desbloqueo,
            "logrado": self._valor(desbloqueo) >= desbloqueo["meta"],
            "avance": min(self._valor(desbloqueo), desbloqueo["meta"]),
        } for desbloqueo in DESBLOQUEOS]

    def proximo(self):
        for desbloqueo in self.progreso():
            if not desbloqueo["logrado"]:
                if desbloqueo["mide"] == "cumplidas":
                    faltan = desbloqueo["meta"] - self.cumplidas
                else:
                    faltan = desbloqueo["meta"] - self.racha_actual
                return {**desbloqueo, "faltan": faltan}
        return None


def _elegido(valor):
    return (valor or "").strip() or None


class Estilo:
    def __init__(self, color=None, forma=None, marco=None, titulo=None, degrade=False, desbloqueados=frozenset()):
        self.color = _elegido(color)
        self.forma = _elegido(forma)
        self.marco = _elegido(marco)
        self.titulo = _elegido(titulo)
        self.degrade = bool(degrade)
        self._validar(self.color, COLORES_AVATAR, "color", "Elegí un color de la lista", desbloqueados)
        self._validar(self.forma, FORMAS, "forma", "Elegí una forma de la lista", desbloqueados)
        self._validar(self.marco, MARCOS, "marco", "Elegí un marco de la lista", desbloqueados)
        self._validar(self.titulo, TITULOS, "titulo", "Elegí un título de la lista", desbloqueados)
        if self.degrade and "titulo" not in desbloqueados:
            raise ValueError("Todavía no desbloqueaste el nombre con degradé")

    @staticmethod
    def _validar(valor, opciones, clave, mensaje, desbloqueados):
        if valor is None:
            return
        if valor not in opciones:
            raise ValueError(mensaje)
        if clave not in desbloqueados:
            nombre = next(desbloqueo["nombre"] for desbloqueo in DESBLOQUEOS if desbloqueo["clave"] == clave)
            raise ValueError(f"Todavía no desbloqueaste: {nombre.lower()}")


def resumen_del_mes(juntadas, anio, mes):
    del_mes = [juntada for juntada in juntadas if juntada["inicio"].year == anio and juntada["inicio"].month == mes]
    veces = Counter()
    nombres = {}
    for juntada in del_mes:
        for usuario_id, nombre in juntada["companeros"]:
            veces[usuario_id] += 1
            nombres[usuario_id] = nombre
    mas_vista = None
    if veces:
        usuario_id, cantidad = min(veces.items(), key=lambda par: (-par[1], nombres[par[0]]))
        mas_vista = {"nombre": nombres[usuario_id], "veces": cantidad}
    return {
        "cantidad": len(del_mes),
        "organizadas": sum(1 for juntada in del_mes if juntada["organizada"]),
        "personas": len(veces),
        "mas_vista": mas_vista,
    }
