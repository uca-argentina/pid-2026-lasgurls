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
    var avatares = visibles.slice(0, MAXIMO_AVATARES).map(function (persona) { return { texto: persona.iniciales, estilo: persona.estilo }; });
    if (visibles.length > MAXIMO_AVATARES) avatares.push({ texto: "+" + (visibles.length - MAXIMO_AVATARES) });
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
      var nombre = crear("span", "detalle-persona-nombre");
      nombre.appendChild(Avatar.nombre(persona.nombre, persona.estilo));
      item.append(
        Avatar.crear(persona.iniciales, persona.estilo, "avatar-chico"),
        nombre,
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

  function hayFiltros() {
    return Object.keys(filtros).some(function (grupo) { return Object.keys(filtros[grupo]).length > 0; });
  }

  function dibujarOpcionTodos() {
    var lista = document.querySelector("[data-leyenda-todos]");
    if (!lista) return;
    lista.replaceChildren();
    var hayOpciones = Object.keys(GRUPOS).some(function (grupo) { return Object.keys(opcionesDelGrupo(grupo)).length > 0; });
    if (!hayOpciones) return;
    var boton = crear("button", "leyenda-filtro" + (hayFiltros() ? " leyenda-filtro-apagada" : ""), "Todos");
    boton.type = "button";
    boton.dataset.filtroTodos = "";
    boton.setAttribute("aria-pressed", String(!hayFiltros()));
    boton.prepend(crear("i", "leyenda-todos"));
    var item = crear("li");
    item.appendChild(boton);
    lista.appendChild(item);
  }

  document.addEventListener("click", function (evento) {
    if (!evento.target.closest("[data-filtro-todos]") || !datos) return;
    filtros = { categoria: {}, tipo: {} };
    dibujar(false);
  });

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
    dibujarOpcionTodos();

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

  var mesAbierto=false;

  function diaCorrido(fecha,dias){
    var dia=new Date(fecha+"T12:00");
    dia.setDate(dia.getDate()+dias);
    return fechaIso(dia);
  }

  function aplicarMes(){
    var lateral=document.querySelector(".calendario-lateral");
    var boton=document.querySelector("[data-ver-mes]");
    if(!lateral||!boton)return;
    lateral.classList.toggle("mes-abierto",mesAbierto);
    boton.textContent=mesAbierto?"Ocultar mes":"Ver mes";
    boton.setAttribute("aria-expanded",mesAbierto);
  }

  function acomodarParaCelu(){
    var anterior=document.querySelector("[data-anterior]");
    var siguiente=document.querySelector("[data-siguiente]");
    var titulo=document.querySelector("[data-titulo-calendario]");
    if(!anterior||!siguiente||!titulo)return;
    if(ESTRECHO.matches){
      anterior.href=conParametros(window.location.pathname,{fecha:diaCorrido(datos.fecha,-1)});
      siguiente.href=conParametros(window.location.pathname,{fecha:diaCorrido(datos.fecha,1)});
      anterior.setAttribute("aria-label","Dia anterior");
      siguiente.setAttribute("aria-label","Dia siguiente");
      var dia=datos.dias.find(function(item){return item.fecha===datos.fecha;});
      titulo.textContent=dia?dia.nombre:titulo.dataset.semana;
    }else{
      anterior.href=anterior.dataset.semana;
      siguiente.href=siguiente.dataset.semana;
      anterior.setAttribute("aria-label","Semana anterior");
      siguiente.setAttribute("aria-label","Semana siguiente");
      titulo.textContent=titulo.dataset.semana;
    }
    aplicarMes();
  }

  function elegirDia(fecha, guardarHistorial) {
    datos.fecha = fecha;
    mesAbierto=false;
    document.querySelectorAll(".mini-calendario-dia").forEach(function (link) {
      link.classList.toggle("mini-calendario-dia-seleccionado", link.dataset.fecha === fecha);
    });
    document.querySelectorAll("[data-con-fecha]").forEach(function (link) {
      link.href = conParametros(link.href, { fecha: fecha });
    });
    if (guardarHistorial) window.history.pushState({}, "", conParametros(window.location.href, { fecha: fecha }));
    dibujar(ESTRECHO.matches);
    acomodarParaCelu();
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

  function iconoDeLugar(){
    var svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
    svg.setAttribute("viewBox","0 0 24 24");
    svg.setAttribute("width","18");
    svg.setAttribute("height","18");
    svg.setAttribute("aria-hidden","true");
    svg.innerHTML='<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><circle cx="12" cy="10" r="3" fill="none" stroke="currentColor" stroke-width="1.8"/>';
    var icono=crear("span","lugar-icono");
    icono.appendChild(svg);
    return icono;
  }

  function tarjetaDeLugar(lugar){
    var tarjeta=crear("div","lugar");
    var encabezado=crear("div","lugar-encabezado");
    var textos=crear("span","lugar-textos");
    var enlace=crear("a","lugar-abrir","Abrir en Google Maps");
    enlace.href=lugar.mapa;
    enlace.target="_blank";
    enlace.rel="noopener";
    textos.append(crear("strong","lugar-nombre",lugar.texto),enlace);
    encabezado.append(iconoDeLugar(),textos);
    var mapa=crear("iframe","lugar-mapa");
    mapa.src=lugar.embebido;
    mapa.title="Mapa de "+lugar.texto;
    mapa.loading="lazy";
    mapa.referrerPolicy="no-referrer-when-downgrade";
    tarjeta.append(encabezado,mapa);
    return tarjeta;
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
        item.append(Avatar.crear(comentario.iniciales,comentario.estilo,"avatar-chico"),cuerpo);
        lista.appendChild(item);
      });
      seccion.appendChild(lista);
    }else{
      seccion.appendChild(crear("p","detalle-sin-comentarios","Todavia no hay comentarios"));
    }
    var formulario=formularioPost(evento.comentar,{},"Comentar","boton-neutro");
    formulario.dataset.enLugar=evento.juntadaID;
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

  function aCentavos(texto){
    var limpio=String(texto||"").trim().replace(",",".");
    if(!/^\d+(\.\d{1,2})?$/.test(limpio))return null;
    var partes=limpio.split(".");
    return Number(partes[0])*100+Number(((partes[1]||"")+"00").slice(0,2));
  }

  function textoCentavos(centavos){
    var entero=String(Math.floor(centavos/100)).replace(/\B(?=(\d{3})+(?!\d))/g,".");
    return "$ "+entero+","+String(centavos%100).padStart(2,"0");
  }

  function campoGasto(etiqueta,control){
    var campo=crear("label","gasto-campo");
    campo.append(crear("span","gasto-etiqueta",etiqueta),control);
    return campo;
  }

  var ICONO_TILDE='<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>';
  var ICONO_TACHO='<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 11v6M14 11v6"/></svg>';

  function formularioDeGasto(evento){
    var formulario=formularioPost(evento.cargarGasto,{},"Guardar gasto","boton-principal");
    formulario.dataset.enLugar=evento.juntadaID;
    formulario.className="formulario-gasto";
    var guardar=formulario.lastChild;

    var descripcion=crear("input");
    descripcion.name="descripcion";
    descripcion.maxLength=60;
    descripcion.required=true;
    descripcion.placeholder="Por ejemplo: pizzas";
    descripcion.dataset.mensaje="Escribi que fue el gasto";

    var monto=crear("input");
    monto.name="monto";
    monto.inputMode="decimal";
    monto.required=true;
    monto.placeholder="0,00";
    monto.dataset.mensaje="Escribi cuanto salio";

    var pagador=crear("select");
    pagador.name="pagador";
    evento.personasGasto.forEach(function(persona){
      var opcion=crear("option","",persona.nombre);
      opcion.value=persona.id;
      opcion.selected=persona.id===datos.usuarioID;
      pagador.appendChild(opcion);
    });

    var personas=crear("div","gasto-personas");
    personas.dataset.requiereUno="Elegi al menos una persona para dividir el gasto";
    evento.personasGasto.forEach(function(persona){
      var fila=crear("div","gasto-persona");
      var casilla=crear("input");
      casilla.type="checkbox";
      casilla.name="participantes";
      casilla.value=persona.id;
      casilla.checked=true;
      casilla.id="gasto-persona-"+persona.id;
      var nombre=crear("label","",persona.nombre);
      nombre.htmlFor=casilla.id;
      var parte=crear("input","gasto-parte");
      parte.name="parte_"+persona.id;
      parte.inputMode="decimal";
      parte.placeholder="0,00";
      parte.setAttribute("aria-label","Parte de "+persona.nombre);
      parte.required=true;
      parte.dataset.mensaje="Pone cuanto le toca a "+persona.nombre;
      fila.append(casilla,nombre,parte);
      personas.appendChild(fila);
    });

    var division=crear("div","gasto-division");
    [["iguales","Partes iguales"],["personalizado","Personalizado"]].forEach(function(opcion,indice){
      var etiqueta=crear("label");
      var radio=crear("input");
      radio.type="radio";
      radio.name="division";
      radio.value=opcion[0];
      radio.checked=indice===0;
      etiqueta.append(radio,crear("span","",opcion[1]));
      division.appendChild(etiqueta);
    });

    var cuenta=crear("p","gasto-cuenta");

    function actualizar(){
      var personalizado=formulario.querySelector('input[name="division"]:checked').value==="personalizado";
      var suma=0;
      var elegidas=0;
      personas.querySelectorAll(".gasto-persona").forEach(function(fila){
        var casilla=fila.querySelector('input[type="checkbox"]');
        var parte=fila.querySelector(".gasto-parte");
        parte.hidden=!personalizado||!casilla.checked;
        parte.disabled=parte.hidden;
        if(casilla.checked){
          elegidas++;
          suma+=aCentavos(parte.value)||0;
        }
      });
      var total=aCentavos(monto.value);
      guardar.disabled=personalizado&&problemaDelGasto()!==null;
      cuenta.hidden=!personalizado||total===null||!elegidas;
      cuenta.classList.remove("gasto-cuenta-ok");
      if(cuenta.hidden)return;
      if(suma===total){
        cuenta.textContent="Suma justo el total";
        cuenta.classList.add("gasto-cuenta-ok");
      }else if(suma<total){
        cuenta.textContent="Faltan "+textoCentavos(total-suma)+" para llegar al total";
      }else{
        cuenta.textContent="Te pasaste por "+textoCentavos(suma-total);
      }
    }
    formulario.addEventListener("input",actualizar);
    formulario.addEventListener("change",actualizar);

    function problemaDelGasto(){
      var total=aCentavos(monto.value);
      if(total===null)return "Escribi un monto valido";
      if(total===0)return "El monto tiene que ser mayor a 0";
      if(formulario.querySelector('input[name="division"]:checked').value!=="personalizado")return null;
      var suma=0;
      var problema=null;
      personas.querySelectorAll(".gasto-persona").forEach(function(fila){
        if(problema||!fila.querySelector('input[type="checkbox"]').checked)return;
        var parte=aCentavos(fila.querySelector(".gasto-parte").value);
        if(!parte)problema="Escribi un monto valido";
        else suma+=parte;
      });
      if(problema)return problema;
      if(suma!==total)return "Las partes tienen que sumar el total del gasto";
      return null;
    }

    formulario.tieneProblema=function(){return problemaDelGasto()!==null;};
    formulario.addEventListener("submit",function(eventoEnvio){
      var problema=problemaDelGasto();
      if(!problema)return;
      eventoEnvio.preventDefault();
      cuenta.hidden=false;
      cuenta.classList.remove("gasto-cuenta-ok");
      cuenta.textContent=problema;
    });

    var montoYPagador=crear("div","gasto-fila");
    montoYPagador.append(campoGasto("Cuanto",monto),campoGasto("Pago",pagador));
    formulario.insertBefore(campoGasto("Que fue",descripcion),guardar);
    formulario.insertBefore(montoYPagador,guardar);
    formulario.insertBefore(crear("span","gasto-etiqueta","Entre quienes"),guardar);
    formulario.insertBefore(division,guardar);
    formulario.insertBefore(personas,guardar);
    formulario.insertBefore(cuenta,guardar);
    actualizar();
    return formulario;
  }

  function seccionDeGastos(evento){
    var seccion=crear("div","detalle-personas detalle-gastos");
    seccion.appendChild(crear("p","detalle-personas-titulo","Gastos"));
    if(evento.gastos.length){
      var lista=crear("ul");
      evento.gastos.forEach(function(gasto){
        var item=crear("li","gasto-item");
        var cuerpo=crear("div","detalle-gasto");
        var arriba=crear("div","detalle-gasto-arriba");
        arriba.append(crear("strong","detalle-gasto-nombre",gasto.descripcion),crear("span","detalle-gasto-monto",gasto.monto));
        var partes=crear("div","gasto-partes");
        gasto.partes.forEach(function(parte){
          var chip=crear("span","gasto-parte-chip",parte.nombre+" ");
          chip.appendChild(crear("b","",parte.monto));
          partes.appendChild(chip);
        });
        cuerpo.append(arriba,crear("span","detalle-gasto-reparto","Pagó "+gasto.pagador),partes);
        item.appendChild(cuerpo);
        if(gasto.borrar){
          var borrar=formularioPost(gasto.borrar,{juntada:evento.juntadaID},"","boton-icono");
          borrar.className="detalle-gasto-borrar";
          borrar.dataset.enLugar=evento.juntadaID;
          borrar.lastChild.innerHTML=ICONO_TACHO;
          borrar.lastChild.setAttribute("aria-label","Borrar gasto "+gasto.descripcion);
          borrar.lastChild.title="Borrar gasto";
          item.appendChild(borrar);
        }
        lista.appendChild(item);
      });
      seccion.appendChild(lista);
    }else{
      seccion.appendChild(crear("p","detalle-sin-comentarios","Todavia no hay gastos"));
    }
    var error=datos.errorGasto&&datos.errorGastoJuntada===evento.juntadaID?datos.errorGasto:null;
    datos.errorGasto=null;
    if(error)seccion.appendChild(crear("p","detalle-aviso",error));
    var formulario=formularioDeGasto(evento);
    formulario.hidden=!error;
    var agregar=crear("button","boton-neutro boton-chico gasto-agregar","Agregar gasto");
    agregar.type="button";
    agregar.hidden=!!error;
    agregar.addEventListener("click",function(){
      formulario.hidden=false;
      agregar.hidden=true;
      formulario.querySelector('input[name="descripcion"]').focus();
    });
    seccion.append(agregar,formulario);
    return seccion;
  }

  function seccionDeSaldos(evento){
    var seccion=crear("div","detalle-personas detalle-saldos");
    seccion.appendChild(crear("p","detalle-personas-titulo","Quién le debe a quién"));
    if(evento.saldos.length){
      var lista=crear("ul","saldos");
      evento.saldos.forEach(function(saldo){
        var tipo=saldo.deudor==="Vos"?"debes":saldo.acreedor==="Vos"?"te-deben":"otros";
        var frase=tipo==="debes"
          ?"Le debés a "+saldo.acreedor
          :tipo==="te-deben"
            ?saldo.deudor+" te debe"
            :saldo.deudor+" le debe a "+saldo.acreedor;
        var item=crear("li","saldo saldo-"+tipo);
        var info=crear("div","saldo-info");
        info.append(crear("span","saldo-frase",frase),crear("strong","saldo-monto",saldo.monto));
        item.appendChild(info);
        if(saldo.saldar){
          var saldar=formularioPost(evento.saldar,Object.assign({juntada:evento.juntadaID},saldo.saldar),"Marcar como saldada","boton-saldar");
          saldar.className="saldo-accion";
          saldar.dataset.enLugar=evento.juntadaID;
          saldar.lastChild.insertAdjacentHTML("afterbegin",ICONO_TILDE);
          item.appendChild(saldar);
        }
        lista.appendChild(item);
      });
      seccion.appendChild(lista);
    }else{
      seccion.appendChild(crear("p","detalle-sin-comentarios",evento.gastos.length?"Están todos a mano.":"Cuando haya gastos vas a ver acá quién le debe a quién."));
    }
    if(evento.saldadas.length){
      seccion.appendChild(crear("p","detalle-saldos-titulo","Ya saldadas"));
      var saldadas=crear("ul","detalle-saldadas");
      evento.saldadas.forEach(function(texto){
        var item=crear("li","",texto);
        item.insertAdjacentHTML("afterbegin",ICONO_TILDE);
        saldadas.appendChild(item);
      });
      seccion.appendChild(saldadas);
    }
    return seccion;
  }

  function abrirJuntadaPedida(){
    var url=new URL(window.location.href);
    var juntadaID=Number(url.searchParams.get("juntada"));
    if(!juntadaID)return;
    url.searchParams.delete("juntada");
    url.searchParams.delete("errorGasto");
    window.history.replaceState({},"",url.pathname+url.search);
    datos.errorGastoJuntada=juntadaID;
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
    if (evento.asistio) {
      var hecho = crear("p", "detalle-checkin-hecho", "Esta juntada ya cuenta para tu racha");
      hecho.insertAdjacentHTML("afterbegin", '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>');
      contenido.push(hecho);
    } else if (evento.checkin) {
      var checkin = crear("a", "boton-principal detalle-checkin", evento.tipo === "organizo" ? "Mostrar QR de check-in" : "Hacer check-in");
      checkin.href = evento.checkin;
      contenido.push(checkin);
    }
    if(evento.lugar)contenido.push(tarjetaDeLugar(evento.lugar));
    if (evento.personas.length) contenido.push(listaDePersonas(evento.personas));
    if(evento.cargarGasto)contenido.push(seccionDeGastos(evento),seccionDeSaldos(evento));
    if(evento.comentar)contenido.push(seccionDeComentarios(evento));
    if(acciones.children.length)contenido.push(acciones);
    dialogo.replaceChildren.apply(dialogo, contenido);
    if (!dialogo.open) dialogo.showModal();
    var listaComentarios=dialogo.querySelector(".detalle-comentarios ul");
    if(listaComentarios)listaComentarios.scrollTop=listaComentarios.scrollHeight;
  }

  function mostrarError(dialogo,texto){
    var aviso=dialogo.querySelector(".detalle-aviso-en-lugar")||crear("p","detalle-aviso detalle-aviso-en-lugar");
    aviso.textContent=texto;
    dialogo.querySelector(".dialogo-arriba").after(aviso);
  }

  function enviarEnLugar(formulario){
    var dialogo=document.querySelector("[data-detalle-evento]");
    var juntadaID=Number(formulario.dataset.enLugar);
    var boton=formulario.querySelector("button");
    var scroll=dialogo.scrollTop;
    var cuerpo=new FormData(formulario);
    dialogo.classList.add("dialogo-cargando");
    dialogo.querySelectorAll("button").forEach(function(otro){otro.disabled=true;});
    if(boton)boton.classList.add("boton-cargando");

    function terminar(){
      dialogo.classList.remove("dialogo-cargando");
    }

    fetch(formulario.action,{method:"POST",body:cuerpo})
      .then(function(respuesta){
        return respuesta.text().then(function(texto){return {respuesta:respuesta,texto:texto};});
      })
      .then(function(resultado){
        terminar();
        var nueva=resultado.respuesta.ok&&new DOMParser().parseFromString(resultado.texto,"text/html").querySelector("[data-datos-calendario]");
        var actual=document.querySelector("[data-datos-calendario]");
        if(!nueva||!actual){
          var evento=datos.eventos.find(function(item){return item.juntadaID===juntadaID;});
          if(evento)mostrarDetalle(evento);
          mostrarError(dialogo,resultado.respuesta.ok?"Algo salió mal. Recargá la página.":resultado.texto);
          return;
        }
        var fecha=datos.fecha;
        actual.textContent=nueva.textContent;
        leerDatos();
        datos.fecha=fecha;
        var error=new URL(resultado.respuesta.url).searchParams.get("errorGasto");
        datos.errorGasto=error;
        datos.errorGastoJuntada=juntadaID;
        dibujar(false);
        var actualizado=datos.eventos.find(function(item){return item.juntadaID===juntadaID;});
        if(!actualizado){
          dialogo.close();
          return;
        }
        mostrarDetalle(actualizado);
        dialogo.scrollTop=scroll;
      })
      .catch(function(){
        terminar();
        dialogo.querySelectorAll("button").forEach(function(otro){otro.disabled=false;});
        if(boton)boton.classList.remove("boton-cargando");
        mostrarError(dialogo,"No pudimos conectarnos. Revisá tu conexión y probá de nuevo.");
      });
  }

  document.addEventListener("submit",function(evento){
    var formulario=evento.target;
    if(formulario.dataset.enLugar===undefined||!formulario.closest("[data-detalle-evento]"))return;
    if(formulario.tieneProblema&&formulario.tieneProblema())return;
    evento.preventDefault();
    enviarEnLugar(formulario);
  },true);

  function abrirCrear(inicio) {
    var dialogo = document.querySelector("[data-crear-en-horario]");
    var fecha = fechaIso(inicio);
    var dia = datos.dias.find(function (item) { return item.fecha === fecha; });
    var parametros = { fecha: fecha, hora: textoHora(inicio) };
    var acciones = crear("div", "dialogo-acciones");
    var evento = crear("a", "boton-neutro", "Nuevo evento");
    evento.href = conParametros(datos.urls.nuevo_evento, parametros);
    var juntada = crear("a", "boton-principal", "Nueva juntada");
    juntada.href = conParametros(datos.urls.nueva_juntada, parametros);
    acciones.append(evento, juntada);
    var arriba=crear("div","dialogo-arriba");
    arriba.appendChild(cruzCerrar());
    dialogo.replaceChildren(arriba, crear("h3", "", "¿Qué querés agendar?"), crear("p", "detalle-cuando", dia.nombre + " a las " + textoHora(inicio)), acciones);
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

  document.addEventListener("click",function(evento){
    if(evento.target.closest("[data-ver-mes]")){
      mesAbierto=!mesAbierto;
      aplicarMes();
    }else if(evento.target.closest(".mini-calendario-dia")){
      mesAbierto=false;
    }
  });

  document.addEventListener("contenido-actualizado", function () {
    if (leerDatos()) dibujar(true);
    if(datos)acomodarParaCelu();
  });
  ESTRECHO.addEventListener("change", function () {
    dibujar(true);
    if(datos)acomodarParaCelu();
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
  if(datos)acomodarParaCelu();
  if(datos)abrirJuntadaPedida();
})();
