COLORES = {
    "#6f86b8": "Azul",
    "#5f6b7a": "Pizarra",
    "#c0648f": "Rosa",
    "#8b74b8": "Lila",
    "#c4704f": "Terracota",
    "#3f8f8a": "Turquesa",
    "#d98a3d": "Naranja",
    "#8a6a4f": "Marrón",
}

CATEGORIAS_DE_FABRICA = [
    ("Facultad", "#6f86b8"),
    ("Trabajo", "#5f6b7a"),
    ("Social", "#c0648f"),
    ("Personal", "#8b74b8"),
]

LARGO_MAXIMO = 30


class Categoria:
    def __init__(self, nombre, color):
        self.nombre = (nombre or "").strip()
        self.color = (color or "").lower()
        self.validar()

    def validar(self):
        if not self.nombre:
            raise ValueError("La categoría tiene que tener un nombre")
        if len(self.nombre) > LARGO_MAXIMO:
            raise ValueError(f"El nombre de la categoría puede tener hasta {LARGO_MAXIMO} caracteres")
        if self.color not in COLORES:
            raise ValueError("Elegí uno de los colores disponibles")

    def se_llama_igual_que(self, otro_nombre):
        return self.nombre.casefold() == (otro_nombre or "").strip().casefold()
