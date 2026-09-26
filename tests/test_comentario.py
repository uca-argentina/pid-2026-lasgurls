import pytest
from dominio.comentario import Comentario


def test_comentarioValido():
    comentario=Comentario(1,2,"  Llevo las empanadas ")

    assert comentario.juntadaID==1
    assert comentario.usuarioID==2
    assert comentario.texto=="Llevo las empanadas"


def test_comentarioVacioEsInvalido():
    with pytest.raises(ValueError) as error:
        Comentario(1,2,"   ")
    assert str(error.value)=="El comentario no puede estar vacio"


def test_comentarioSinTextoEsInvalido():
    with pytest.raises(ValueError) as error:
        Comentario(1,2,None)
    assert str(error.value)=="El comentario no puede estar vacio"


def test_comentarioDemasiadoLargoEsInvalido():
    with pytest.raises(ValueError) as error:
        Comentario(1,2,"x"*501)
    assert str(error.value)=="El comentario puede tener hasta 500 caracteres"


def test_comentarioDeExactamente500CaracteresEsValido():
    comentario=Comentario(1,2,"x"*500)

    assert len(comentario.texto)==500
