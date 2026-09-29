window.GrillaSemanal = (function () {
  var UN_DIA = 24 * 60 * 60 * 1000;

  function crear(etiqueta, clase, texto) {
    var elemento = document.createElement(etiqueta);
    if (clase) elemento.className = clase;
    if (texto !== undefined) elemento.textContent = texto;
    return elemento;
  }

  function dosCifras(numero) {
    return String(numero).padStart(2, "0");
  }

  function textoHora(momento) {
    return dosCifras(momento.getHours()) + ":" + dosCifras(momento.getMinutes());
  }

  function fechaIso(momento) {
    return momento.getFullYear() + "-" + dosCifras(momento.getMonth() + 1) + "-" + dosCifras(momento.getDate());
  }

  function mediaHora(momento) {
    var redondeado = new Date(momento);
    redondeado.setMinutes(redondeado.getMinutes() < 30 ? 0 : 30, 0, 0);
    return redondeado;
  }

  function asignarCarriles(eventos) {
    var grupo = [];
    var finesDeCarril = [];
    var finDelGrupo = 0;
    function cerrarGrupo() {
      grupo.forEach(function (evento) {
        evento.izquierda = (evento.carril / finesDeCarril.length) * 100;
        evento.ancho = 100 / finesDeCarril.length;
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

  function inicioDelDia(fecha) {
    return new Date(fecha + "T00:00");
  }

  function agregarBloque(columnas, bloque) {
    columnas.forEach(function (columna) {
      var dia = inicioDelDia(columna.dataset.fecha).getTime();
      var inicio = Math.max(bloque.inicio.getTime(), dia);
      var fin = Math.min(bloque.fin.getTime(), dia + UN_DIA);
      if (fin <= inicio) return;

      var elemento = crear("span", "grilla-bloque " + (bloque.clase || ""), bloque.texto);
      elemento.style.top = ((inicio - dia) / UN_DIA) * 100 + "%";
      elemento.style.height = ((fin - inicio) / UN_DIA) * 100 + "%";
      elemento.style.left = (bloque.izquierda || 0) + "%";
      elemento.style.width = (bloque.ancho || 100) + "%";
      if (bloque.titulo) elemento.title = bloque.titulo;
      if (bloque.color) elemento.style.setProperty("--color-evento", bloque.color);
      (bloque.lineas || []).forEach(function (linea, indice) {
        elemento.appendChild(crear(indice === 0 ? "strong" : "span", "grilla-linea", linea));
      });
      (bloque.filas || []).forEach(function (fila) {
        var renglon = crear("span", "grilla-fila " + (fila.clase || ""));
        if (fila.avatar) renglon.appendChild(crear("span", "grilla-avatar " + (fila.avatar.clase || ""), fila.avatar.texto));
        if (fila.texto) renglon.appendChild(crear("span", "grilla-fila-texto", fila.texto));
        elemento.appendChild(renglon);
      });
      if (bloque.avatares && bloque.avatares.length) {
        var avatares = crear("span", "grilla-avatares");
        bloque.avatares.forEach(function (avatar) {
          avatares.appendChild(crear("span", "grilla-avatar", avatar));
        });
        elemento.appendChild(avatares);
      }
      Object.keys(bloque.datos || {}).forEach(function (clave) {
        elemento.dataset[clave] = bloque.datos[clave];
      });
      columna.appendChild(elemento);
    });
  }

  function dibujar(contenedor, opciones) {
    var desplazamiento = contenedor.scrollTop;
    var ahora = new Date();
    var hoy = fechaIso(ahora);
    var tabla = crear("div", "grilla-tabla");
    tabla.appendChild(crear("span", "grilla-esquina"));

    opciones.dias.forEach(function (dia) {
      var clases = (dia.fecha === hoy ? " grilla-dia-hoy" : "") + (dia.fecha === opciones.fechaElegida ? " grilla-dia-elegido" : "");
      var encabezado = crear("span", "grilla-dia" + clases, dia.titulo);
      encabezado.dataset.fecha = dia.fecha;
      encabezado.appendChild(crear("strong", "", String(dia.numero)));
      tabla.appendChild(encabezado);
    });

    var horas = crear("div", "grilla-horas");
    for (var hora = 1; hora < 24; hora++) {
      var marca = crear("span", "", dosCifras(hora) + ":00");
      marca.style.top = (hora / 24) * 100 + "%";
      horas.appendChild(marca);
    }
    tabla.appendChild(horas);

    var columnas = opciones.dias.map(function (dia) {
      var columna = crear("div", "grilla-columna");
      columna.dataset.fecha = dia.fecha;
      tabla.appendChild(columna);
      return columna;
    });
    var pasado = { inicio: inicioDelDia(opciones.dias[0].fecha), fin: opciones.pasadoHasta || ahora, clase: "grilla-pasado" };
    var lineaDeAhora = { inicio: ahora, fin: new Date(ahora.getTime() + 60000), clase: "grilla-ahora" };
    [pasado].concat(opciones.bloques, [lineaDeAhora]).forEach(function (bloque) {
      agregarBloque(columnas, bloque);
    });

    contenedor.replaceChildren(tabla);
    tabla.style.gridTemplateColumns = "var(--ancho-horas) repeat(" + opciones.dias.length + ", 1fr)";
    contenedor.scrollTop = opciones.hora === undefined
      ? desplazamiento
      : (opciones.hora / 24) * tabla.querySelector(".grilla-columna").offsetHeight;
  }

  function momentoEn(columna, evento) {
    var caja = columna.getBoundingClientRect();
    var proporcion = Math.min(Math.max((evento.clientY - caja.top) / caja.height, 0), 1);
    return new Date(inicioDelDia(columna.dataset.fecha).getTime() + proporcion * UN_DIA);
  }

  function mostrarFantasma(contenedor, inicio, fin, texto) {
    borrarFantasma(contenedor);
    agregarBloque(Array.from(contenedor.querySelectorAll(".grilla-columna")), {
      inicio: inicio, fin: fin, clase: "grilla-fantasma", texto: texto,
    });
  }

  function borrarFantasma(contenedor) {
    contenedor.querySelectorAll(".grilla-fantasma").forEach(function (fantasma) {
      fantasma.remove();
    });
  }

  return {
    dibujar: dibujar, momentoEn: momentoEn, asignarCarriles: asignarCarriles,
    mostrarFantasma: mostrarFantasma, borrarFantasma: borrarFantasma,
    crear: crear, textoHora: textoHora, fechaIso: fechaIso, mediaHora: mediaHora,
  };
})();
