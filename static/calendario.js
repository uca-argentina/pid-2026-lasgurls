(function () {
  var ESTRECHO = window.matchMedia("(max-width: 700px)");
  var ETIQUETAS = {
    personal: "Evento personal",
    organizo: "Juntada que organizás",
    confirmada: "Juntada confirmada",
    pendiente: "Invitación sin responder",
    tal_vez: "Invitación: dijiste tal vez",
  };
  var ESTADOS = {
    organiza: "Organiza",
    Si: "Va",
    "Tal vez": "Tal vez",
    Pendiente: "Sin responder",
    No: "No va",
  };
  var MAXIMO_AVATARES = 3;
  var datos = null;

  var crear = GrillaSemanal.crear;
  var textoHora = GrillaSemanal.textoHora;
  var fechaIso = GrillaSemanal.fechaIso;
  var mediaHora = GrillaSemanal.mediaHora;

  function leerDatos() {
    var fuente = document.querySelector("[data-datos-calendario]");
    datos = fuente ? JSON.parse(fuente.textContent) : null;
    return datos;
  }

  function conParametros(url, parametros) {
    var destino = new URL(url, window.location.href);
    Object.keys(parametros).forEach(function (clave) {
      destino.searchParams.set(clave, parametros[clave]);
    });
    return destino.pathname + destino.search;
  }

  function asignarCarriles(eventos) {
    var grupo = [];
    var finesDeCarril = [];
    var finDelGrupo = 0;
    function cerrarGrupo() {
      grupo.forEach(function (evento) {
        evento.carriles = finesDeCarril.length;
      });
      grupo = [];
      finesDeCarril = [];
    }
    eventos.slice().sort(function (a, b) {
      return a.inicio - b.inicio || b.fin - a.fin;
    }).forEach(function (evento) {
      if (grupo.length && evento.inicio >= finDelGrupo) cerrarGrupo();
      var carril = finesDeCarril.findIndex(function (fin) {
        return fin <= evento.inicio;
      });
      if (carril === -1) {
        carril = finesDeCarril.length;
        finesDeCarril.push(evento.fin);
      } else {
        finesDeCarril[carril] = evento.fin;
      }
      evento.carril = carril;
      grupo.push(evento);
      finDelGrupo = Math.max(finDelGrupo, evento.fin);
    });
    cerrarGrupo();
  }

  function avataresDelBloque(personas) {
    var visibles = personas.filter(function (persona) { return persona.estado !== "No"; });
    var avatares = visibles.slice(0, MAXIMO_AVATARES).map(function (persona) { return persona.iniciales; });
    if (visibles.length > MAXIMO_AVATARES) avatares.push("+" + (visibles.length - MAXIMO_AVATARES));
    return avatares;
  }

  function etiquetaDeRespuesta(estado) {
    return crear("span", "estado-respuesta estado-" + estado.replace(" ", "-").toLowerCase(), ESTADOS[estado]);
  }

  function listaDePersonas(personas) {
    var seccion = crear("div", "detalle-personas");
    seccion.appendChild(crear("p", "detalle-personas-titulo", "Quiénes van"));
    var lista = crear("ul");
    personas.forEach(function (persona) {
      var item = crear("li", persona.estado === "No" ? "detalle-persona-no-va" : "");
      item.append(
        crear("span", "avatar avatar-chico", persona.iniciales),
        crear("span", "detalle-persona-nombre", persona.nombre),
        etiquetaDeRespuesta(persona.estado)
      );
      lista.appendChild(item);
    });
    seccion.appendChild(lista);
    return seccion;
  }

  function diasVisibles() {
    return ESTRECHO.matches
      ? datos.dias.filter(function (dia) { return dia.fecha === datos.fecha; })
      : datos.dias;
  }

  function horaInicial() {
    var visibles = diasVisibles().map(function (dia) { return dia.fecha; });
    var horas = datos.eventos.filter(function (evento) {
      return visibles.indexOf(evento.inicio.slice(0, 10)) !== -1;
    }).map(function (evento) {
      return new Date(evento.inicio).getHours();
    });
    return Math.max(0, Math.min.apply(null, [9].concat(horas)) - 1);
  }

  function circuloDeCategoria(evento) {
    var circulo = crear("i", "evento-" + evento.tipo);
    if (evento.color) circulo.style.setProperty("--color-evento", evento.color);
    return circulo;
  }

  function dibujarLeyendaDeCategorias() {
    var leyenda = document.querySelector("[data-leyenda-categorias]");
    var vistas = {};
    datos.eventos.forEach(function (evento) {
      if (!evento.categoria && evento.tipo !== "personal") return;
      var nombre = evento.categoria || "Sin categoría";
      if (vistas[nombre]) return;
      vistas[nombre] = true;
      var item = crear("li", "", nombre);
      item.prepend(circuloDeCategoria(evento));
      leyenda.appendChild(item);
    });
  }

  function dibujar(ubicar) {
    var contenedor = document.querySelector("[data-grilla-calendario]");
    if (!contenedor) return;
    document.querySelector("[data-leyenda-categorias]").replaceChildren();
    dibujarLeyendaDeCategorias();

    var eventos = datos.eventos.map(function (evento, indice) {
      return { inicio: new Date(evento.inicio).getTime(), fin: new Date(evento.fin).getTime(), indice: indice };
    });
    asignarCarriles(eventos);

    var bloques = eventos.map(function (posicion) {
      var evento = datos.eventos[posicion.indice];
      var inicio = new Date(posicion.inicio);
      var fin = new Date(posicion.fin);
      return {
        inicio: inicio, fin: fin, carril: posicion.carril, carriles: posicion.carriles,
        clase: "evento evento-" + evento.tipo,
        color: evento.color,
        lineas: [evento.titulo, textoHora(inicio) + " – " + textoHora(fin)],
        avatares: avataresDelBloque(evento.personas),
        titulo: evento.titulo + " · " + evento.cuando,
        datos: { evento: posicion.indice },
      };
    });
    GrillaSemanal.dibujar(contenedor, {
      hora: ubicar ? horaInicial() : undefined,
      bloques: bloques,
      dias: diasVisibles(),
      fechaElegida: datos.fecha,
    });
  }

  function elegirDia(fecha, guardarHistorial) {
    datos.fecha = fecha;
    document.querySelectorAll(".mini-calendario-dia").forEach(function (link) {
      link.classList.toggle("mini-calendario-dia-seleccionado", link.dataset.fecha === fecha);
    });
    document.querySelectorAll("[data-con-fecha]").forEach(function (link) {
      link.href = conParametros(link.href, { fecha: fecha });
    });
    if (guardarHistorial) window.history.pushState({}, "", conParametros(window.location.href, { fecha: fecha }));
    dibujar(ESTRECHO.matches);
  }

  window.navegarLocalmente = function (url, guardarHistorial) {
    var destino = new URL(url, window.location.href);
    if (!datos || destino.pathname !== window.location.pathname) return false;
    var fecha = destino.searchParams.get("fecha") || fechaIso(new Date());
    var esDeEstaSemana = datos.dias.some(function (dia) { return dia.fecha === fecha; });
    if (!esDeEstaSemana) return false;
    elegirDia(fecha, guardarHistorial);
    return true;
  };

  function botonCerrar(texto) {
    var formulario = crear("form", "dialogo-cerrar");
    formulario.method = "dialog";
    formulario.appendChild(crear("button", "boton-neutro", texto));
    return formulario;
  }

  function formularioPost(url, campos, texto, clase) {
    var formulario = crear("form");
    formulario.method = "POST";
    formulario.action = url;
    Object.keys(Object.assign({ fecha: datos.fecha }, campos)).forEach(function (nombre) {
      var campo = crear("input");
      campo.type = "hidden";
      campo.name = nombre;
      campo.value = nombre === "fecha" ? datos.fecha : campos[nombre];
      formulario.appendChild(campo);
    });
    formulario.appendChild(crear("button", clase, texto));
    return formulario;
  }

  function botonConConfirmacion(evento, texto, pregunta, textoConfirmar, url) {
    var boton = crear("button", "boton-neutro boton-rechazar", texto);
    boton.type = "button";
    boton.addEventListener("click", function () {
      var volver = crear("button", "boton-neutro dialogo-cerrar", "Volver");
      volver.type = "button";
      volver.addEventListener("click", function () {
        mostrarDetalle(evento);
      });
      var acciones = crear("div", "dialogo-acciones");
      acciones.append(volver, formularioPost(url, {}, textoConfirmar, "boton-peligro"));
      var dialogo = document.querySelector("[data-detalle-evento]");
      dialogo.querySelector(".dialogo-acciones").replaceWith(crear("p", "detalle-aviso", pregunta), acciones);
    });
    return boton;
  }

  function mostrarDetalle(evento) {
    var dialogo = document.querySelector("[data-detalle-evento]");
    var etiqueta = evento.tipo === "personal"
      ? evento.categoria || "Sin categoría"
      : ETIQUETAS[evento.tipo] + (evento.categoria ? " · " + evento.categoria : "");
    var tipo = crear("p", "detalle-tipo", etiqueta);
    tipo.prepend(circuloDeCategoria(evento));
    var acciones = crear("div", "dialogo-acciones");
    acciones.appendChild(botonCerrar("Cerrar"));

    if (evento.responder) {
      [["No", "Rechazar", "boton-neutro boton-rechazar"], ["Tal vez", "Tal vez", "boton-neutro"], ["Si", "Aceptar", "boton-principal"]]
        .forEach(function (opcion) {
          if (opcion[0] === "Tal vez" && evento.tipo === "tal_vez") return;
          acciones.appendChild(formularioPost(evento.responder, { respuesta: opcion[0] }, opcion[1], opcion[2]));
        });
    }
    if (evento.cancelar) {
      acciones.appendChild(botonConConfirmacion(evento, "Cancelar juntada",
        "¿Seguro que querés cancelar «" + evento.titulo + "»? Se borra para todos los invitados y no se puede deshacer.",
        "Sí, cancelar juntada", evento.cancelar));
    }
    if (evento.abandonar) {
      acciones.appendChild(botonConConfirmacion(evento, "No voy a ir",
        "¿Te das de baja de «" + evento.titulo + "»? El organizador va a ver que ya no vas.",
        "Sí, darme de baja", evento.abandonar));
    }

    var contenido = [tipo, crear("h3", "", evento.titulo), crear("p", "detalle-cuando", evento.cuando), crear("p", "", evento.detalle)];
    if (evento.personas.length) contenido.push(listaDePersonas(evento.personas));
    contenido.push(acciones);
    dialogo.replaceChildren.apply(dialogo, contenido);
    if (!dialogo.open) dialogo.showModal();
  }

  function abrirCrear(inicio) {
    var dialogo = document.querySelector("[data-crear-en-horario]");
    var fecha = fechaIso(inicio);
    var dia = datos.dias.find(function (item) { return item.fecha === fecha; });
    var parametros = { fecha: fecha, hora: textoHora(inicio) };
    var acciones = crear("div", "dialogo-acciones");
    acciones.appendChild(botonCerrar("Cancelar"));
    var evento = crear("a", "boton-neutro", "Nuevo evento");
    evento.href = conParametros(datos.urls.nuevo_evento, parametros);
    var juntada = crear("a", "boton-principal", "Nueva juntada");
    juntada.href = conParametros(datos.urls.nueva_juntada, parametros);
    acciones.append(evento, juntada);
    dialogo.replaceChildren(crear("h3", "", "¿Qué querés agendar?"), crear("p", "detalle-cuando", dia.nombre + " a las " + textoHora(inicio)), acciones);
    dialogo.showModal();
  }

  document.addEventListener("mousemove", function (evento) {
    var contenedor = document.querySelector("[data-grilla-calendario]");
    if (!contenedor) return;
    var columna = evento.target.closest(".grilla-columna");
    if (!columna || evento.target !== columna) {
      GrillaSemanal.borrarFantasma(contenedor);
      return;
    }
    var inicio = mediaHora(GrillaSemanal.momentoEn(columna, evento));
    var yaPaso = inicio < new Date();
    columna.style.cursor = yaPaso ? "default" : "";
    if (yaPaso) GrillaSemanal.borrarFantasma(contenedor);
    else GrillaSemanal.mostrarFantasma(contenedor, inicio, new Date(inicio.getTime() + 60 * 60000), "+ " + textoHora(inicio));
  });

  document.addEventListener("click", function (evento) {
    if (!evento.target.closest("[data-grilla-calendario]")) return;
    var bloque = evento.target.closest(".evento");
    var encabezado = evento.target.closest(".grilla-dia");
    var columna = evento.target.closest(".grilla-columna");
    if (bloque) mostrarDetalle(datos.eventos[Number(bloque.dataset.evento)]);
    else if (encabezado) elegirDia(encabezado.dataset.fecha, true);
    else if (columna) {
      var inicio = mediaHora(GrillaSemanal.momentoEn(columna, evento));
      if (inicio >= new Date()) abrirCrear(inicio);
    }
  });

  document.addEventListener("contenido-actualizado", function () {
    if (leerDatos()) dibujar(true);
  });
  ESTRECHO.addEventListener("change", function () {
    dibujar(true);
  });
  setInterval(function () {
    if (datos) dibujar(false);
  }, 60000);

  if (leerDatos()) dibujar(true);
})();
