import pytest
from dominio.categoria import Categoria, CATEGORIAS_DE_FABRICA, COLORES


def test_categoria_valida():
    categoria = Categoria("  Gimnasio ", "#3F8F8A")

    assert categoria.nombre == "Gimnasio"
    assert categoria.color == "#3f8f8a"


def test_nombre_vacio_es_invalido():
    with pytest.raises(ValueError) as error:
        Categoria("   ", "#3f8f8a")
    assert str(error.value) == "La categoría tiene que tener un nombre"


def test_nombre_demasiado_largo_es_invalido():
    with pytest.raises(ValueError) as error:
        Categoria("x" * 31, "#3f8f8a")
    assert str(error.value) == "El nombre de la categoría puede tener hasta 30 caracteres"


def test_color_fuera_de_la_paleta_es_invalido():
    with pytest.raises(ValueError) as error:
        Categoria("Gimnasio", "#00ff00")
    assert str(error.value) == "Elegí uno de los colores disponibles"


def test_compara_nombres_sin_importar_mayusculas_ni_espacios():
    categoria = Categoria("Facultad", "#6f86b8")

    assert categoria.se_llama_igual_que(" facultad ")
    assert not categoria.se_llama_igual_que("Trabajo")


def test_las_categorias_de_fabrica_usan_colores_de_la_paleta():
    for nombre, color in CATEGORIAS_DE_FABRICA:
        assert Categoria(nombre, color).color in COLORES
