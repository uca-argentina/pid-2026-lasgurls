from datetime import datetime
from dominio.agenda.agenda import Agenda
import pytest

AHORA = datetime(2026, 9, 1, 12, 0)


def test_creacion_correcta_de_agenda():
    datos=Agenda(1,"15/09/2026","Juntada","18:00","21:00", ahora=AHORA)
    resultado=datos.registrar_agenda()

    assert resultado=={
        "usuario": 1,
        "titulo_reunion": "Juntada",
        "fecha": "2026-09-15",
        "hora_inicio": "18:00:00",
        "hora_fin": "21:00:00",
        "visibilidad": "ocupado",
    }

def test_evento_que_termina_al_dia_siguiente_es_valido():
    datos=Agenda(1,"15/09/2026","Guardia","22:00","06:00", ahora=AHORA)
    resultado=datos.registrar_agenda()

    assert resultado["hora_inicio"]=="22:00:00"
    assert resultado["hora_fin"]=="06:00:00"

def test_datos_hora_inicio_igual_a_hora_fin_es_invalido():
    with pytest.raises(ValueError) as error:
        Agenda(1,"15/09/2026","Juntada","18:00","18:00", ahora=AHORA)
    assert str(error.value) == "La hora de inicio y la de finalización no pueden ser iguales"

def test_formato_fecha_invalido():
    with pytest.raises(ValueError) as error:
        Agenda(1,"15-09-2026","Juntada","18:00","17:00", ahora=AHORA)
    assert str(error.value) == "Formato de fecha inválido: '15-09-2026' (se espera DD/MM/AAAA)"

def test_formato_horario_invalido():
    with pytest.raises(ValueError) as error:
        Agenda(1,"15/09/2026","Juntada","18","17:00", ahora=AHORA)
    assert str(error.value) == "Formato de hora de inicio inválido: '18' (se espera HH:MM)"

def test_titulo_vacio_es_invalido():
    with pytest.raises(ValueError) as error:
        Agenda(1, "15/09/2026", "", "18:00", "21:00", ahora=AHORA)
    assert str(error.value) == "El campo título no puede estar vacío"


def test_usuario_vacio_es_invalido():
    with pytest.raises(ValueError) as error:
        Agenda("", "15/09/2026", "Juntada", "18:00", "21:00", ahora=AHORA)
    assert str(error.value) == "El campo responsable no puede estar vacío"

def test_evento_en_un_dia_que_ya_paso_es_invalido():
    with pytest.raises(ValueError) as error:
        Agenda(1, "31/08/2026", "Dentista", "10:00", "11:00", ahora=AHORA)
    assert str(error.value) == "El evento no puede empezar en un horario que ya pasó"

def test_evento_de_hoy_mas_tarde_es_valido():
    datos = Agenda(1, "01/09/2026", "Dentista", "12:30", "13:00", ahora=AHORA)

    assert datos.registrar_agenda()["hora_inicio"] == "12:30:00"

def test_visibilidad_invalido():
    with pytest.raises(ValueError) as error:
        Agenda(
            usuario_id=1,
            fecha="15/09/2026",
            titulo_reunion="Juntada",
            hora_inicio="18:00",
            hora_fin="21:00",
            visibilidad="secreto",
            ahora=AHORA,
        )
    assert str(error.value) == "La visibilidad tiene que ser : detalle, ocupado"
    
def test_visibilidad_cambia_a_detalle():
    datos = Agenda(
        usuario_id=1,
        fecha="01/09/2026",
        titulo_reunion="Dentista",
        hora_inicio="12:30",
        hora_fin="13:00",
        visibilidad="detalle",
        ahora=AHORA,
    )

    assert datos.registrar_agenda()["visibilidad"] == "detalle"