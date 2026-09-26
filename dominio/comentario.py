largoMaximo=500


class Comentario:
    def __init__(self,juntadaID,usuarioID,texto):
        self.juntadaID=juntadaID
        self.usuarioID=usuarioID
        self.texto=(texto or "").strip()
        self.validar()

    def validar(self):
        if not self.texto:
            raise ValueError("El comentario no puede estar vacio")
        if len(self.texto)>largoMaximo:
            raise ValueError(f"El comentario puede tener hasta {largoMaximo} caracteres")
