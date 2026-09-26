from datetime import datetime, time, timedelta


def unir_ocupados(ocupados):
    unidos = []
    for inicio, fin in sorted(ocupados):
        if unidos and inicio <= unidos[-1][1]:
            unidos[-1] = (unidos[-1][0], max(unidos[-1][1], fin))
        else:
            unidos.append((inicio, fin))
    return unidos


def buscar_huecos(ocupados, desde, hasta, duracion):
    if duracion <= timedelta(0):
        raise ValueError("La duración tiene que ser mayor a cero")

    huecos = []
    actual = desde
    for inicio, fin in unir_ocupados(ocupados):
        if fin <= actual:
            continue
        if inicio >= hasta:
            break
        if inicio - actual >= duracion:
            huecos.append((actual, inicio))
        actual = max(actual, fin)

    if hasta - actual >= duracion:
        huecos.append((actual, hasta))
    return huecos


def huecos_del_dia(huecos, dia, duracion):
    comienzo = datetime.combine(dia, time(0))
    final = comienzo + timedelta(days=1)
    resultado = []
    for inicio, fin in huecos:
        desde = max(inicio, comienzo)
        if desde >= final or fin - desde < duracion:
            continue
        resultado.append((desde, min(fin, max(final, desde + duracion))))
    return resultado


def proxima_media_hora(momento):
    redondeado = momento.replace(second=0, microsecond=0) + timedelta(minutes=29)
    return redondeado - timedelta(minutes=redondeado.minute % 30)
