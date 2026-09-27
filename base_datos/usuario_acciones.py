from sqlalchemy import select
from base_datos.configuracion import Session
from base_datos.usuario_tabla import UsuarioTabla
from dominio.usuario import Usuario

def guardar(usuario):
    if buscar_por_email(usuario.email) is not None:
        raise ValueError("Ya existe una cuenta registrada con ese email")
    
    sesion = Session()
    usuario_tabla = UsuarioTabla(
        email=usuario.email,
        password=usuario.password,
        nombre=usuario.nombre,
    )
    sesion.add(usuario_tabla)
    sesion.commit()
    sesion.close()

def obtenerTodos():
    with Session() as sesion:
        consulta=select(UsuarioTabla).where(UsuarioTabla.activo.is_(True)).order_by(UsuarioTabla.nombre)
        return sesion.scalars(consulta).all()

def buscarPorID(usuarioID):
    with Session() as sesion:
        return sesion.get(UsuarioTabla, usuarioID)

def buscar_por_email(email):
    sesion = Session()
    usuario_tabla = sesion.query(UsuarioTabla).filter_by(email=email).first()
    sesion.close()
    return usuario_tabla


def verificar_login(email, password):
    usuario_tabla = buscar_por_email(email)
    if usuario_tabla is None or not usuario_tabla.activo:
        return None
    if not Usuario.verificar_password(password, usuario_tabla.password):
        return None
    return usuario_tabla

def actualizar_perfil(usuarioID,nombre):
    nombre=(nombre or "").strip()
    Usuario.validar_nombre(nombre)
    if len(nombre)>255:
        raise ValueError("El nombre debe tener hasta 255 caracteres")
    with Session() as sesion:
        usuario=sesion.get(UsuarioTabla,usuarioID)
        if usuario is None or not usuario.activo:
            raise ValueError("La cuenta no está activa")
        usuario.nombre=nombre
        sesion.commit()

def actualizar_compartir_disponibilidad(usuarioID, valor):
    with Session() as sesion:
        usuario = sesion.get(UsuarioTabla, usuarioID)
        if usuario is None or not usuario.activo:
            raise ValueError("La cuenta no está activa")
        usuario.compartir_disponibilidad=valor
        sesion.commit()
     

def dar_de_baja(usuarioID,password):
    with Session() as sesion:
        usuario=sesion.get(UsuarioTabla,usuarioID)
        if usuario is None or not usuario.activo:
            raise ValueError("La cuenta no está activa")
        try:
            correcta=Usuario.verificar_password(password or "",usuario.password)
        except ValueError:
            correcta=False
        if not correcta:
            raise ValueError("La contraseña es incorrecta")
        usuario.activo=False
        sesion.commit()
