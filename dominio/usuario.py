import bcrypt


class Usuario:
    def __init__(self, email, password, nombre):
        self.validar_email(email)
        self.validar_password(password)
        self.validar_nombre(nombre)

        self.email = email.strip().lower()
        self.password = self.hashear_password(password)
        self.nombre = nombre

    @staticmethod
    def validar_email(email):
        if not email:
            raise ValueError("El email no puede estar vacío")
        if any(caracter.isspace() for caracter in email):
            raise ValueError("El email no puede contener espacios")
        if email.count("@") != 1:
            raise ValueError("El correo debe contener un @")
        usuario, _, dominio = email.partition("@")
        if not usuario or not dominio:
            raise ValueError("El email no es válido")
        if "." not in dominio:
            raise ValueError("El email debe tener un dominio válido como '.com' ")

    def validar_password(self, password):
        if not password or len(password) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        if len(password.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede tener más de 72 caracteres")
        if not self.contiene_mayuscula(password):
            raise ValueError("La contraseña debe tener al menos una mayúscula")
        if not self.contiene_simbolo(password):
            raise ValueError("La contraseña debe tener al menos un símbolo")

    def contiene_mayuscula(self, password):
        for caracter in password:
            if caracter.isupper():
                return True
        return False

    def contiene_simbolo(self, password):
        for caracter in password:
            if not caracter.isalnum():
                return True
        return False

    @staticmethod
    def validar_nombre(nombre):
        if not nombre or not nombre.strip():
            raise ValueError("El nombre no debe estar vacío")

    def hashear_password(self, password):
        password_en_bytes = password.encode("utf-8")
        hash_bytes = bcrypt.hashpw(password_en_bytes, bcrypt.gensalt())
        return hash_bytes.decode("utf-8")

    
    @staticmethod
    def verificar_password(password_plana, password_hasheada):
        return bcrypt.checkpw(
            password_plana.encode("utf-8"),
            password_hasheada.encode("utf-8"),
        )