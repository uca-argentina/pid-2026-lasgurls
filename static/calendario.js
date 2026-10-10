(function () {
  var ESTRECHO = window.matchMedia("(max-width: 700px)");
  var ETIQUETAS = {
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
  var filtros = { categoria: {}, tipo: {} };

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

  function nombreDeCategoria(evento) {
    if (!evento.categoria && evento.tipo !== "personal") return null;
    return evento.categoria || "Sin categoría";
  }

  var GRUPOS = {
    categoria: { selector: "[data-leyenda-categorias]", valor: nombreDeCategoria },
    tipo: {
      selector: "[data-leyenda-tipos]",
      valor: function (evento) { return ETIQUETAS[evento.tipo] ? evento.tipo : null; },
    },
  };

  function pasaElFiltro(evento) {
    return Object.keys(GRUPOS).every(function (grupo) {
      var elegidos = filtros[grupo];
      return Object.keys(elegidos).length === 0 || GRUPOS[grupo].valor(evento) in elegidos;
    });
  }

  function horaInicial() {
    var visibles = diasVisibles().map(function (dia) { return dia.fecha; });
    var horas = datos.eventos.filter(pasaElFiltro).filter(function (evento) {
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

  function opcionesDelGrupo(grupo) {
    var opciones = {};
    datos.eventos.forEach(function (evento) {
      var valor = GRUPOS[grupo].valor(evento);
      if (valor && !opciones[valor]) opciones[valor] = evento;
    });
    return opciones;
  }

  function dibujarLeyenda(grupo) {
    var leyenda = document.querySelector(GRUPOS[grupo].selector);
    var opciones = opcionesDelGrupo(grupo);
    var elegidos = filtros[grupo];
    Object.keys(elegidos).forEach(function (valor) {
      if (!opciones[valor]) delete elegidos[valor];
    });
    var hayElegidos = Object.keys(elegidos).length > 0;

    leyenda.replaceChildren();
    Object.keys(opciones).forEach(function (valor) {
      var elegido = valor in elegidos;
      var evento = opciones[valor];
      var texto = grupo === "tipo" ? ETIQUETAS[valor] : valor;
      var boton = crear("button", "leyenda-filtro" + (hayElegidos && !elegido ? " leyenda-filtro-apagada" : ""), texto);
      boton.type = "button";
      boton.dataset.filtroGrupo = grupo;
      boton.dataset.filtroValor = valor;
      boton.setAttribute("aria-pressed", String(elegido));
      boton.prepend(grupo === "tipo" ? crear("i", "evento-" + valor) : circuloDeCategoria(evento));
      var item = crear("li");
      item.appendChild(boton);
      leyenda.appendChild(item);
    });
  }

  document.addEventListener("click", function (evento) {
    var boton = evento.target.closest("[data-filtro-grupo]");
    if (!boton || !datos) return;
    var elegidos = filtros[boton.dataset.filtroGrupo];
    var valor = boton.dataset.filtroValor;
    if (valor in elegidos) delete elegidos[valor];
    else elegidos[valor] = true;
    dibujar(false);
  });

  function dibujar(ubicar) {
    var contenedor = document.querySelector("[data-grilla-calendario]");
    if (!contenedor) return;
    dibujarLeyenda("categoria");
    dibujarLeyenda("tipo");

    var eventos = datos.eventos.map(function (evento, indice) {
      return { inicio: new Date(evento.inicio).getTime(), fin: new Date(evento.fin).getTime(), indice: indice };
    }).filter(function (posicion) {
      return pasaElFiltro(datos.eventos[posicion.indice]);
    });
    GrillaSemanal.asignarCarriles(eventos);

    var bloques = eventos.map(function (posicion) {
      var evento = datos.eventos[posicion.indice];
      var inicio = new Date(posicion.inicio);
      var fin = new Date(posicion.fin);
      return {
        inicio: inicio, fin: fin, izquierda: posicion.izquierda, ancho: posicion.ancho,
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
    var boton = crear("button", "dialogo-menu-opcion", texto);
    boton.type = "button";
    boton.addEventListener("click", function () {
      boton.closest("ul").hidden=true;
      var volver = crear("button", "boton-neutro dialogo-cerrar", "Volver");
      volver.type = "button";
      volver.addEventListener("click", function () {
        mostrarDetalle(evento);
      });
      var acciones = crear("div", "dialogo-acciones");
      acciones.append(volver, formularioPost(url, {}, textoConfirmar, "boton-peligro"));
      var dialogo = document.querySelector("[data-detalle-evento]");
      var avisoViejo=dialogo.querySelector(".detalle-aviso");
      if(avisoViejo)avisoViejo.remove();
      var aviso=crear("p", "detalle-aviso", pregunta);
      var accionesViejas=dialogo.querySelector(".dialogo-acciones");
      if(accionesViejas)accionesViejas.replaceWith(aviso,acciones);
      else dialogo.append(aviso,acciones);
    });
    return boton;
  }

  function menuMas(opciones){
    var menu=crear("div","dialogo-menu");
    var boton=crear("button","","⋯");
    boton.type="button";
    boton.setAttribute("aria-label","Mas opciones");
    var lista=crear("ul");
    lista.hidden=true;
    opciones.forEach(function(opcion){
      var item=crear("li");
      item.appendChild(opcion);
      lista.appendChild(item);
    });
    boton.addEventListener("click",function(){
      lista.hidden=!lista.hidden;
    });
    menu.append(boton,lista);
    return menu;
  }

  function cruzCerrar(){
    var formulario=crear("form","dialogo-cruz");
    formulario.method="dialog";
    var boton=crear("button","","×");
    boton.setAttribute("aria-label","Cerrar");
    boton.autofocus=true;
    formulario.appendChild(boton);
    return formulario;
  }

  function parrafoDeLugar(evento){
    var parrafo=crear("p","detalle-lugar",evento.ubicacion+" · ");
    var enlace=crear("a","","Ver en el mapa");
    enlace.href=evento.mapa;
    enlace.target="_blank";
    enlace.rel="noopener";
    parrafo.appendChild(enlace);
    return parrafo;
  }

  function seccionDeComentarios(evento){
    var seccion=crear("div","detalle-personas detalle-comentarios");
    seccion.appendChild(crear("p","detalle-personas-titulo","Comentarios"));
    if(evento.comentarios.length){
      var lista=crear("ul");
      evento.comentarios.forEach(function(comentario){
        var item=crear("li");
        var cuerpo=crear("div","detalle-comentario");
        cuerpo.append(crear("span","detalle-comentario-autor",comentario.nombre+" · "+comentario.cuando),crear("span","",comentario.texto));
        item.append(crear("span","avatar avatar-chico",comentario.iniciales),cuerpo);
        lista.appendChild(item);
      });
      seccion.appendChild(lista);
    }else{
      seccion.appendChild(crear("p","detalle-sin-comentarios","Todavia no hay comentarios"));
    }
    var formulario=formularioPost(evento.comentar,{},"Comentar","boton-neutro");
    formulario.className="detalle-comentar";
    var campo=crear("input");
    campo.type="text";
    campo.name="texto";
    campo.maxLength=500;
    campo.required=true;
    campo.placeholder="Escribi un comentario";
    campo.dataset.mensaje="Escribí un comentario antes de enviarlo.";
    formulario.insertBefore(campo,formulario.lastChild);
    seccion.appendChild(formulario);
    return seccion;
  }

  function abrirJuntadaPedida(){
    var url=new URL(window.location.href);
    var juntadaID=Number(url.searchParams.get("juntada"));
    if(!juntadaID)return;
    url.searchParams.delete("juntada");
    window.history.replaceState({},"",url.pathname+url.search);
    var evento=datos.eventos.find(function(item){return item.juntadaID===juntadaID;});
    if(evento)mostrarDetalle(evento);
  }

  function mostrarDetalle(evento) {
    var dialogo = document.querySelector("[data-detalle-evento]");
    var etiqueta = evento.tipo === "personal"
      ? evento.categoria || "Sin categoría"
      : ETIQUETAS[evento.tipo] + (evento.categoria ? " · " + evento.categoria : "");
    var tipo = crear("p", "detalle-tipo", etiqueta);
    tipo.prepend(circuloDeCategoria(evento));
    var acciones = crear("div", "dialogo-acciones");

    if (evento.responder) {
      [["No", "Rechazar", "boton-neutro boton-rechazar"], ["Tal vez", "Tal vez", "boton-neutro"], ["Si", "Aceptar", "boton-principal"]]
        .forEach(function (opcion) {
          if (opcion[0] === "Tal vez" && evento.tipo === "tal_vez") return;
          acciones.appendChild(formularioPost(evento.responder, { respuesta: opcion[0] }, opcion[1], opcion[2]));
        });
    }
    var opciones=[];
    if (evento.reprogramar) {
      var reprogramar = crear("a", "dialogo-menu-opcion dialogo-menu-opcion-neutra", "Reprogramar");
      reprogramar.href = evento.reprogramar;
      opciones.push(reprogramar);
    }
    if (evento.cancelar && evento.cancelar_serie) {
      opciones.push(botonConConfirmacion(evento, "Cancelar esta fecha",
        "¿Cancelás solo la juntada de " + evento.cuando + "? Las demás fechas de la serie siguen igual.",
        "Sí, cancelar esta fecha", evento.cancelar));
      opciones.push(botonConConfirmacion(evento, "Cancelar toda la serie",
        "¿Cancelás todas las fechas que quedan de «" + evento.titulo + "»? Se borran para todos los invitados y no se puede deshacer.",
        "Sí, cancelar la serie", evento.cancelar_serie));
    } else if (evento.cancelar) {
      opciones.push(botonConConfirmacion(evento, "Cancelar juntada",
        "¿Seguro que querés cancelar «" + evento.titulo + "»? Se borra para todos los invitados y no se puede deshacer.",
        "Sí, cancelar juntada", evento.cancelar));
    }
    if (evento.borrar) {
      opciones.push(botonConConfirmacion(evento, "Borrar evento",
        "¿Seguro que querés borrar «" + evento.titulo + "»? No se puede deshacer.",
        "Sí, borrar evento", evento.borrar));
    }
    if (evento.abandonar) {
      opciones.push(botonConConfirmacion(evento, "No voy a ir",
        "¿Te das de baja de «" + evento.titulo + "»? El organizador va a ver que ya no vas.",
        "Sí, darme de baja", evento.abandonar));
    }
    var arriba=crear("div","dialogo-arriba");
    if(opciones.length)arriba.appendChild(menuMas(opciones));
    arriba.appendChild(cruzCerrar());

    var contenido = [arriba, tipo, crear("h3", "", evento.titulo), crear("p", "detalle-cuando", evento.cuando), crear("p", "", evento.detalle)];
    if(evento.ubicacion)contenido.splice(4,0,parrafoDeLugar(evento));
    if (evento.personas.length) contenido.push(listaDePersonas(evento.personas));
    if(evento.comentar)contenido.push(seccionDeComentarios(evento));
    if(acciones.children.length)contenido.push(acciones);
    dialogo.replaceChildren.apply(dialogo, contenido);
    if (!dialogo.open) dialogo.showModal();
    var listaComentarios=dialogo.querySelector(".detalle-comentarios ul");
    if(listaComentarios)listaComentarios.scrollTop=listaComentarios.scrollHeight;
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

  document.addEventListener("click",function(evento){
    document.querySelectorAll(".dialogo-menu ul:not([hidden])").forEach(function(lista){
      if(!lista.parentNode.contains(evento.target))lista.hidden=true;
    });
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

  function actualizarDatos() {
    if (!datos || document.hidden || document.querySelector("dialog[open]")) return;
    fetch(window.location.href)
      .then(function (respuesta) {
        return respuesta.ok && !respuesta.redirected ? respuesta.text() : null;
      })
      .then(function (html) {
        if (html === null || !datos || document.querySelector("dialog[open]")) return;
        var nueva = new DOMParser().parseFromString(html, "text/html").querySelector("[data-datos-calendario]");
        var actual = document.querySelector("[data-datos-calendario]");
        if (!nueva || !actual || nueva.textContent === actual.textContent) return;
        var fecha = datos.fecha;
        actual.textContent = nueva.textContent;
        leerDatos();
        datos.fecha = fecha;
        dibujar(false);
      })
      .catch(function () {});
  }

  setInterval(actualizarDatos, 15000);
  document.addEventListener("visibilitychange", actualizarDatos);

  if (leerDatos()) dibujar(true);
  if(datos)abrirJuntadaPedida();
})();
