import pytest
from dominio.grupo import Grupo


def test_grupoValido():
    grupo=Grupo(1,"  Las de la facu ",[2,3])

    assert grupo.creadorID==1
    assert grupo.nombre=="Las de la facu"
    assert grupo.miembrosIDs==[2,3]


def test_grupoSinNombreEsInvalido():
    with pytest.raises(ValueError) as error:
        Grupo(1,"   ",[2,3])
    assert str(error.value)=="El grupo tiene que tener un nombre"


def test_grupoConNombreDemasiadoLargoEsInvalido():
    with pytest.raises(ValueError) as error:
        Grupo(1,"x"*31,[2,3])
    assert str(error.value)=="El nombre del grupo puede tener hasta 30 caracteres"


def test_grupoDeExactamente30CaracteresEsValido():
    grupo=Grupo(1,"x"*30,[2])

    assert len(grupo.nombre)==30


def test_grupoSinAmigosEsInvalido():
    with pytest.raises(ValueError) as error:
        Grupo(1,"Las de la facu",[])
    assert str(error.value)=="El grupo tiene que tener al menos un amigo"


def test_grupoConMiembrosEnNoneEsInvalido():
    with pytest.raises(ValueError) as error:
        Grupo(1,"Las de la facu",None)
    assert str(error.value)=="El grupo tiene que tener al menos un amigo"


def test_noPodesEstarEnTuPropioGrupo():
    with pytest.raises(ValueError) as error:
        Grupo(1,"Las de la facu",[1,2])
    assert str(error.value)=="No podes estar en tu propio grupo"
