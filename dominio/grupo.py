largoMaximo=30


class Grupo:
    def __init__(self,creadorID,nombre,miembrosIDs):
        self.creadorID=creadorID
        self.nombre=(nombre or "").strip()
        self.miembrosIDs=miembrosIDs or []
        self.validar()

    def validar(self):
        if not self.nombre:
            raise ValueError("El grupo tiene que tener un nombre")
        if len(self.nombre)>largoMaximo:
            raise ValueError(f"El nombre del grupo puede tener hasta {largoMaximo} caracteres")
        if not self.miembrosIDs:
            raise ValueError("El grupo tiene que tener al menos un amigo")
        if self.creadorID in self.miembrosIDs:
            raise ValueError("No te podes agregar a vos misma a un grupo")
