from functools import wraps
import os
import secrets
import time as modulo_tiempo
import unicodedata
from datetime import date, datetime, time, timedelta
import calendar as modulo_calendario

os.environ.setdefault("TZ","America/Argentina/Buenos_Aires")
if hasattr(modulo_tiempo,"tzset"):
    modulo_tiempo.tzset()

from flask import Flask, request, render_template, session, redirect, url_for, g, flash
from dominio.usuario import Usuario
from dominio.juntada.juntada import Juntada
from dominio.juntada.reprogramacion import Reprogramacion
from dominio.juntada.recurrencia import Recurrencia, un_anio_despues, texto_de_repeticion
from dominio.agenda.agenda import Agenda
from dominio.comentario import Comentario
from dominio.grupo import Grupo
from dominio.ubicacion import Ubicacion
from dominio.gasto import Gasto, leerMonto
from dominio.encuesta import Encuesta, MINIMO_OPCIONES, MAXIMO_OPCIONES 
import base_datos.encuesta_acciones as encuesta_acciones
from base_datos.usuario_acciones import guardar, actualizar_perfil, dar_de_baja, actualizar_compartir_disponibilidad
from base_datos.usuario_acciones import verificar_login, buscarPorID, obtenerTodos
from base_datos.secretos import SECRET_KEY
from base_datos.configuracion import USA_AIVEN
from base_datos.preparar_local import asegurar_base_local
from amistad_acciones import enviarSolicitud, aceptarSolicitud, rechazarSolicitud, eliminarAmigo
from base_datos.solicitud_acciones import obtenerRecibidas, obtener_amigos
from base_datos.agenda_acciones import obtener_por_usuario as obtener_agenda_de_usuario
from base_datos.agenda_acciones import guardar as guardar_agenda, borrar_evento
from base_datos.juntada_acciones import (
    guardar as guardar_juntada,
    obtener_organizadas,
    obtener_invitaciones_del_calendario,
    obtener_invitados_de_juntadas,
    responder_invitacion,
    cancelar_juntada as borrar_juntada_organizada,
    cancelar_serie,
    darse_de_baja as bajarse_de_juntada,
    reprogramar_juntada,
    obtener_por_id,
)
from base_datos.disponibilidad_amigo_acciones import obtener_disponibilidad
from base_datos.notificacion_acciones import obtener_no_leidas, marcar_leidas, juntadas_reprogramadas
from base_datos.comentario_acciones import guardar as guardarComentario, obtenerDeJuntadas as obtenerComentarios
from base_datos.gasto_acciones import guardar as guardarGasto, borrar as borrarGasto, obtenerDeJuntadas as obtenerGastos, personasDeJuntadas, saldosDeJuntadas, saldarDeuda as saldarDeudaEnBase
from base_datos.grupo_acciones import guardar as guardarGrupo, borrar as borrarGrupo, obtenerDeUsuario as obtenerGrupos
from base_datos.categoria_acciones import obtener_categorias, crear_categoria, borrar_categoria, puede_usar_categoria
from dominio.categoria import Categoria, COLORES
from dominio.modulo_utilidades.rango_horario import rango_del_evento, termina_al_dia_siguiente, ya_empezo
from dominio.disponibilidad.buscador_huecos import buscar_huecos, huecos_del_dia, proxima_media_hora
from dominio.gamificacion.checkin import Posicion, generar_codigo, leer_codigo, se_puede_hacer_checkin, se_puede_habilitar, checkin_cerrado, SEGUNDOS_POR_CODIGO
from dominio.gamificacion.logros import Logros, Estilo, resumen_del_mes, COLORES_AVATAR, FORMAS, MARCOS, TITULOS
from base_datos.gamificacion_acciones import registrar_checkin, presentes, juntadas_con_asistencia, historiales, estilos_de, guardar_estilo

NOMBRES_MES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
DIAS_SEMANA = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
DIAS_SEMANA_LARGO = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
DURACIONES_JUNTADA = [
    (30, "30 min"), (60, "1 h"), (90, "1 h 30 min"), (120, "2 h"), (180, "3 h"),
    (240, "4 h"), (360, "6 h"), (480, "8 h"), (720, "12 h"),
]

app= Flask(__name__)
app.config["SECRET_KEY"]=SECRET_KEY
asegurar_base_local()

def login_requerido(vista):
    @wraps(vista)
    def decorador(*args, **kwargs):
        if "usuarioID" not in session:
            return redirect(url_for("mostrar_login"))
        usuario=buscarPorID(session["usuarioID"])
        if usuario is None or not usuario.activo:
            session.clear()
            return redirect(url_for("mostrar_login"))
        g.usuario=usuario
        return vista(*args, **kwargs)
    return decorador

def volver_a(destino_por_defecto):
    destino=request.form.get("volver","")
    if destino.startswith("/") and not destino.startswith("//") and "\\" not in destino:
        return redirect(destino)
    return redirect(destino_por_defecto)

@app.template_filter("hace")
def hace(momento):
    minutos=int((datetime.now()-momento).total_seconds()//60)
    if minutos<1:
        return "Recién"
    if minutos<60:
        return f"Hace {minutos} min"
    if minutos<24*60:
        return f"Hace {minutos//60} h"
    if (date.today()-momento.date()).days==1:
        return f"Ayer, {momento:%H:%M}"
    return f"{momento:%d/%m, %H:%M}"

@app.template_filter("iniciales")
def iniciales(nombre):
    return "".join(parte[0] for parte in nombre.split()[:2]).upper() or "?"

@app.template_global()
def texto_horario(fecha,hora_inicio,hora_fin):
    texto=f"{hora_inicio:%H:%M} a {hora_fin:%H:%M}"
    return texto+" (+1)" if termina_al_dia_siguiente(fecha,hora_inicio,hora_fin) else texto

def nombre_del_dia(dia):
    return f"{DIAS_SEMANA_LARGO[dia.weekday()].capitalize()} {dia.day} de {NOMBRES_MES[dia.month]}"

def a_texto(momento):
    return momento.strftime("%Y-%m-%dT%H:%M")

def dias_de_la_semana(lunes):
    return [lunes+timedelta(days=i) for i in range(7)]

def dia_de_la_grilla(dia):
    return {"fecha":dia.isoformat(),"titulo":DIAS_SEMANA[dia.weekday()].capitalize(),"numero":dia.day,"nombre":nombre_del_dia(dia)}

def titulo_semana(lunes):
    domingo=lunes+timedelta(days=6)
    if lunes.month==domingo.month:
        return f"{lunes.day} – {domingo.day} de {NOMBRES_MES[lunes.month]} de {domingo.year}"
    return f"{lunes.day} de {NOMBRES_MES[lunes.month]} – {domingo.day} de {NOMBRES_MES[domingo.month]} de {domingo.year}"

def sin_acentos(texto):
    return "".join(letra for letra in unicodedata.normalize("NFD",texto.casefold()) if not unicodedata.combining(letra))

def invitaciones_del_usuario(inicio,fin):
    if "invitaciones" not in g:
        g.invitaciones=obtener_invitaciones_del_calendario(g.usuario.id,inicio,fin)
    return g.invitaciones

def logros_de(usuarios_ids):
    if "logros" not in g:
        g.logros={}
        g.historiales={}
    faltan=[usuario_id for usuario_id in set(usuarios_ids) if usuario_id not in g.logros]
    if faltan:
        g.historiales.update(historiales(faltan,datetime.now()))
        for usuario_id in faltan:
            g.logros[usuario_id]=Logros([item["cumplio"] for item in g.historiales.get(usuario_id,[])])
    return g.logros

def estilos_visibles(usuarios_ids):
    if "estilos" not in g:
        g.estilos={}
    faltan=[usuario_id for usuario_id in set(usuarios_ids) if usuario_id not in g.estilos]
    if faltan:
        logros=logros_de(faltan)
        guardados=estilos_de(faltan)
        for usuario_id in faltan:
            estilo=guardados.get(usuario_id)
            g.estilos[usuario_id]={
                "color":estilo.color if estilo else None,
                "forma":estilo.forma if estilo else None,
                "marco":estilo.marco if estilo else None,
                "titulo":estilo.titulo if estilo else None,
                "degrade":bool(estilo and estilo.degrade),
                "racha":logros[usuario_id].racha_actual if logros[usuario_id].tiene_fuego else 0,
            }
    return g.estilos

@app.template_global()
def estilos_de_usuarios(usuarios_ids):
    return estilos_visibles(usuarios_ids)

def estilo_del_usuario_actual():
    return estilos_visibles([g.usuario.id])[g.usuario.id]

def solicitudes_recibidas():
    if "solicitudes" not in g:
        g.solicitudes=[
            {"solicitud":solicitud,"emisor":emisor}
            for solicitud,emisor in obtenerRecibidas(g.usuario.id)
        ]
    return g.solicitudes

@app.context_processor
def datos_del_header():
    usuario=g.get("usuario")
    if usuario is None:
        return {}

    hoy=date.today()
    invitaciones=[
        {"juntada":juntada,"estado":invitacion.estado,"organizador":organizador}
        for invitacion,juntada,organizador,*_ in invitaciones_del_usuario(hoy,hoy)
        if invitacion.estado in ("Pendiente","Tal vez") and juntada.fecha>=hoy
    ]
    invitaciones.sort(key=lambda item: (item["juntada"].fecha, item["juntada"].hora_inicio))
    invitaciones=agrupar_por_serie(invitaciones)
    reprogramadas=juntadas_reprogramadas(usuario.id,[item["juntada"].id for item in invitaciones])
    for item in invitaciones:
        item["reprogramada"]=item["juntada"].id in reprogramadas

    solicitudes=solicitudes_recibidas()
    avisos=[
        aviso for aviso in obtener_no_leidas(usuario.id)
        if not (aviso.tipo=="reprogramacion" and aviso.juntada_id in reprogramadas)
    ]
    pendientes=len(solicitudes)+len(avisos)+sum(1 for item in invitaciones if item["estado"]=="Pendiente")

    return {
        "usuario_actual":usuario,
        "estilo_actual":estilo_del_usuario_actual,
        "notificaciones_juntadas":invitaciones,
        "notificaciones_amistad":solicitudes,
        "notificaciones_avisos":avisos,
        "notificaciones_pendientes":pendientes,
    }

def agrupar_por_serie(invitaciones):
    agrupadas=[]
    por_serie={}
    for item in invitaciones:
        serie_id=item["juntada"].serie_id
        clave=(serie_id,item["estado"])
        if serie_id is not None and clave in por_serie:
            por_serie[clave]["fechas"]+=1
            continue
        item["fechas"]=1
        item["repeticion"]=texto_de_repeticion(item["juntada"].repeticion,item["juntada"].fecha)
        if serie_id is not None:
            por_serie[clave]=item
        agrupadas.append(item)
    return agrupadas

@app.route("/registro", methods=["POST"])
def registro():
    nombre=request.form.get("nombre")
    email=request.form.get("email")
    password=request.form.get("password")

    try:
        usuario=Usuario(email,password,nombre)
        guardar(usuario)
    except ValueError as error:
        return render_template("registro.html", error=str(error), nombre=nombre, email=email), 400

    return redirect(url_for("mostrar_login", registrado="1"))


@app.route("/registro", methods = ["GET"])
def mostrar_registro():
    return render_template("registro.html", error=None, nombre="", email="")

@app.route("/login",methods=["GET"])
def mostrar_login():
    return render_template("login.html")

@app.route("/login",methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    usuario_encontrado=verificar_login(email,password)
    if usuario_encontrado is None:
        return render_template("login.html", error="Email o contraseña incorrectos"), 401

    session.clear()
    session["usuarioID"]=usuario_encontrado.id
    return redirect(url_for("mostrar_inicio"))

@app.route("/logout",methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("mostrar_login"))

def datos_de_logros():
    usuario_id=g.usuario.id
    logros=logros_de([usuario_id])[usuario_id]
    hoy=date.today()
    cumplidas=[item for item in g.historiales.get(usuario_id,[]) if item["cumplio"]]
    return {
        "logros":logros,"desbloqueados":logros.desbloqueados(),"progreso":logros.progreso(),"proximo":logros.proximo(),
        "estilo":estilo_del_usuario_actual(),"colores_avatar":COLORES_AVATAR,"formas":FORMAS,"marcos":MARCOS,"titulos":TITULOS,
        "resumen":resumen_del_mes(cumplidas,hoy.year,hoy.month),"nombre_mes":NOMBRES_MES[hoy.month],
    }

def pagina_perfil(nombre, email, error, guardado):
    return render_template(
        "perfil.html", nombre=nombre, email=email, error=error, guardado=guardado,
        categorias=obtener_categorias(g.usuario.id), colores=COLORES,
        compartir_disponibilidad=g.usuario.compartir_disponibilidad,
        **datos_de_logros(),
    )

@app.route("/perfil",methods=["GET","POST"])
@login_requerido
def mostrar_perfil():
    usuario=g.usuario

    if "perfil_token" not in session:
        session["perfil_token"]=secrets.token_hex(32)
    nombre=usuario.nombre
    email=usuario.email
    error=None
    estado=200

    if request.method=="POST":
        if not secrets.compare_digest(request.form.get("token",""),session["perfil_token"]):
            return "El formulario venció. Recargá la página e intentá nuevamente.",400
        nombre=request.form.get("nombre","")
        compartir_disponibilidad = "compartir_disponibilidad" in request.form
        try:
            actualizar_perfil(session["usuarioID"],nombre)
            actualizar_compartir_disponibilidad(session["usuarioID"],compartir_disponibilidad)
        except ValueError as problema:
            error=str(problema)
            estado=400
        else:
            session["perfil_guardado"]=True
            return redirect(url_for("mostrar_perfil"))

    guardado=session.pop("perfil_guardado",False)
    return pagina_perfil(nombre, email, error, guardado), estado

@app.route("/perfil/estilo",methods=["POST"])
@login_requerido
def guardar_estilo_propio():
    token=session.get("perfil_token")
    if not token or not secrets.compare_digest(request.form.get("token",""),token):
        return "El formulario venció. Recargá la página e intentá nuevamente.",400
    usuario=g.usuario
    logros=logros_de([usuario.id])[usuario.id]
    try:
        estilo=Estilo(
            request.form.get("color"),request.form.get("forma"),request.form.get("marco"),request.form.get("titulo"),
            "degrade" in request.form,logros.desbloqueados(),
        )
    except ValueError as error:
        return pagina_perfil(usuario.nombre,usuario.email,str(error),False),400
    guardar_estilo(usuario.id,estilo)
    session["perfil_guardado"]=True
    return redirect(url_for("mostrar_perfil")+"#mi-estilo")

@app.route("/perfil/baja",methods=["POST"])
@login_requerido
def baja_cuenta():
    token=session.get("perfil_token")
    if not token or not secrets.compare_digest(request.form.get("token",""),token):
        return "El formulario venció. Recargá la página e intentá nuevamente.",400
    usuario=g.usuario
    try:
        if request.form.get("confirmar")!="si":
            raise ValueError("Confirmá que querés dar de baja tu cuenta")
        dar_de_baja(session["usuarioID"],request.form.get("password",""))
    except ValueError as error:
        return pagina_perfil(usuario.nombre,usuario.email,str(error),False),400
    session.clear()
    return redirect(url_for("mostrar_login",baja="1"))

def datos_de_lugar(texto):
    ubicacion=Ubicacion(texto)
    if not ubicacion.texto:
        return None
    return {"texto":ubicacion.texto,"mapa":ubicacion.enlaceMapa(),"embebido":ubicacion.enlaceEmbebido()}

def eventos_del_usuario(usuario_id,desde,hasta):
    eventos=[]

    for agenda,categoria,color in obtener_agenda_de_usuario(usuario_id,desde,hasta):
        muestra_titulo=agenda.visibilidad=="detalle" and g.usuario.compartir_disponibilidad
        if agenda.visibilidad=="oculto":
            que_ven="Tus amigos no ven este evento."
        elif muestra_titulo:
            que_ven="Tus amigos ven el título."
        else:
            que_ven="Tus amigos solo ven que estás ocupado/a."
        eventos.append({
            "fecha":agenda.fecha,"titulo":agenda.titulo,"hora_inicio":agenda.hora_inicio,"hora_fin":agenda.hora_fin,
            "tipo":"personal","juntada_id":None,"agenda_id":agenda.id,"categoria":categoria,"color":color,
            "detalle":que_ven,
            "ubicacion":agenda.ubicacion,
            
        
        })

    organizadas={}
    for juntada,nombre_invitado,estado,categoria,color,invitado_id in obtener_organizadas(usuario_id,desde,hasta):
        invitados=organizadas.setdefault(juntada.id,(juntada,[],categoria,color))[1]
        if nombre_invitado is not None:
            invitados.append((nombre_invitado,estado,invitado_id))

    for juntada,invitados,categoria,color in organizadas.values():
        confirmados=sum(1 for _,estado,_ in invitados if estado=="Si")
        if(juntada.cupo==confirmados):
            eventos.append({
            "fecha":juntada.fecha,"titulo":juntada.titulo,"hora_inicio":juntada.hora_inicio,"hora_fin":juntada.hora_fin,
            "tipo":"organizo","detalle":f"Organizás · {confirmados} de {len(invitados)} confirmaron"+texto_repeticion(juntada),
            "juntada_id":juntada.id,"serie_id":juntada.serie_id,"categoria":categoria,"color":color,
            "personas":[persona(g.usuario.nombre,"organiza",usuario_id,es_vos=True)]+[persona(nombre,estado,invitado_id) for nombre,estado,invitado_id in invitados],
            "ubicacion":juntada.ubicacion,
            "cupo":"COMPLETO"
        })
        else:
            eventos.append({
            "fecha":juntada.fecha,"titulo":juntada.titulo,"hora_inicio":juntada.hora_inicio,"hora_fin":juntada.hora_fin,
            "tipo":"organizo","detalle":f"Organizás · {confirmados} de {len(invitados)} confirmaron"+texto_repeticion(juntada),
            "juntada_id":juntada.id,"serie_id":juntada.serie_id,"categoria":categoria,"color":color,
            "personas":[persona(g.usuario.nombre,"organiza",usuario_id,es_vos=True)]+[persona(nombre,estado,invitado_id) for nombre,estado,invitado_id in invitados],
            "ubicacion":juntada.ubicacion,
            "cupo":juntada.cupo
        })

        
       
        

    invitaciones=[
        fila for fila in invitaciones_del_usuario(desde,hasta) if desde<=fila[1].fecha<=hasta
    ]
    invitados_por_juntada={}
    for juntada_id,invitado_id,nombre,estado in obtener_invitados_de_juntadas([fila[1].id for fila in invitaciones]):
        invitados_por_juntada.setdefault(juntada_id,[]).append(persona(nombre,estado,invitado_id,es_vos=invitado_id==usuario_id))

    for invitacion,juntada,organizador,categoria,color in invitaciones:
        respuesta={"Si":"Confirmaste","Tal vez":"Dijiste tal vez"}.get(invitacion.estado,"Todavía no respondiste")
        eventos.append({
            "fecha":juntada.fecha,"titulo":juntada.titulo,"hora_inicio":juntada.hora_inicio,"hora_fin":juntada.hora_fin,
            "tipo":{"Si":"confirmada","Tal vez":"tal_vez"}.get(invitacion.estado,"pendiente"),
            "detalle":f"Te invitó {organizador} · {respuesta}"+texto_repeticion(juntada),
            "juntada_id":juntada.id,"categoria":categoria,"color":color,
            "personas":[persona(organizador,"organiza",juntada.organizador_id)]+invitados_por_juntada.get(juntada.id,[]),
            "ubicacion":juntada.ubicacion,
            "cupo":juntada.cupo
        })
    agregar_estilos(eventos)
    return eventos

def agregar_estilos(eventos):
    personas=[item for evento in eventos for item in evento.get("personas",[])]
    estilos=estilos_visibles([item["id"] for item in personas])
    for item in personas:
        item["estilo"]=estilos[item["id"]]

HORA_INICIO_SEMANA=8
MAXIMO_PROXIMAS=5

def asignar_carriles(bloques):
    grupo=[]
    fin_del_grupo=None
    for bloque in sorted(bloques,key=lambda bloque:(bloque["inicio"],bloque["fin"])):
        if grupo and bloque["inicio"]>=fin_del_grupo:
            repartir_carriles(grupo)
            grupo=[]
        grupo.append(bloque)
        fin_del_grupo=bloque["fin"] if fin_del_grupo is None or len(grupo)==1 else max(fin_del_grupo,bloque["fin"])
    if grupo:
        repartir_carriles(grupo)

def repartir_carriles(grupo):
    finales=[]
    for bloque in grupo:
        carril=next((indice for indice,fin in enumerate(finales) if fin<=bloque["inicio"]),len(finales))
        if carril==len(finales):
            finales.append(bloque["fin"])
        else:
            finales[carril]=bloque["fin"]
        bloque["carril"]=carril
    for bloque in grupo:
        bloque["izquierda"]=round(bloque["carril"]/len(finales)*100,2)
        bloque["ancho"]=round(100/len(finales),2)

def mi_semana(lunes,eventos,ahora):
    dias=dias_de_la_semana(lunes)
    por_dia={dia:[] for dia in dias}
    for evento in eventos:
        inicio,fin=rango_del_evento(evento["fecha"],evento["hora_inicio"],evento["hora_fin"])
        for dia in dias:
            inicio_dia=datetime.combine(dia,time(0))
            desde,hasta=max(inicio,inicio_dia),min(fin,inicio_dia+timedelta(days=1))
            if desde<hasta:
                por_dia[dia].append({"inicio":desde,"fin":hasta,"evento":evento,"sigue":inicio<inicio_dia})

    primera_hora=min([HORA_INICIO_SEMANA]+[bloque["inicio"].hour for bloques in por_dia.values() for bloque in bloques if not bloque["sigue"]])
    minutos_visibles=(24-primera_hora)*60
    semana=[]
    for dia in dias:
        inicio_visible=datetime.combine(dia,time(primera_hora))
        bloques=[]
        for bloque in por_dia[dia]:
            if bloque["fin"]>inicio_visible:
                bloques.append({**bloque,"inicio":max(bloque["inicio"],inicio_visible)})
        asignar_carriles(bloques)
        semana.append({
            "fecha":dia,"titulo":DIAS_SEMANA[dia.weekday()].capitalize(),"numero":dia.day,"es_hoy":dia==ahora.date(),
            "nombre":nombre_del_dia(dia),
            "bloques":[{
                "arriba":round((bloque["inicio"]-inicio_visible).total_seconds()/60/minutos_visibles*100,2),
                "alto":round((bloque["fin"]-bloque["inicio"]).total_seconds()/60/minutos_visibles*100,2),
                "izquierda":bloque["izquierda"],"ancho":bloque["ancho"],
                "tipo":bloque["evento"]["tipo"],"color":bloque["evento"].get("color"),
                "titulo":bloque["evento"]["titulo"],"hora":f"{bloque['inicio']:%H:%M}",
                "juntada_id":bloque["evento"]["juntada_id"],
                "detalle":f"{bloque['evento']['titulo']} · {texto_horario(bloque['evento']['fecha'],bloque['evento']['hora_inicio'],bloque['evento']['hora_fin'])}",
            } for bloque in bloques],
        })
    minutos_ahora=(ahora-datetime.combine(ahora.date(),time(primera_hora))).total_seconds()/60
    return {
        "dias":semana,
        "primera_hora":primera_hora,
        "horas":[{"texto":f"{hora:02d}","arriba":round((hora-primera_hora)*60/minutos_visibles*100,2)} for hora in range(primera_hora,24,2)],
        "ahora":round(minutos_ahora/minutos_visibles*100,2) if 0<=minutos_ahora<=minutos_visibles else None,
    }

def proximas_juntadas(eventos,ahora):
    proximas=[]
    for evento in eventos:
        if evento["tipo"] not in ("organizo","confirmada","tal_vez"):
            continue
        inicio,fin=rango_del_evento(evento["fecha"],evento["hora_inicio"],evento["hora_fin"])
        if fin<=ahora:
            continue
        proximas.append((inicio,evento))
    proximas.sort(key=lambda par:par[0])
    return [{
        **evento,
        "dia":"Hoy" if evento["fecha"]==ahora.date() else DIAS_SEMANA[evento["fecha"].weekday()].capitalize(),
        "numero":evento["fecha"].day,
        "horario":texto_horario(evento["fecha"],evento["hora_inicio"],evento["hora_fin"]),
        "van":[persona for persona in evento["personas"] if persona["estado"] in ("organiza","Si")],
        "lugar":Ubicacion(evento.get("ubicacion")).texto,
    } for _,evento in proximas[:MAXIMO_PROXIMAS]]

@app.route("/",methods=["GET"])
@login_requerido
def mostrar_inicio():
    ahora=datetime.now()
    hoy=ahora.date()
    lunes=hoy-timedelta(days=hoy.weekday())
    hasta=max(lunes+timedelta(days=6),hoy+timedelta(days=60))
    eventos=eventos_del_usuario(session["usuarioID"],lunes-timedelta(days=1),hasta)
    return render_template(
        "inicio.html",
        hoy=nombre_del_dia(hoy),
        checkins=checkins_abiertos(eventos,ahora),
        proximas=proximas_juntadas(eventos,ahora),
        semana=mi_semana(lunes,eventos,ahora),
        titulo_semana=titulo_semana(lunes),
        encuestas=[resumen_de_encuesta(encuesta) for encuesta in encuesta_acciones.obtener_de_usuario(session["usuarioID"])],
    )

def checkins_abiertos(eventos,ahora):
    abiertos=[
        evento for evento in eventos
        if evento["juntada_id"] and se_puede_hacer_checkin(evento["fecha"],evento["hora_inicio"],evento["hora_fin"],ahora)
    ]
    asistidas=juntadas_con_asistencia(session["usuarioID"],[evento["juntada_id"] for evento in abiertos])
    return [{
        "titulo":evento["titulo"],
        "empezo":ya_empezo(evento["fecha"],evento["hora_inicio"],ahora),
        "hora":f"{evento['hora_inicio']:%H:%M}",
        "organiza":evento["tipo"]=="organizo",
        "url":url_for("mostrar_checkin",juntada_id=evento["juntada_id"]),
    } for evento in abiertos if evento["juntada_id"] not in asistidas]

def fecha_corta(fecha):
    return f"{DIAS_SEMANA[fecha.weekday()].capitalize()} {fecha.day}/{fecha.month}"

def resumen_de_encuesta(encuesta):
    encuesta["opciones_lideres"]=[
        f"{fecha_corta(opcion['fecha'])} · {texto_horario(opcion['fecha'],opcion['hora_inicio'],opcion['hora_fin'])}"
        for opcion in encuesta["ganadoras"]
    ]
    juntada=encuesta["juntada"]
    encuesta["cuando_se_juntan"]=f"{fecha_corta(juntada.fecha)} · {texto_horario(juntada.fecha,juntada.hora_inicio,juntada.hora_fin)}" if juntada else None
    encuesta["repite"]=texto_de_repeticion(juntada.repeticion,juntada.fecha) if juntada and juntada.repeticion else None
    encuesta["progreso"]=round(encuesta["votaron"]/encuesta["participantes"]*100) if encuesta["participantes"] else 0
    return encuesta

@app.route("/calendario",methods=["GET"])
@login_requerido
def mostrar_calendario():
    usuario_id=session["usuarioID"]

    fecha_parametro=request.args.get("fecha")
    try:
        fecha_seleccionada=date.fromisoformat(fecha_parametro) if fecha_parametro else date.today()
    except ValueError:
        fecha_seleccionada=date.today()

    semanas=modulo_calendario.Calendar(firstweekday=0).monthdatescalendar(
        fecha_seleccionada.year, fecha_seleccionada.month
    )
    lunes=fecha_seleccionada-timedelta(days=fecha_seleccionada.weekday())
    desde=semanas[0][0]-timedelta(days=1)
    hasta=semanas[-1][-1]
    eventos=eventos_del_usuario(usuario_id,desde,hasta)

    ahora=datetime.now()
    inicio_semana=datetime.combine(lunes,time(0))
    fin_semana=inicio_semana+timedelta(days=7)
    dias_con_eventos=set()
    eventos_de_la_semana=[]
    juntadasIDs=[evento["juntada_id"] for evento in eventos if evento["juntada_id"]]
    comentariosPorJuntada={}
    comentarios=obtenerComentarios(juntadasIDs)
    estilosComentarios=estilos_visibles([comentario.usuarioID for comentario,_ in comentarios])
    for comentario,nombre in comentarios:
        comentariosPorJuntada.setdefault(comentario.juntadaID,[]).append({
            "nombre":"Vos" if comentario.usuarioID==usuario_id else nombre,
            "iniciales":iniciales(nombre),
            "estilo":estilosComentarios[comentario.usuarioID],
            "texto":comentario.texto,
            "cuando":f"{comentario.fechaHora:%d/%m %H:%M}",
        })
    gastosPorJuntada={}
    for gasto in obtenerGastos(juntadasIDs):
        gastosPorJuntada.setdefault(gasto["juntadaID"],[]).append({
            "descripcion":gasto["descripcion"],
            "monto":textoMonto(gasto["monto"]),
            "pagador":"Vos" if gasto["pagadorID"]==usuario_id else gasto["pagador"],
            "partes":[{"nombre":"Vos" if parte["usuarioID"]==usuario_id else parte["nombre"],"monto":textoMonto(parte["monto"])} for parte in gasto["partes"]],
            "borrar":url_for("borrarGastoPropio",gastoID=gasto["id"]) if gasto["creadorID"]==usuario_id else None,
        })
    personasPorJuntada=personasDeJuntadas(juntadasIDs)
    saldosPorJuntada=saldosDeJuntadas(juntadasIDs)
    def nombreVisible(personaID,nombre):
        return "Vos" if personaID==usuario_id else nombre
    
    asistidas=juntadas_con_asistencia(usuario_id,juntadasIDs)
    for evento in eventos:
        inicio,fin=rango_del_evento(evento["fecha"],evento["hora_inicio"],evento["hora_fin"])
        dias_con_eventos.add(evento["fecha"])
        if termina_al_dia_siguiente(evento["fecha"],evento["hora_inicio"],evento["hora_fin"]):
            dias_con_eventos.add(fin.date())
        if inicio<fin_semana and fin>inicio_semana:
            eventos_de_la_semana.append({
                "inicio":a_texto(inicio),"fin":a_texto(fin),"titulo":evento["titulo"],"tipo":evento["tipo"],
                "detalle":evento["detalle"],"personas":evento.get("personas",[]),
                "categoria":evento.get("categoria"),"color":evento.get("color"),
                "cuando":f"{nombre_del_dia(evento['fecha'])} · {texto_horario(evento['fecha'],evento['hora_inicio'],evento['hora_fin'])}",
                "juntadaID":evento["juntada_id"],
                "comentarios":comentariosPorJuntada.get(evento["juntada_id"],[]),
                "lugar":datos_de_lugar(evento["ubicacion"]),
                
                "gastos":gastosPorJuntada.get(evento["juntada_id"],[]),
                                "saldos":[
                    {
                        "deudor":nombreVisible(saldo["deudorID"],saldo["deudor"]),
                        "acreedor":nombreVisible(saldo["acreedorID"],saldo["acreedor"]),
                        "monto":textoMonto(saldo["monto"]),
                        "saldar":{"deudorID":saldo["deudorID"],"acreedorID":saldo["acreedorID"],"monto":str(saldo["monto"])} if usuario_id in (saldo["deudorID"],saldo["acreedorID"]) else None,
                    }
                    for saldo in saldosPorJuntada.get(evento["juntada_id"],{}).get("pendientes",[])
                ],
                "saldadas":[
                    (
                        f"Le pagaste {textoMonto(pago['monto'])} a {pago['acreedor']}" if pago["deudorID"]==usuario_id
                        else f"{pago['deudor']} me pagó {textoMonto(pago['monto'])}" if pago["acreedorID"]==usuario_id
                        else f"{pago['deudor']} le pagó {textoMonto(pago['monto'])} a {pago['acreedor']}"
                    )
                    for pago in saldosPorJuntada.get(evento["juntada_id"],{}).get("saldadas",[])
                ],
                "saldar":url_for("saldarDeuda",juntadaID=evento["juntada_id"]) if evento["juntada_id"] else None,
                "personasGasto":[{"id":p["id"],"nombre":"Vos" if p["id"]==usuario_id else p["nombre"]} for p in personasPorJuntada.get(evento["juntada_id"],[])],
                "asistio":evento["juntada_id"] in asistidas,
                **acciones_del_evento(evento,ahora),
            })

    datos={
        "fecha":fecha_seleccionada.isoformat(),
        "dias":[dia_de_la_grilla(dia) for dia in dias_de_la_semana(lunes)],
        "eventos":eventos_de_la_semana,
        "usuarioID":usuario_id,
        "errorGasto":request.args.get("errorGasto"),
        "urls":{"nuevo_evento":url_for("mostrar_nueva_agenda"),"nueva_juntada":url_for("mostrar_nueva_juntada")},
    }

    inicio_mes=fecha_seleccionada.replace(day=1)
    return render_template(
        "calendario.html",
        datos=datos,
        fecha_seleccionada=fecha_seleccionada,
        titulo=titulo_semana(lunes),
        semana_anterior=lunes-timedelta(days=7),
        semana_siguiente=lunes+timedelta(days=7),
        dias_semana_elegida=dias_de_la_semana(lunes),
        dias_con_eventos=dias_con_eventos,
        semanas=semanas,
        hoy=date.today(),
        mes_anterior=(inicio_mes-timedelta(days=1)).replace(day=1),
        mes_siguiente=(inicio_mes+timedelta(days=31)).replace(day=1),
        nombre_mes=NOMBRES_MES[fecha_seleccionada.month],
        dias_semana=DIAS_SEMANA,
    )

def texto_repeticion(juntada):
    texto=texto_de_repeticion(juntada.repeticion,juntada.fecha)
    return f" · {texto}" if texto else ""

def persona(nombre,estado,usuario_id,es_vos=False):
    return {"id":usuario_id,"nombre":"Vos" if es_vos else nombre,"iniciales":iniciales(nombre),"estado":estado}

def acciones_del_evento(evento,ahora):
    tipo=evento["tipo"]
    todavia_no_empezo=not ya_empezo(evento["fecha"],evento["hora_inicio"],ahora)
    juntada_id=evento["juntada_id"]
    return {
        "responder":url_for("responder_juntada",juntada_id=juntada_id) if tipo in ("pendiente","tal_vez") else None,
        "cancelar":url_for("cancelar_juntada",juntada_id=juntada_id) if tipo=="organizo" and todavia_no_empezo else None,
        "cancelar_serie":url_for("cancelar_serie_de_juntadas",juntada_id=juntada_id) if tipo=="organizo" and todavia_no_empezo and evento.get("serie_id") else None,
        "reprogramar":url_for("mostrar_reprogramar_juntada",juntada_id=juntada_id) if tipo=="organizo" and todavia_no_empezo else None,
        "abandonar":url_for("abandonar_juntada",juntada_id=juntada_id) if tipo=="confirmada" and todavia_no_empezo else None,
        "comentar":url_for("comentarJuntada",juntadaID=juntada_id) if juntada_id else None,
        "cargarGasto":url_for("cargarGasto",juntadaID=juntada_id) if juntada_id else None,
        "checkin":url_for("mostrar_checkin",juntada_id=juntada_id) if juntada_id and se_puede_habilitar(evento["fecha"],evento["hora_inicio"],evento["hora_fin"],ahora) else None,
        "checkinAnticipado":bool(juntada_id) and not se_puede_hacer_checkin(evento["fecha"],evento["hora_inicio"],evento["hora_fin"],ahora),
        "borrar":url_for("borrar_evento_propio",evento_id=evento["agenda_id"]) if tipo=="personal" else None,
    }

def volver_al_calendario():
    fecha_parametro=request.form.get("fecha")
    return volver_a(url_for("mostrar_calendario", fecha=fecha_parametro) if fecha_parametro else url_for("mostrar_calendario"))

def horario_sugerido(minutos):
    try:
        inicio=datetime.strptime(request.args.get("hora",""),"%H:%M")
    except ValueError:
        return "",""
    return f"{inicio:%H:%M}",f"{inicio+timedelta(minutes=minutos):%H:%M}"

@app.route("/agenda/nueva",methods=["GET"])
@login_requerido
def mostrar_nueva_agenda():
    hora_desde,hora_hasta=horario_sugerido(60)
    return formulario_evento(fecha_pedida(),hora_desde=hora_desde,hora_hasta=hora_hasta)

def formulario_evento(fecha_sugerida,error=None,hora_desde="",hora_hasta=""):
    return formulario_con_horario(
        "agenda_nueva.html",fecha_sugerida,60,error,hora_desde,hora_hasta,
        categorias=obtener_categorias(g.usuario.id),colores=COLORES,
    )

@app.route("/agenda/nueva", methods=["POST"])
@login_requerido
def crear_agenda():
    usuario_id = session["usuarioID"]
    fecha_parametro = request.form.get("fecha", "")
    categoria_id = request.form.get("categoria", type=int)
    visibilidad = request.form.get("visibilidad", "ocupado")

    try:
        if categoria_id is not None and not puede_usar_categoria(categoria_id, usuario_id):
            raise ValueError("Elegí una categoría válida")
        fecha_formateada = datetime.strptime(fecha_parametro, "%Y-%m-%d").strftime("%d/%m/%Y")
        agenda = Agenda(
            usuario_id=usuario_id,
            fecha=fecha_formateada,
            titulo_reunion=request.form.get("titulo"),
            hora_inicio=request.form.get("hora_inicio"),
            hora_fin=request.form.get("hora_fin"),
            categoria_id=categoria_id,
            visibilidad=visibilidad,
            comparte_detalles=g.usuario.compartir_disponibilidad,
            ubicacion=request.form.get("ubicacion",""),
        )
    except ValueError as error:
        return formulario_evento(fecha_parametro, error=str(error)), 400

    guardar_agenda(agenda)
    return redirect(url_for("mostrar_calendario", fecha=fecha_parametro))

def fecha_pedida():
    return max(request.args.get("fecha",""),date.today().isoformat())

def formulario_con_horario(plantilla,fecha_sugerida,duracion_inicial,error=None,hora_desde="",hora_hasta="",**datos):
    return render_template(
        plantilla, fecha_sugerida=fecha_sugerida, error=error, duraciones=DURACIONES_JUNTADA,
        duracion_inicial=duracion_inicial, hora_desde=hora_desde, hora_hasta=hora_hasta,
        hoy=date.today().isoformat(), comparte_detalles=g.usuario.compartir_disponibilidad, **datos,
    )

def formulario_juntada(amigos,fecha_sugerida,seleccionados,error=None,hora_desde="",hora_hasta=""):
    return formulario_con_horario(
        "juntada_nueva.html",fecha_sugerida,120,error,hora_desde,hora_hasta,amigos=amigos,seleccionados=seleccionados,
        categorias=obtener_categorias(g.usuario.id),colores=COLORES,
        grupos=[(grupo,miembros) for grupo,miembros in obtenerGrupos(g.usuario.id) if miembros],
    )

def recurrencia_del_formulario(fecha):
    if request.form.get("repetir")!="semanal":
        return None
    return Recurrencia("semanal",un_anio_despues(fecha).strftime("%d/%m/%Y"))

@app.route("/juntada/nueva",methods=["GET"])
@login_requerido
def mostrar_nueva_juntada():
    amigos=obtener_amigos(session["usuarioID"])
    invitado_id=request.args.get("invitado",type=int)
    grupoID=request.args.get("grupo",type=int)
    miembrosIDs=[]
    for grupo,miembros in obtenerGrupos(session["usuarioID"]):
        if grupo.id==grupoID:
            miembrosIDs=[miembro.id for miembro in miembros]
    seleccionados=[amigo.id for amigo in amigos if amigo.id==invitado_id or amigo.id in miembrosIDs]
    hora_desde,hora_hasta=horario_sugerido(120)
    return formulario_juntada(amigos,fecha_pedida(),seleccionados,hora_desde=hora_desde,hora_hasta=hora_hasta)

@app.route("/juntada/nueva",methods=["POST"])
@login_requerido
def crear_juntada():
    usuario_id=session["usuarioID"]
    fecha_parametro=request.form.get("fecha","")
    invitados_ids=[int(id) for id in request.form.getlist("invitados")]
    amigos=obtener_amigos(usuario_id)
    amigos_ids=[amigo.id for amigo in amigos]
    visibilidad = request.form.get("visibilidad", "ocupado")
    

    if not set(invitados_ids).issubset(set(amigos_ids)):
        seleccionados=[id for id in invitados_ids if id in amigos_ids]
        return formulario_juntada(amigos,fecha_parametro,seleccionados,"Solo podés invitar a tus amigos."), 400

    categoria_id=request.form.get("categoria",type=int)
    try:
        if categoria_id is not None and not puede_usar_categoria(categoria_id,usuario_id):
            raise ValueError("Elegí una categoría válida")
        fecha_formateada=datetime.strptime(fecha_parametro, "%Y-%m-%d").strftime("%d/%m/%Y")
        juntada=Juntada(
            organizador=usuario_id,
            fecha=fecha_formateada,
            titulo_juntada=request.form.get("titulo"),
            hora_inicio=request.form.get("hora_inicio"),
            hora_fin=request.form.get("hora_fin"),
            amigos_invitados=invitados_ids,
            categoria_id=categoria_id,
            visibilidad=visibilidad,
            comparte_detalles=g.usuario.compartir_disponibilidad,
            recurrencia=recurrencia_del_formulario(datetime.strptime(fecha_parametro, "%Y-%m-%d").date()),
            ubicacion=request.form.get("ubicacion",""),cupo=request.form.get("cupo","")
        )
    except ValueError as error:
        return formulario_juntada(amigos,fecha_parametro,invitados_ids,str(error)), 400

    guardar_juntada(juntada)
    return redirect(url_for("mostrar_calendario", fecha=fecha_parametro))

def formulario_encuesta(amigos,seleccionados,error=None,opciones=None):
    return render_template(
        "encuesta_nueva.html",amigos=amigos,seleccionados=seleccionados,error=error,
        opciones=opciones or [("","",""),("","","")],
        hoy=date.today().isoformat(),minimo=MINIMO_OPCIONES,maximo=MAXIMO_OPCIONES,
    )

@app.route("/encuesta/nueva",methods=["GET"])
@login_requerido
def mostrar_nueva_encuesta():
    return formulario_encuesta(obtener_amigos(session["usuarioID"]),[])

@app.route("/encuesta/nueva",methods=["POST"])
@login_requerido
def crear_encuesta():
    usuario_id=session["usuarioID"]
    invitados_ids=[int(id) for id in request.form.getlist("invitados")]
    amigos=obtener_amigos(usuario_id)
    amigos_ids=[amigo.id for amigo in amigos]
    opciones_formulario=list(zip(
        request.form.getlist("fecha"),request.form.getlist("hora_inicio"),request.form.getlist("hora_fin"),
    ))

    if not set(invitados_ids).issubset(set(amigos_ids)):
        seleccionados=[id for id in invitados_ids if id in amigos_ids]
        return formulario_encuesta(amigos,seleccionados,"Solo podés invitar a tus amigos.",opciones_formulario),400

    try:
        if any(not fecha for fecha,_,_ in opciones_formulario):
            raise ValueError("Elegí la fecha de cada opción")
        encuesta=Encuesta(
            usuario_id,
            request.form.get("titulo",""),
            [(datetime.strptime(fecha,"%Y-%m-%d").strftime("%d/%m/%Y"),inicio,fin) for fecha,inicio,fin in opciones_formulario],
            invitados_ids,
            ubicacion=request.form.get("ubicacion",""),
            repeticion="semanal" if request.form.get("repetir")=="semanal" else None,
        )
        
    except ValueError as error:
        return formulario_encuesta(amigos,invitados_ids,str(error),opciones_formulario),400

    encuesta_id=encuesta_acciones.crear(encuesta,datetime.now())
    return redirect(url_for("mostrar_encuesta",encuesta_id=encuesta_id))

@app.route("/encuesta/<int:encuesta_id>",methods=["GET"])
@login_requerido
def mostrar_encuesta(encuesta_id,error=None):
    encuesta=encuesta_acciones.obtener_detalle(encuesta_id,session["usuarioID"])
    if encuesta is None:
        return "No encontramos esa encuesta.",404
    for opcion in encuesta["opciones"]:
        opcion["dia"]=nombre_del_dia(opcion["fecha"])
        opcion["repite"]=texto_de_repeticion(encuesta["repeticion"],opcion["fecha"]) if encuesta["repeticion"] else None
    encuesta["lugar"]=datos_de_lugar(encuesta["ubicacion"])
    juntada=obtener_por_id(encuesta["juntada_id"]) if encuesta["juntada_id"] else None
    return render_template("encuesta.html",encuesta=encuesta,juntada=juntada,error=error)

@app.route("/encuesta/<int:encuesta_id>/votar",methods=["POST"])
@login_requerido
def votar_encuesta(encuesta_id):
    try:
        opciones_ids=[int(id) for id in request.form.getlist("opciones")]
        encuesta_acciones.votar(encuesta_id,session["usuarioID"],opciones_ids,datetime.now())
    except ValueError as error:
        return mostrar_encuesta(encuesta_id,str(error)),400
    flash("Guardamos tu voto. Te avisamos cuando se confirme la fecha.")
    return redirect(url_for("mostrar_inicio"))

@app.route("/encuesta/<int:encuesta_id>/cerrar",methods=["POST"])
@login_requerido
def cerrar_encuesta(encuesta_id):
    try:
        encuesta_acciones.cerrar(encuesta_id,session["usuarioID"],datetime.now())
    except ValueError as error:
        return mostrar_encuesta(encuesta_id,str(error)),400
    return redirect(url_for("mostrar_encuesta",encuesta_id=encuesta_id))

@app.route("/encuesta/<int:encuesta_id>/borrar",methods=["POST"])
@login_requerido
def borrar_encuesta_del_inicio(encuesta_id):
    try:
        encuesta_acciones.ocultar(encuesta_id,session["usuarioID"])
    except ValueError as error:
        return str(error),400
    return redirect(url_for("mostrar_inicio"))

@app.route("/encuesta/<int:encuesta_id>/confirmar",methods=["POST"])
@login_requerido
def confirmar_encuesta(encuesta_id):
    try:
        encuesta_acciones.confirmar(encuesta_id,session["usuarioID"],request.form.get("opcion",type=int),datetime.now())
    except ValueError as error:
        return mostrar_encuesta(encuesta_id,str(error)),400
    return redirect(url_for("mostrar_encuesta",encuesta_id=encuesta_id))

@app.route("/juntada/<int:juntada_id>/responder",methods=["POST"])
@login_requerido
def responder_juntada(juntada_id):
    responder_invitacion(juntada_id, session["usuarioID"], request.form.get("respuesta"), datetime.now(), request.form.get("serie")=="1")
    return volver_al_calendario()

@app.route("/agenda/<int:evento_id>/borrar",methods=["POST"])
@login_requerido
def borrar_evento_propio(evento_id):
    if not borrar_evento(evento_id, session["usuarioID"]):
        return "No se puede borrar este evento.", 400
    return volver_al_calendario()

@app.route("/juntada/<int:juntada_id>/cancelar",methods=["POST"])
@login_requerido
def cancelar_juntada(juntada_id):
    if not borrar_juntada_organizada(juntada_id, session["usuarioID"], datetime.now()):
        return "No se puede cancelar esta juntada.", 400
    return volver_al_calendario()

def juntada_para_reprogramar(juntada_id):
    juntada=obtener_por_id(juntada_id)
    if juntada is None or juntada.organizador_id!=session["usuarioID"] or ya_empezo(juntada.fecha,juntada.hora_inicio,datetime.now()):
        return None
    return juntada

def formulario_reprogramar(juntada,fecha_sugerida,hora_desde,hora_hasta,error=None):
    invitados=[(invitado_id,nombre) for _,invitado_id,nombre,estado in obtener_invitados_de_juntadas([juntada.id]) if estado!="No"]
    inicio,fin=rango_del_evento(juntada.fecha,juntada.hora_inicio,juntada.hora_fin)
    minutos=int((fin-inicio).total_seconds()//60)
    duracion=min((opcion for opcion,_ in DURACIONES_JUNTADA),key=lambda opcion:abs(opcion-minutos))
    return formulario_con_horario(
        "juntada_reprogramar.html",fecha_sugerida,duracion,error,hora_desde,hora_hasta,
        juntada=juntada,invitados=invitados,
        cuando_actual=f"{nombre_del_dia(juntada.fecha)} · {texto_horario(juntada.fecha,juntada.hora_inicio,juntada.hora_fin)}",
    )

@app.route("/juntada/<int:juntada_id>/reprogramar",methods=["GET"])
@login_requerido
def mostrar_reprogramar_juntada(juntada_id):
    juntada=juntada_para_reprogramar(juntada_id)
    if juntada is None:
        return "No se puede reprogramar esta juntada.", 400
    return formulario_reprogramar(juntada,juntada.fecha.isoformat(),f"{juntada.hora_inicio:%H:%M}",f"{juntada.hora_fin:%H:%M}")

@app.route("/juntada/<int:juntada_id>/reprogramar",methods=["POST"])
@login_requerido
def reprogramar(juntada_id):
    juntada=juntada_para_reprogramar(juntada_id)
    if juntada is None:
        return "No se puede reprogramar esta juntada.", 400
    fecha_parametro=request.form.get("fecha","")
    ahora=datetime.now()
    try:
        fecha_formateada=datetime.strptime(fecha_parametro,"%Y-%m-%d").strftime("%d/%m/%Y")
        reprogramacion=Reprogramacion(fecha_formateada,request.form.get("hora_inicio"),request.form.get("hora_fin"),ahora)
        reprogramacion.validar_que_cambie(juntada.fecha,juntada.hora_inicio,juntada.hora_fin)
    except ValueError as error:
        return formulario_reprogramar(juntada,fecha_parametro,"","",str(error)), 400

    if not reprogramar_juntada(juntada_id,session["usuarioID"],reprogramacion,ahora):
        return "No se puede reprogramar esta juntada.", 400
    return redirect(url_for("mostrar_calendario",fecha=fecha_parametro,juntada=juntada_id))

@app.route("/juntada/<int:juntada_id>/cancelar-serie",methods=["POST"])
@login_requerido
def cancelar_serie_de_juntadas(juntada_id):
    if not cancelar_serie(juntada_id, session["usuarioID"], datetime.now()):
        return "No se puede cancelar esta serie.", 400
    return volver_al_calendario()

@app.route("/juntada/<int:juntada_id>/abandonar",methods=["POST"])
@login_requerido
def abandonar_juntada(juntada_id):
    if not bajarse_de_juntada(juntada_id, session["usuarioID"], datetime.now()):
        return "No te podés dar de baja de esta juntada.", 400
    return volver_al_calendario()

@app.route("/juntada/<int:juntada_id>/checkin",methods=["GET"])
@login_requerido
def mostrar_checkin(juntada_id):
    usuario_id=session["usuarioID"]
    juntada=obtener_por_id(juntada_id)
    if juntada is None:
        return "No encontramos esa juntada.",404
    organiza=juntada.organizador_id==usuario_id
    invitado=any(invitado_id==usuario_id and estado!="No" for _,invitado_id,_,estado in obtener_invitados_de_juntadas([juntada_id]))
    if not organiza and not invitado:
        return "No estás en la lista de esta juntada.",403
    ahora=datetime.now()
    return render_template(
        "checkin.html",juntada=juntada,organiza=organiza,
        abierto=se_puede_habilitar(juntada.fecha,juntada.hora_inicio,juntada.hora_fin,ahora) if organiza else not checkin_cerrado(juntada.fecha,juntada.hora_inicio,juntada.hora_fin,ahora),
        anticipado=not se_puede_hacer_checkin(juntada.fecha,juntada.hora_inicio,juntada.hora_fin,ahora),
        cerrado=checkin_cerrado(juntada.fecha,juntada.hora_inicio,juntada.hora_fin,ahora),
        ya_hizo=juntada_id in juntadas_con_asistencia(usuario_id,[juntada_id]),
        cuando=f"{nombre_del_dia(juntada.fecha)} · {texto_horario(juntada.fecha,juntada.hora_inicio,juntada.hora_fin)}",
        presentes=[nombre for presente_id,nombre in presentes(juntada_id) if presente_id!=usuario_id],
        modo_local=not USA_AIVEN,
    )

def posicion_del_pedido(datos):
    return Posicion(datos.get("latitud"),datos.get("longitud"),datos.get("precision"))

@app.route("/juntada/<int:juntada_id>/qr",methods=["POST"])
@login_requerido
def codigo_de_checkin(juntada_id):
    usuario_id=session["usuarioID"]
    juntada=obtener_por_id(juntada_id)
    ahora=datetime.now()
    if juntada is None or juntada.organizador_id!=usuario_id:
        return {"error":"Solo quien organiza puede mostrar el QR"},403
    if not se_puede_habilitar(juntada.fecha,juntada.hora_inicio,juntada.hora_fin,ahora):
        return {"error":"El check-in de esta juntada no está disponible ahora"},400
    try:
        posicion=posicion_del_pedido(request.get_json(silent=True) or {})
    except ValueError as error:
        return {"error":str(error)},400
    return {
        "codigo":generar_codigo(app.config["SECRET_KEY"],juntada_id,posicion,ahora),
        "segundos":SEGUNDOS_POR_CODIGO,
        "presentes":[nombre for presente_id,nombre in presentes(juntada_id) if presente_id!=usuario_id],
    }

@app.route("/checkin",methods=["POST"])
@login_requerido
def hacer_checkin():
    usuario_id=session["usuarioID"]
    datos=request.get_json(silent=True) or {}
    ahora=datetime.now()
    try:
        juntada_id,posicion_organizador=leer_codigo(app.config["SECRET_KEY"],datos.get("codigo"),ahora)
        posicion=posicion_del_pedido(datos)
        if not posicion.esta_cerca_de(posicion_organizador):
            raise ValueError("Parece que no estás en el mismo lugar que quien organiza. Acercate y probá de nuevo")
        titulo=registrar_checkin(juntada_id,usuario_id,ahora)
    except ValueError as error:
        return {"error":str(error)},400
    logros=logros_de([usuario_id])[usuario_id]
    return {"mensaje":f"¡Listo! Estás en «{titulo}»","racha":logros.racha_actual,"perfil":url_for("mostrar_perfil")}

@app.route("/juntada/<int:juntadaID>/comentar",methods=["POST"])
@login_requerido
def comentarJuntada(juntadaID):
    try:
        comentario=Comentario(juntadaID,session["usuarioID"],request.form.get("texto"))
    except ValueError as error:
        return str(error),400
    if not guardarComentario(comentario,datetime.now()):
        return "No podes comentar en esta juntada",400
    return redirect(url_for("mostrar_calendario",fecha=request.form.get("fecha"),juntada=juntadaID))

def textoMonto(monto):
    entero,decimales=f"{monto:,.2f}".split(".")
    return "$ "+entero.replace(",",".")+","+decimales

def volverAlGasto(juntadaID,error=None):
    return redirect(url_for("mostrar_calendario",fecha=request.form.get("fecha"),juntada=juntadaID,errorGasto=error))

@app.route("/juntada/<int:juntadaID>/gasto",methods=["POST"])
@login_requerido
def cargarGasto(juntadaID):
    usuarioID=session["usuarioID"]
    participantesIDs=request.form.getlist("participantes",type=int)
    partes=None
    if request.form.get("division")=="personalizado":
        partes={participanteID:request.form.get(f"parte_{participanteID}","") for participanteID in participantesIDs}
    try:
        gasto=Gasto(
            juntadaID,usuarioID,
            request.form.get("pagador",usuarioID,type=int),
            request.form.get("descripcion"),
            request.form.get("monto",""),
            participantesIDs,
            partes,
        )
    except ValueError as error:
        return volverAlGasto(juntadaID,str(error))
    if guardarGasto(gasto,datetime.now()) is None:
        return volverAlGasto(juntadaID,"Solo los que participan de la juntada pueden estar en un gasto")
    return volverAlGasto(juntadaID)

@app.route("/juntada/<int:juntadaID>/saldar",methods=["POST"])
@login_requerido
def saldarDeuda(juntadaID):
    try:
        monto=leerMonto(request.form.get("monto",""))
    except ValueError as error:
        return volverAlGasto(juntadaID,str(error))
    motivo=saldarDeudaEnBase(
        juntadaID,session["usuarioID"],
        request.form.get("deudorID",type=int),request.form.get("acreedorID",type=int),
        monto,datetime.now()
    )
    return volverAlGasto(juntadaID,motivo)


@app.route("/gasto/<int:gastoID>/borrar",methods=["POST"])
@login_requerido
def borrarGastoPropio(gastoID):
    juntadaID=request.form.get("juntada",type=int)
    if not borrarGasto(gastoID,session["usuarioID"]):
        return volverAlGasto(juntadaID,"Solo podes borrar los gastos que cargaste vos")
    return volverAlGasto(juntadaID)

@app.route("/amistad",methods=["GET"])
@login_requerido
def mostrar_amistad():
    nombre=request.args.get("nombre","")
    usuarios=obtenerTodos()
    buscado=sin_acentos(nombre.strip())
    personas=[usuario for usuario in usuarios if buscado and buscado in sin_acentos(usuario.nombre)]
    amigos=obtener_amigos(session["usuarioID"])
    amigos_ids={amigo.id for amigo in amigos}
    sugerencias=[
        usuario for usuario in usuarios
        if usuario.id != session["usuarioID"]
    ]

    return render_template(
        "amistad.html",
        personas=personas,
        nombre=nombre,
        recibidas=solicitudes_recibidas(),
        sugerencias=sugerencias,
        amigos=amigos,
        amigos_ids=amigos_ids,
        grupos=obtenerGrupos(session["usuarioID"])
    )

@app.route("/amistad/enviar/<int:receptorID>",methods=["POST"])
@login_requerido
def enviar_solicitud(receptorID):
    emisorID=session["usuarioID"]
    receptor=buscarPorID(receptorID)
    if receptor is None or not receptor.activo:
        return "Ese usuario no está disponible.",400
    solicitud=enviarSolicitud(emisorID,receptorID)

    if solicitud is None:
        return "No se puede enviar esta solicitud.", 400

    return redirect(url_for("mostrar_amistad"))

@app.route("/amistad/aceptar/<int:solicitudID>",methods=["POST"])
@login_requerido
def aceptar_solicitud(solicitudID):
    aceptada=aceptarSolicitud(solicitudID,session["usuarioID"])

    if not aceptada:
        return "No se puede aceptar esta solicitud.", 400

    return volver_a(url_for("mostrar_amistad"))

@app.route("/amistad/rechazar/<int:solicitudID>",methods=["POST"])
@login_requerido
def rechazar_solicitud(solicitudID):
    rechazada=rechazarSolicitud(solicitudID,session["usuarioID"])

    if not rechazada:
        return "No se puede rechazar esta solicitud.", 400

    return volver_a(url_for("mostrar_amistad"))

@app.route("/categorias",methods=["POST"])
@login_requerido
def crear_categoria_propia():
    try:
        return crear_categoria(session["usuarioID"],Categoria(request.form.get("nombre"),request.form.get("color")))
    except ValueError as error:
        return {"error":str(error)},400

@app.route("/categorias/<int:categoria_id>/borrar",methods=["POST"])
@login_requerido
def borrar_categoria_propia(categoria_id):
    if not borrar_categoria(categoria_id,session["usuarioID"]):
        return "No se puede borrar esta categoría.", 400
    return redirect(url_for("mostrar_perfil"))

@app.route("/notificaciones",methods=["GET"])
@login_requerido
def mostrar_notificaciones():
    return render_template("_notificaciones.html")

@app.route("/notificaciones/leidas",methods=["POST"])
@login_requerido
def marcar_notificaciones_leidas():
    marcar_leidas(session["usuarioID"])
    return "",204

@app.route("/amistad/eliminar/<int:amigoID>",methods=["POST"])
@login_requerido
def eliminar_amigo(amigoID):
    eliminado=eliminarAmigo(session["usuarioID"],amigoID)

    if not eliminado:
        return "No se puede eliminar esta amistad.", 400

    return redirect(url_for("mostrar_amistad"))

@app.route("/grupo/nuevo",methods=["GET"])
@login_requerido
def mostrarNuevoGrupo():
    return render_template("grupo_nuevo.html",amigos=obtener_amigos(session["usuarioID"]),nombre="",seleccionados=[],error=None)

@app.route("/grupo/nuevo",methods=["POST"])
@login_requerido
def crearGrupo():
    usuarioID=session["usuarioID"]
    nombre=request.form.get("nombre","")
    miembrosIDs=[int(miembroID) for miembroID in request.form.getlist("miembros")]
    amigos=obtener_amigos(usuarioID)
    amigosIDs=[amigo.id for amigo in amigos]
    try:
        grupo=Grupo(usuarioID,nombre,miembrosIDs)
        if not set(miembrosIDs).issubset(amigosIDs):
            raise ValueError("Solo podes agregar a tus amigos")
    except ValueError as error:
        return render_template("grupo_nuevo.html",amigos=amigos,nombre=nombre,seleccionados=miembrosIDs,error=str(error)),400
    guardarGrupo(grupo)
    return redirect(url_for("mostrar_amistad"))

@app.route("/grupo/<int:grupoID>/borrar",methods=["POST"])
@login_requerido
def borrarGrupoPropio(grupoID):
    if not borrarGrupo(grupoID,session["usuarioID"]):
        return "No se puede borrar este grupo",400
    return redirect(url_for("mostrar_amistad"))

@app.route("/disponibilidad",methods=["GET"])
@login_requerido
def consultar_disponibilidad():
    try:
        fecha=date.fromisoformat(request.args.get("fecha",""))
    except ValueError:
        return {"error":"Elegí una fecha válida."},400
    minutos=request.args.get("duracion",type=int)
    if minutos is None or not 0<minutos<=24*60:
        return {"error":"Elegí una duración válida."},400

    duracion=timedelta(minutes=minutos)
    lunes=fecha-timedelta(days=fecha.weekday())
    inicio=datetime.combine(lunes,time(0))
    fin=inicio+timedelta(days=7)+duracion
    try:
        ocupados=obtener_disponibilidad(session["usuarioID"],request.args.getlist("amigos",type=int),lunes,fin.date(),request.args.get("excluir",type=int))
    except ValueError as error:
        return {"error":str(error)},403

    todos=[(bloque["inicio"],bloque["fin"]) for bloques in ocupados.values() for bloque in bloques]
    desde=max(inicio,proxima_media_hora(datetime.now()))
    huecos=buscar_huecos(todos,desde,fin,duracion)

    return {
        "yo":session["usuarioID"],
        "titulo":titulo_semana(lunes),
        "desde":a_texto(desde),
        "ocupados":{usuario_id:[[a_texto(bloque["inicio"]),a_texto(bloque["fin"]),bloque.get("titulo")] for bloque in bloques] for usuario_id,bloques in ocupados.items()},
        "dias":[{
            **dia_de_la_grilla(dia),
            "huecos":[{"inicio":a_texto(inicio),"fin":a_texto(fin)} for inicio,fin in huecos_del_dia(huecos,dia,duracion)],
        } for dia in dias_de_la_semana(lunes)],
    }

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
