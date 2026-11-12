class Cupo:
    def __init__(self,texto):
        self.numero=None
        texto=(texto or "").strip()
        if texto!="":
            if not texto.isdigit():
                raise ValueError("El cupo tiene que ser un numero")
            self.numero=int(texto)
            if self.numero<1:
                raise ValueError("El cupo tiene que ser al menos 1")