(function () {
  var formulario = document.querySelector("[data-formulario-con-disponibilidad]");
  if (!formulario) return;

  var crear = GrillaSemanal.crear;
  var textoHora = GrillaSemanal.textoHora;
  var fechaIso = GrillaSemanal.fechaIso;
  var esJuntada = formulario.dataset.formularioConDisponibilidad === "juntada";
  var TEXTOS = esJuntada
    ? {
        libre: "Libres todos",
        sinLugarEnLaSemana: "Esta semana no hay un horario libre para todos. Probá con otra semana o con una duración más corta.",
        sinLugarEnElDia: " no hay un horario libre para todos. Elegí un espacio verde de otro día.",
        libresEnElDia: "Libres para todos el ",
      }
    : {
        libre: "Libre",
        sinLugarEnLaSemana: "Esta semana no tenés un horario libre. Probá con otra semana o con una duración más corta.",
        sinLugarEnElDia: " no tenés un horario libre. Elegí un espacio verde de otro día.",
        libresEnElDia: "Tenés libre el ",
      };

  var panel = formulario.querySelector("[data-disponibilidad]");
  var grilla = panel.querySelector("[data-grilla]");
  var tituloSemana = panel.querySelector("[data-titulo-semana]");
  var leyenda = panel.querySelector("[data-leyenda]");
  var contenedorHuecos = panel.querySelector("[data-huecos]");
  var aviso = formulario.querySelector("[data-aviso-choque]");
  var campoFecha = formulario.querySelector("#fecha");
  var campoDuracion = formulario.querySelector("#duracion");
  var campoDesde = formulario.querySelector("#hora_inicio");
  var campoHasta = formulario.querySelector("#hora_fin");
  var UN_DIA = 24 * 60 * 60 * 1000;
  var COLORES_PERSONAS = 5;

  var semana = campoFecha.value || fechaIso(new Date());
  var datos = null;
  var peticion = null;
  var espera = null;

  function duracion() {
    return Number(campoDuracion.value) * 60000;
  }

  function amigosElegidos() {
    return Array.from(formulario.querySelectorAll('input[name="invitados"]:checked'));
  }

  function personas() {
    var misIniciales = document.querySelector(".boton-avatar .avatar").textContent.trim();
    return [{ id: String(datos.yo), nombre: "Vos", iniciales: misIniciales }].concat(amigosElegidos().map(function (casilla) {
      return { id: casilla.value, nombre: casilla.dataset.nombre, iniciales: casilla.dataset.iniciales };
    }));
  }

  function rangoElegido() {
    if (!campoFecha.value || !campoDesde.value || !campoHasta.value || campoDesde.value === campoHasta.value) return null;
    var inicio = new Date(campoFecha.value + "T" + campoDesde.value);
    var fin = new Date(campoFecha.value + "T" + campoHasta.value);
    if (fin <= inicio) fin = new Date(fin.getTime() + UN_DIA);
    return [inicio, fin];
  }

  function elegirHorario(inicio) {
    campoFecha.value = fechaIso(inicio);
    campoDesde.value = textoHora(inicio);
    campoHasta.value = textoHora(new Date(inicio.getTime() + duracion()));
    dibujar();
  }

  function libresUnidos() {
    var libres = [];
    datos.dias.forEach(function (dia) {
      dia.huecos.forEach(function (hueco) {
        var inicio = new Date(hueco.inicio);
        var fin = new Date(hueco.fin);
        var ultimo = libres[libres.length - 1];
        if (ultimo && inicio <= ultimo[1]) ultimo[1] = new Date(Math.max(ultimo[1], fin));
        else libres.push([inicio, fin]);
      });
    });
    return libres;
  }

  function inicioSugerido(momento) {
    var libre = libresUnidos().find(function (intervalo) {
      return momento >= intervalo[0] && momento < intervalo[1];
    });
    if (!libre) return null;
    var inicio = Math.max(GrillaSemanal.mediaHora(momento).getTime(), libre[0].getTime());
    return new Date(Math.min(inicio, libre[1].getTime() - duracion()));
  }

  function dibujarLeyenda() {
    leyenda.replaceChildren();
    personas().forEach(function (persona, indice) {
      var item = crear("span", "", persona.nombre);
      item.prepend(crear("i", "leyenda-avatar grilla-persona-" + (indice % COLORES_PERSONAS), persona.iniciales));
      leyenda.appendChild(item);
    });
    formulario.querySelectorAll('input[name="invitados"]').forEach(function (casilla) {
      var avatar = casilla.parentElement.querySelector(".avatar");
      avatar.className = "avatar avatar-chico";
      var indice = amigosElegidos().indexOf(casilla) + 1;
      if (indice > 0) avatar.classList.add("grilla-persona-" + (indice % COLORES_PERSONAS));
    });
    [["grilla-libre", TEXTOS.libre], ["grilla-pasado", "Ya pasó"]].forEach(function (par) {
      var item = crear("span", "", par[1]);
      item.prepend(crear("i", "leyenda-muestra " + par[0]));
      leyenda.appendChild(item);
    });
  }

  function tramosOcupados() {
    var bloques = [];
    personas().forEach(function (persona, indice) {
      (datos.ocupados[persona.id] || []).forEach(function (bloque) {
        bloques.push({ inicio: new Date(bloque[0]).getTime(), fin: new Date(bloque[1]).getTime(), persona: indice });
      });
    });
    var bordes = [];
    bloques.forEach(function (bloque) {
      bordes.push(bloque.inicio, bloque.fin);
    });
    bordes = bordes.filter(function (borde, posicion) { return bordes.indexOf(borde) === posicion; }).sort(function (a, b) { return a - b; });

    var lista = personas();
    var tramos = [];
    for (var i = 0; i < bordes.length - 1; i++) {
      var ocupados = bloques.filter(function (bloque) {
        return bloque.inicio <= bordes[i] && bloque.fin >= bordes[i + 1];
      }).map(function (bloque) { return bloque.persona; });
      ocupados = ocupados.filter(function (persona, posicion) { return ocupados.indexOf(persona) === posicion; }).sort();
      if (!ocupados.length) continue;
      var anterior = tramos[tramos.length - 1];
      if (anterior && anterior.fin.getTime() === bordes[i] && anterior.clave === ocupados.join()) {
        anterior.fin = new Date(bordes[i + 1]);
      } else {
        tramos.push({
          inicio: new Date(bordes[i]), fin: new Date(bordes[i + 1]), clave: ocupados.join(),
          personas: ocupados.map(function (indice) {
            return Object.assign({ color: indice % COLORES_PERSONAS }, lista[indice]);
          }),
        });
      }
    }
    return tramos;
  }

  function nombresJuntos(lista) {
    var nombres = lista.map(function (persona) { return persona.nombre; });
    if (nombres.length > 2) return nombres.length + " personas";
    return nombres.join(" y ");
  }

  function dibujarGrilla(hora) {
    var bloques = [];

    datos.dias.forEach(function (dia) {
      dia.huecos.forEach(function (hueco) {
        bloques.push({ inicio: new Date(hueco.inicio), fin: new Date(hueco.fin), clase: "grilla-libre", titulo: TEXTOS.libre + ": hacé clic para elegir" });
      });
    });

    tramosOcupados().forEach(function (tramo) {
      var nombres = nombresJuntos(tramo.personas);
      var horario = textoHora(tramo.inicio) + "–" + textoHora(tramo.fin);
      bloques.push({
        inicio: tramo.inicio, fin: tramo.fin,
        clase: "evento " + (tramo.personas.length === 1 ? "ocupado-persona-" + tramo.personas[0].color : "ocupado-varios"),
        avatares: tramo.personas.map(function (persona) {
          return { texto: persona.iniciales, clase: "grilla-persona-" + persona.color };
        }),
        titulo: nombres + (tramo.personas.length === 1 ? " está ocupado/a" : " están ocupados") + " de " + horario,
      });
    });

    var elegido = rangoElegido();
    if (elegido) bloques.push({ inicio: elegido[0], fin: elegido[1], clase: "grilla-elegido" });

    GrillaSemanal.dibujar(grilla, {
      hora: hora,
      bloques: bloques,
      dias: datos.dias,
      fechaElegida: campoFecha.value,
      pasadoHasta: new Date(datos.desde),
    });
  }

  function textoHueco(hueco) {
    var inicio = new Date(hueco.inicio);
    var fin = new Date(hueco.fin);
    if (fin - inicio >= UN_DIA) return "Todo el día";
    var diaSiguiente = fin.getDate() !== inicio.getDate();
    if (diaSiguiente && textoHora(fin) === "00:00") return textoHora(inicio) + " – 24:00";
    return textoHora(inicio) + " – " + textoHora(fin) + (diaSiguiente ? " (+1)" : "");
  }

  function botonHueco(hueco) {
    var inicio = new Date(hueco.inicio);
    var boton = crear("button", "hueco", textoHueco(hueco));
    boton.type = "button";
    if (fechaIso(inicio) === campoFecha.value && campoDesde.value === textoHora(inicio)) boton.classList.add("hueco-elegido");
    boton.addEventListener("click", function () {
      elegirHorario(inicio);
    });
    return boton;
  }

  function mensaje(texto) {
    contenedorHuecos.appendChild(crear("p", "disponibilidad-mensaje", texto));
  }

  function dibujarHuecos() {
    contenedorHuecos.replaceChildren();
    if (!datos.dias.some(function (dia) { return dia.huecos.length; })) {
      var finDeSemana = new Date(datos.dias[6].fecha + "T00:00").getTime() + UN_DIA;
      mensaje(new Date(datos.desde).getTime() >= finDeSemana
        ? "Esta semana ya pasó."
        : TEXTOS.sinLugarEnLaSemana);
      var siguiente = crear("button", "boton-secundario", "Ver la semana siguiente");
      siguiente.type = "button";
      siguiente.addEventListener("click", function () {
        cambiarSemana(1);
      });
      contenedorHuecos.appendChild(siguiente);
      return;
    }

    var dia = datos.dias.find(function (item) {
      return item.fecha === campoFecha.value;
    });
    if (!dia) {
      mensaje("Hacé clic en un espacio verde para elegir el horario.");
      return;
    }
    var nombre = dia.nombre.charAt(0).toLowerCase() + dia.nombre.slice(1);
    if (!dia.huecos.length) {
      mensaje("El " + nombre + TEXTOS.sinLugarEnElDia);
      return;
    }
    mensaje(TEXTOS.libresEnElDia + nombre + " (o hacé clic en cualquier espacio verde):");
    var fila = crear("div", "huecos");
    dia.huecos.forEach(function (hueco) {
      fila.appendChild(botonHueco(hueco));
    });
    contenedorHuecos.appendChild(fila);
  }

  function revisarChoque() {
    var elegido = rangoElegido();
    var ocupados = !datos || !elegido ? [] : personas().filter(function (persona) {
      return (datos.ocupados[persona.id] || []).some(function (bloque) {
        return new Date(bloque[0]) < elegido[1] && new Date(bloque[1]) > elegido[0];
      });
    });
    aviso.hidden = !ocupados.length;
    if (!ocupados.length) aviso.textContent = "";
    else if (!esJuntada) aviso.textContent = "En ese horario ya tenés algo. Podés crear el evento igual.";
    else aviso.textContent = "En ese horario ya tienen algo: " + ocupados.map(function (persona) {
      return persona.nombre === "Vos" ? "vos" : persona.nombre;
    }).join(", ") + ". Podés crear la juntada igual.";
  }

  function dibujar(hora) {
    if (datos) {
      tituloSemana.textContent = datos.titulo;
      dibujarLeyenda();
      dibujarGrilla(hora);
      dibujarHuecos();
    }
    revisarChoque();
  }

  function consultar(cambiaLaSemana) {
    clearTimeout(espera);
    espera = setTimeout(function () {
      if (peticion) peticion.abort();
      var controlador = new AbortController();
      peticion = controlador;

      var parametros = new URLSearchParams({ fecha: semana, duracion: campoDuracion.value });
      amigosElegidos().forEach(function (casilla) {
        parametros.append("amigos", casilla.value);
      });
      panel.hidden = false;
      panel.classList.add("cargando");

      fetch(panel.dataset.disponibilidad + "?" + parametros, { signal: controlador.signal })
        .then(function (respuesta) {
          return respuesta.json().then(function (cuerpo) {
            if (!respuesta.ok) throw { mensaje: cuerpo.error };
            return cuerpo;
          });
        })
        .then(function (cuerpo) {
          datos = cuerpo;
          var elegido = rangoElegido();
          dibujar(cambiaLaSemana ? (elegido ? Math.max(elegido[0].getHours() - 1, 0) : 8) : undefined);
        })
        .catch(function (error) {
          if (error && error.name === "AbortError") return;
          datos = null;
          grilla.replaceChildren();
          contenedorHuecos.replaceChildren();
          mensaje((error && error.mensaje) || "No pudimos consultar la disponibilidad. Probá de nuevo.");
          revisarChoque();
        })
        .finally(function () {
          if (peticion !== controlador) return;
          peticion = null;
          panel.classList.remove("cargando");
        });
    }, 250);
  }

  function cambiarSemana(semanas) {
    var dia = new Date(semana + "T00:00");
    dia.setDate(dia.getDate() + semanas * 7);
    semana = fechaIso(dia);
    consultar(true);
  }

  grilla.addEventListener("mousemove", function (evento) {
    var libre = evento.target.closest(".grilla-libre");
    var inicio = libre && inicioSugerido(GrillaSemanal.momentoEn(libre.parentElement, evento));
    if (inicio) GrillaSemanal.mostrarFantasma(grilla, inicio, new Date(inicio.getTime() + duracion()), textoHora(inicio));
    else GrillaSemanal.borrarFantasma(grilla);
  });
  grilla.addEventListener("mouseleave", function () {
    GrillaSemanal.borrarFantasma(grilla);
  });
  grilla.addEventListener("click", function (evento) {
    var libre = evento.target.closest(".grilla-libre");
    if (!libre) return;
    var inicio = inicioSugerido(GrillaSemanal.momentoEn(libre.parentElement, evento));
    if (inicio) elegirHorario(inicio);
  });

  panel.querySelectorAll("[data-semana]").forEach(function (boton) {
    boton.addEventListener("click", function () {
      if (boton.dataset.semana === "hoy") {
        semana = fechaIso(new Date());
        consultar(true);
      } else {
        cambiarSemana(Number(boton.dataset.semana));
      }
    });
  });
  campoFecha.addEventListener("change", function () {
    if (!campoFecha.value) return;
    semana = campoFecha.value;
    consultar(true);
  });
  campoDuracion.addEventListener("change", function () {
    consultar(false);
  });
  formulario.addEventListener("change", function (evento) {
    if (evento.target.name === "invitados") consultar(false);
  });
  campoDesde.addEventListener("input", function () {
    if (campoDesde.value && !campoHasta.value) {
      campoHasta.value = textoHora(new Date(new Date("2000-01-01T" + campoDesde.value).getTime() + duracion()));
    }
    dibujar();
  });
  campoHasta.addEventListener("input", function () {
    dibujar();
  });

  consultar(true);
})();
