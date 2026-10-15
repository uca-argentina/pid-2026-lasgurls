(function () {
  var MEDIA_HORA = 30;

  function dosCifras(numero) {
    return String(numero).padStart(2, "0");
  }

  function momentoEn(columna, evento) {
    var cuerpo = columna.closest("[data-primera-hora]");
    var primeraHora = Number(cuerpo.dataset.primeraHora);
    var minutosVisibles = (24 - primeraHora) * 60;
    var caja = columna.getBoundingClientRect();
    var proporcion = Math.min(Math.max((evento.clientY - caja.top) / caja.height, 0), 1);
    var minutos = primeraHora * 60 + Math.floor(proporcion * minutosVisibles / MEDIA_HORA) * MEDIA_HORA;
    minutos = Math.min(minutos, 24 * 60 - MEDIA_HORA);
    var partes = columna.dataset.fecha.split("-").map(Number);
    return {
      fecha: columna.dataset.fecha,
      hora: dosCifras(Math.floor(minutos / 60)) + ":" + dosCifras(minutos % 60),
      fechaHora: new Date(partes[0], partes[1] - 1, partes[2], Math.floor(minutos / 60), minutos % 60),
      arriba: (minutos - primeraHora * 60) / minutosVisibles * 100,
      alto: Math.min(60, 24 * 60 - minutos) / minutosVisibles * 100,
    };
  }

  function borrarFantasma() {
    document.querySelectorAll(".mini-fantasma").forEach(function (fantasma) {
      fantasma.remove();
    });
  }

  function columnaLibre(evento) {
    var columna = evento.target.closest(".mini-semana-columna");
    if (!columna || evento.target.closest(".mini-evento")) return null;
    return columna;
  }

  document.addEventListener("mousemove", function (evento) {
    var columna = columnaLibre(evento);
    if (!columna) {
      borrarFantasma();
      return;
    }
    var momento = momentoEn(columna, evento);
    var yaPaso = momento.fechaHora < new Date();
    columna.style.cursor = yaPaso ? "default" : "pointer";
    borrarFantasma();
    if (yaPaso) return;
    var fantasma = document.createElement("span");
    fantasma.className = "grilla-fantasma mini-fantasma";
    fantasma.style.top = momento.arriba + "%";
    fantasma.style.height = momento.alto + "%";
    fantasma.textContent = "+ " + momento.hora;
    columna.appendChild(fantasma);
  });

  document.addEventListener("mouseleave", borrarFantasma);

  function enlace(clase, texto, url, momento) {
    var link = document.createElement("a");
    link.className = clase;
    link.textContent = texto;
    var destino = new URL(url, window.location.href);
    destino.searchParams.set("fecha", momento.fecha);
    destino.searchParams.set("hora", momento.hora);
    link.href = destino.pathname + destino.search;
    return link;
  }

  function abrirCrear(columna, momento) {
    var semana = columna.closest(".mini-semana");
    var dialogo = document.querySelector("[data-crear-en-horario]");
    var arriba = document.createElement("div");
    arriba.className = "dialogo-arriba";
    var cerrar = document.createElement("form");
    cerrar.className = "dialogo-cruz";
    cerrar.method = "dialog";
    var cruz = document.createElement("button");
    cruz.textContent = "×";
    cruz.setAttribute("aria-label", "Cerrar");
    cerrar.appendChild(cruz);
    arriba.appendChild(cerrar);
    var titulo = document.createElement("h3");
    titulo.textContent = "¿Qué querés agendar?";
    var cuando = document.createElement("p");
    cuando.className = "detalle-cuando";
    cuando.textContent = columna.dataset.nombre + " a las " + momento.hora;
    var acciones = document.createElement("div");
    acciones.className = "dialogo-acciones";
    acciones.append(
      enlace("boton-neutro", "Nuevo evento", semana.dataset.nuevoEvento, momento),
      enlace("boton-principal", "Nueva juntada", semana.dataset.nuevaJuntada, momento)
    );
    dialogo.replaceChildren(arriba, titulo, cuando, acciones);
    dialogo.showModal();
  }

  document.addEventListener("click", function (evento) {
    var columna = columnaLibre(evento);
    if (!columna) return;
    var momento = momentoEn(columna, evento);
    if (momento.fechaHora < new Date()) return;
    borrarFantasma();
    abrirCrear(columna, momento);
  });
})();
