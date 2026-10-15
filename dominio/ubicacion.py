from urllib.parse import quote_plus

largoMaximo=120


class Ubicacion:
    def __init__(self,texto):
        self.texto=(texto or "").strip()
        self.validar()

    def validar(self):
        if len(self.texto)>largoMaximo:
            raise ValueError(f"El lugar puede tener hasta {largoMaximo} caracteres")

    def enlaceMapa(self):
        if not self.texto:
            return None
        return "https://www.google.com/maps/search/?api=1&query="+quote_plus(self.texto)

    def enlaceEmbebido(self):
        if not self.texto:
            return None
        return "https://maps.google.com/maps?q="+quote_plus(self.texto)+"&z=15&output=embed"
