from datetime import datetime, time, timedelta


def rango_del_evento(fecha, hora_inicio, hora_fin):
    inicio = datetime.combine(fecha, hora_inicio)
    fin = datetime.combine(fecha, hora_fin)
    if fin <= inicio:
        fin += timedelta(days=1)
    return inicio, fin


def termina_al_dia_siguiente(fecha, hora_inicio, hora_fin):
    inicio, fin = rango_del_evento(fecha, hora_inicio, hora_fin)
    return fin.date() > inicio.date() and fin.time() != time(0)


def ya_empezo(fecha, hora_inicio, ahora):
    return datetime.combine(fecha, hora_inicio) <= ahora
